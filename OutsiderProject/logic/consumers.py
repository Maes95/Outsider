import json
import uuid
import random

from enum import Enum
from collections import Counter
from channels.generic.websocket import AsyncJsonWebsocketConsumer

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


class RoomConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.outsider = None
        self.selected_word = None
        self.votes = []

    # region Sync REST calls

    @sync_to_async
    def get_room(self):
        room = RoomModel.objects.get(name=self.room_name)
        return room

    @sync_to_async
    def update_room(self, room):
        return room.save()

    @sync_to_async
    def delete_room(self):
        return RoomModel.objects.get(name=self.room_name).delete()

    @sync_to_async
    def get_word_list(self):
        return WordsListModel.objects.get(name="Current")

    # endregion

    # region Websocket

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

            # Send "disconnection" message to room group
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

    async def receive_json(self, content):
        if not "message" in content:
            return

        message = content["message"]

        username = ""
        if "username" in content:
            username = content["username"]

        message_type = "default"

        # Check action to take
        if "action" in content:
            action = content["action"]

            # Check connections to add the new player
            if action == "connection":
                message_type = "connection"

                captain = True if len(self.db_room.current_connections) == 0 else False
                self.user = WebsocketUser(username=username, captain=captain)
                self.db_room.current_connections.append(self.user.__dict__)
                await self.update_room(self.db_room)

            # Start game by selecting an 'outsider', shuffling the players and selecting a word
            elif action == "startGame":
                message_type = "startGame"

                random.shuffle(self.db_room.current_connections)

                self.outsider = random.choice(self.db_room.current_connections)

                word_list = await self.get_word_list()
                self.selected_word = random.choice(word_list.word_list)

                for player in self.db_room.current_connections:
                    player["state"] = State.PLAYING

                self.db_room.current_connections[0]["state"] = State.PLAYER_TURN

                self.db_room.started_game = True
                await self.update_room(self.db_room)

                message = {
                    "outsider": self.outsider["id"],
                    "selected_word": self.selected_word,
                    "turn_order": self.db_room.current_connections,
                }

            # Add guessWord and pass the turn to the next player
            elif action == "nextTurn":
                message_type = "nextTurn"

                self.user.guessWord = message
                self.user.state = State.PLAYING

                players = content["order"]
                for i in range(len(players)):
                    if players[i]["id"] == self.user.id:
                        players[i]["guessWord"] = message
                        if (i + 1) < len(players):
                            players[i + 1]["state"] = State.PLAYER_TURN
                            next_player = players[i + 1]["id"]
                        else:
                            next_player = players[0]

                message = {"turn_order": players, "next_player": next_player}

            # Add one vote to the selected player
            elif action == "votingOutsider":
                message_type = "votingOutsider"
                message = {
                    "playerVote": message,
                }

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": message_type, "message": message, "username": username},
        )

    # endregion

    # region Room group methods

    async def updateConnections(self, type, username):
        ms = "Se ha unido a la sala" if type == "connection" else "Se ha desconectado"

        # Send message to WebSocket
        await self.send_json(
            content={
                "message_type": type,
                "message": ms,
                "username": username,
                "user": json.dumps(self.user.__dict__),
                "actual_users": json.dumps(
                    self.db_room.current_connections, default=lambda x: x.__dict__
                ),
            }
        )

    async def connection(self, event):
        self.db_room = await self.get_room()

        await self.updateConnections(type="connection", username=event["username"])

    async def disconnection(self, event):
        self.db_room = await self.get_room()
        if self.db_room.current_connections[0]["id"] == self.user.id:
            self.user.captain = True

        await self.updateConnections(type="disconnection", username=event["username"])

    async def default(self, event):
        message = event["message"]

        username = ""
        if "username" in event:
            username = event["username"]

        # Send message to WebSocket
        await self.send_json(
            content={
                "message_type": "default",
                "message": message,
                "username": username,
            }
        )

    async def startGame(self, event):
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
        await self.send_json(
            content={
                "message_type": "startGame",
                "user": json.dumps(self.user.__dict__),
                "key_word": key_word,
                "actual_users": json.dumps(turn_order, default=lambda x: x.__dict__),
            }
        )

    async def nextTurn(self, event):
        turn_order = event["message"]["turn_order"]

        if event["message"]["next_player"] == self.user.id:
            self.user.state = State.PLAYER_TURN

        # Send message to WebSocket
        await self.send_json(
            content={
                "message_type": "nextTurn",
                "user": json.dumps(self.user.__dict__),
                "actual_users": json.dumps(turn_order, default=lambda x: x.__dict__),
            }
        )

    async def votingOutsider(self, event):
        # ONLY THE CAPTAIN COUNT THE VOTES
        if not self.user.captain:
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

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "votingComplete", "player_out": player_out},
            )

    async def votingComplete(self, event):
        player_out = event["player_out"]

        # Send message to WebSocket
        await self.send_json(
            content={
                "message_type": "votingComplete",
                "player_out": player_out,
            }
        )

    # endregion
