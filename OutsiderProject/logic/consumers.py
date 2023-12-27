import json
import uuid
import random

from enum import Enum
from collections import Counter
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import RoomModel, WordsListModel

from asgiref.sync import sync_to_async


class State(str, Enum):
    LOBBY = "LOBBY"
    PLAYING = "PLAYING"
    PLAYER_TURN = "PLAYER_TURN"
    OUT = "OUT"


class WebsocketUser:
    def __init__(self, username, captain):
        self.username = username
        self.id = str(uuid.uuid4())
        self.captain = captain
        self.outsider = False
        self.state = State.LOBBY
        self.guessWord = ""

    def __str__(self):
        return f"{self.username}"

    def __repr__(self):
        return f"{self.username}"


class RoomConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.outsider = None
        self.selected_word = None
        self.votes = []

    @sync_to_async
    def get_room(self):
        return RoomModel.objects.get(name=self.room_name)

    @sync_to_async
    def get_word_list(self):
        return WordsListModel.objects.get(name="Current")

    @sync_to_async
    def update_room(self, room):
        return room.save()

    @sync_to_async
    def delete_room(self):
        return RoomModel.objects.get(name=self.room_name).delete()

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"room_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.db_room = await self.get_room()

    async def disconnect(self, close_code):
        if self.user and self.db_room.current_connections:
            for player in self.db_room.current_connections:
                if player["id"] == self.user.id:
                    self.db_room.current_connections.remove(player)
                    break

            if self.db_room.current_connections:
                if self.user.captain:
                    self.db_room.current_connections[0]["captain"] = True
                await self.update_room(self.db_room)
            else:
                # Delete current room if there's no users left
                await self.delete_room()

            # Send DISCONNECT message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "disconnection",
                    "message": self.user.username + " se ha desconectado",
                    "username": self.user.username,
                },
            )

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    ###

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        username = ""
        if "username" in text_data_json:
            username = text_data_json["username"]

        message_type = "default"

        if "action" in text_data_json:
            # Check connections to add the new player
            if text_data_json["action"] == "connection":
                message_type = "connection"

                captain = True if len(self.db_room.current_connections) == 0 else False
                self.user = WebsocketUser(username=username, captain=captain)
                self.db_room.current_connections.append(self.user.__dict__)
                await self.update_room(self.db_room)

            # Start game by selecting an 'outsider', shuffling the players and selecting a word
            elif text_data_json["action"] == "startGame":
                message_type = "startGame"

                random.shuffle(self.db_room.current_connections)

                self.outsider = random.choice(self.db_room.current_connections)

                word_list = await self.get_word_list()
                self.selected_word = random.choice(word_list.word_list)

                for player in self.db_room.current_connections:
                    player["state"] = State.PLAYING

                self.db_room.current_connections[0]["state"] = State.PLAYER_TURN

                message = {
                    "outsider": self.outsider["id"],
                    "selected_word": self.selected_word,
                    "turn_order": self.db_room.current_connections,
                }

            elif text_data_json["action"] == "nextTurn":
                message_type = "nextTurn"

                self.user.guessWord = message
                self.user.state = State.PLAYING

                players = text_data_json["order"]
                for i in range(len(players)):
                    if players[i]["id"] == self.user.id:
                        # Add guessWord and pass the turn to the next player
                        players[i]["guessWord"] = message
                        if (i + 1) < len(players):
                            players[i + 1]["state"] = State.PLAYER_TURN
                            next_player = players[i + 1]["id"]
                        else:
                            next_player = players[0]

                message = {"turn_order": players, "next_player": next_player}

            elif text_data_json["action"] == "votingOutsider":
                message_type = "votingOutsider"
                message = {
                    "playerVote": message,
                }

            elif text_data_json["action"] == "votingComplete":
                message_type = "votingComplete"

                message = {
                    "playerOut": message,
                }

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": message_type, "message": message, "username": username},
        )

    ###

    # Receive connection message from room group
    async def connection(self, event):
        if not "username" in event:
            return

        username = event["username"]

        self.db_room = await self.get_room()

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "connection",
                    "message": "Se ha unido a la sala",
                    "username": username,
                    "user": json.dumps(self.user.__dict__),
                    "actual_users": json.dumps(
                        self.db_room.current_connections, default=lambda x: x.__dict__
                    ),
                }
            )
        )

    # Recieve disconnection message from room group
    async def disconnection(self, event):
        if not "username" in event:
            return

        username = event["username"]

        self.db_room = await self.get_room()
        if self.db_room.current_connections[0]["id"] == self.user.id:
            self.user.captain = True

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "disconnection",
                    "message": "Se ha desconectado",
                    "username": username,
                    "user": json.dumps(self.user.__dict__),
                    "actual_users": json.dumps(
                        self.db_room.current_connections, default=lambda x: x.__dict__
                    ),
                }
            )
        )

    # Recieve 'startGame' message from room group
    async def startGame(self, event):
        if not "message" in event:
            return

        turn_order = event["message"]["turn_order"]
        key_word = event["message"]["selected_word"]
        outsider = event["message"]["outsider"]

        if self.user.captain:
            self.outsider = outsider

        if outsider == self.user.id:
            self.user.outsider = True
            key_word = key_word["b"]
        else:
            key_word = key_word["a"]

        if turn_order[0]["id"] == self.user.id:
            self.user.state = State.PLAYER_TURN

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "startGame",
                    "user": json.dumps(self.user.__dict__),
                    "key_word": key_word,
                    "actual_users": json.dumps(
                        turn_order, default=lambda x: x.__dict__
                    ),
                }
            )
        )

    # Recieve 'nextTurn' message from room group
    async def nextTurn(self, event):
        if not "message" in event:
            return

        turn_order = event["message"]["turn_order"]

        if event["message"]["next_player"] == self.user.id:
            self.user.state = State.PLAYER_TURN

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "nextTurn",
                    "user": json.dumps(self.user.__dict__),
                    "actual_users": json.dumps(
                        turn_order, default=lambda x: x.__dict__
                    ),
                }
            )
        )

    # Recieve 'votingOutsider' message from room group
    # (ONLY FOR THE CAPTAIN TO COUNT THE VOTES)
    async def votingOutsider(self, event):
        if not self.user.captain:
            return

        if not "message" in event:
            return

        self.votes.append(event["message"]["playerVote"])

        if len(self.votes) >= len(self.db_room.current_connections):
            counter = Counter(self.votes).most_common()
            player_out = ""

            if len(counter) > 1:
                if counter[0][1] > counter[1][1]:
                    # If there's a most voted player
                    player_out = counter[0][0]
            else:
                player_out = counter[0][0]

            for player in self.db_room.current_connections:
                if player["id"] == player_out:
                    player_out = player
                    if player_out["id"] == self.outsider:
                        player_out["outsider"] = True

            # CHANGE ->  # Send message to room group
            # await self.channel_layer.group_send(
            #   self.room_group_name,
            #   {"type": votingComplete, "player_out": player_out},
            # )

            # Send message to WebSocket
            await self.send(
                text_data=json.dumps(
                    {
                        "message_type": "votingOutsider",
                        "player_out": player_out,
                    }
                )
            )

    # Receive 'votingComplete' from room group
    async def votingComplete(self, event):
        if not "message" in event:
            return

        player_out = event["message"]["playerOut"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message_type": "votingComplete",
                    "player_out": player_out,
                }
            )
        )

    # Receive default/chat from room group
    async def default(self, event):
        message = event["message"]
        username = ""

        if "username" in event:
            username = event["username"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {"message_type": "default", "message": message, "username": username}
            )
        )
