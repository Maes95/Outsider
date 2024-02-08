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
        self.selected_word = None
        self.votes = []
        self.filtered_players = []
        self.word_list = []
        self.outsiders = []
        self.repeated_words = None
        self.first_player = None
        self.finish_game = False

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
        if self.finish_game:
            return

        self.db_room = await self.get_room()

        if self.user and self.db_room.current_connections:
            for player in self.db_room.current_connections:
                if player["id"] == self.user.id:
                    self.db_room.current_connections.remove(player)
                    break

            if self.db_room.current_connections:
                if self.user.captain:
                    self.db_room.current_connections[0]["captain"] = True
                if self.user.outsider:
                    self.db_room.number_outsiders -= 1

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
                    "disconnected_user": self.user.__dict__,
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

            # Start game by selecting the posibles 'outsiders', shuffling the players and selecting a word
            elif action == "startGame":
                message_type = "startGame"

                await self.startGameLogic()

                message = {
                    "outsiders": self.outsiders,
                    "selected_word": self.selected_word,
                    "first_player": self.first_player,
                    "turn_order": self.db_room.current_connections,
                }

            # Add guessWord and pass the turn to the next player
            elif action == "nextTurn":
                message_type = "nextTurn"

                self.user.guessWord = message
                self.user.state = State.PLAYING

                players = content["order"]
                for i in range(len(players)):
                    if players[i]["state"] == State.OUT:
                        continue
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
                    "player_vote": message,
                }

            # Check if the Ousider guessed correctly the password
            elif action == "lastChance":
                message_type = "lastChance"

                guess = message.casefold()
                key_word = self.selected_word["a"].casefold()

                message = {
                    "last_chance_guess": guess == key_word,
                }

            # "Restart" the game state with a new word and turn order
            elif action == "nextRound":
                message_type = "nextRound"

                await self.startGameLogic(restart=True)

                message = {
                    "outsiders": self.outsiders,
                    "selected_word": self.selected_word,
                    "first_player": self.first_player,
                    "turn_order": self.db_room.current_connections,
                }

            # End the current game for all the users/connections
            elif action == "endGame":
                try:
                    await self.delete_room()
                except:
                    pass

                message_type = "endGame"

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": message_type, "message": message, "username": username},
        )

    async def setOutsiders(self):
        if len(self.db_room.current_connections) >= 6:
            self.db_room.number_outsiders = 2

        if self.db_room.number_outsiders > 1:
            k = self.db_room.number_outsiders
            select_outsiders = random.sample(self.db_room.current_connections, k)
            for outsider in select_outsiders:
                self.outsiders.append(outsider["id"])

        else:
            self.outsiders.append(random.choice(self.db_room.current_connections)["id"])

    async def startGameLogic(self, restart=False):
        if not self.word_list:
            self.word_list = await self.get_word_list()

        if restart:
            self.db_room = await self.get_room()
            self.filtered_players = []
            try:
                self.selected_word = random.choice(
                    [
                        word
                        for word in self.word_list.word_list
                        if word not in self.db_room.repeated_words
                    ]
                )
            except:
                print("EXCEPTION -> No more words to select, restarting...")
                self.selected_word = random.choice(self.word_list.word_list)
                self.db_room.repeated_words = []

        else:
            self.selected_word = random.choice(self.word_list.word_list)
            self.db_room.started_game = True
            await self.setOutsiders()

        self.db_room.repeated_words.append(self.selected_word)

        random.shuffle(self.db_room.current_connections)

        player_turn = True
        for player in self.db_room.current_connections:
            if player["state"] == State.OUT:
                continue

            if player_turn:
                player["state"] = State.PLAYER_TURN
                self.first_player = player
                player_turn = False
            else:
                player["state"] = State.PLAYING

        await self.update_room(self.db_room)

    # endregion

    # region Room group methods

    async def updateConnections(self, type, username, disconnected_user=None):
        ms = "Se ha unido a la sala" if type == "connection" else "Se ha desconectado"

        await self.send_json(
            content={
                "message_type": type,
                "message": ms,
                "username": username,
                "user": json.dumps(self.user.__dict__),
                "actual_users": json.dumps(
                    self.db_room.current_connections, default=lambda x: x.__dict__
                ),
                "disconnected_user": disconnected_user,
            }
        )

    async def startGameLogicRoomGroup(self, event):
        self.selected_word = event["message"]["selected_word"]

        if self.user.id in self.outsiders:
            self.user.outsider = True
            key_word = "???"
        else:
            key_word = self.selected_word["a"]

        turn_order = event["message"]["turn_order"]

        if event["message"]["first_player"]["id"] == self.user.id:
            self.user.state = State.PLAYER_TURN
            # Only send the password if the outsider if the first player
            if self.user.outsider:
                key_word = self.selected_word["b"]
        elif self.user.state != State.OUT:
            self.user.state = State.PLAYING

        return key_word, turn_order

    ###

    async def connection(self, event):
        self.db_room = await self.get_room()

        await self.updateConnections(type="connection", username=event["username"])

    async def disconnection(self, event):
        self.db_room = await self.get_room()
        disconnected_user = event["disconnected_user"]

        if disconnected_user["captain"] == True:
            if self.db_room.current_connections[0]["id"] == self.user.id:
                self.user.captain = True

        await self.updateConnections(
            type="disconnection",
            username=disconnected_user["username"],
            disconnected_user=disconnected_user,
        )

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
        self.outsiders = event["message"]["outsiders"]
        key_word, turn_order = await self.startGameLogicRoomGroup(event=event)

        await self.send_json(
            content={
                "message_type": "startGame",
                "user": json.dumps(self.user.__dict__),
                "key_word": key_word,
                "actual_users": json.dumps(turn_order, default=lambda x: x.__dict__),
            }
        )
        self.db_room = await self.get_room()

    async def nextTurn(self, event):
        turn_order = event["message"]["turn_order"]

        if event["message"]["next_player"] == self.user.id:
            self.user.state = State.PLAYER_TURN

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

        self.votes.append(event["message"]["player_vote"])

        if not self.filtered_players:
            self.filtered_players = [
                player
                for player in self.db_room.current_connections
                if player["state"] == State.PLAYER_TURN
                or player["state"] == State.PLAYING
            ]

        if len(self.votes) >= len(self.filtered_players):
            counter = Counter(self.votes).most_common()
            player_out = ""

            if len(counter) > 1:
                if counter[0][1] > counter[1][1]:
                    # If there's a most voted player
                    player_out = counter[0][0]
            else:
                player_out = counter[0][0]

            current_playing = 0

            next_captain = None

            for player in self.db_room.current_connections:
                if player["id"] == player_out:
                    player["state"] = State.OUT
                    player_out = player

                    if player_out["captain"]:
                        index = self.db_room.current_connections.index(player)

                        if index + 1 < len(self.db_room.current_connections):
                            self.db_room.current_connections[index]["captain"] = True
                            next_captain = self.db_room.current_connections[index]
                        else:
                            self.db_room.current_connections[0]["captain"] = True
                            next_captain = self.db_room.current_connections[0]

                    if player_out["id"] in self.outsiders:
                        player_out["outsider"] = True
                    continue

                current_playing = current_playing + 1

            # Check if the players can continue playing without the eliminated player
            if player_out and player_out["outsider"]:
                self.db_room.number_outsiders -= 1

            can_continue = (
                current_playing > self.db_room.number_outsiders * 2
                if self.db_room.number_outsiders > 0
                else False
            )

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "votingComplete",
                    "player_out": player_out,
                    "continue_playing": can_continue,
                    "number_outsiders": self.db_room.number_outsiders,
                    "next_captain": next_captain,
                    "actual_users": json.dumps(
                        self.db_room.current_connections, default=lambda x: x.__dict__
                    ),
                },
            )

            await self.update_room(self.db_room)

    async def votingComplete(self, event):
        player_out = event["player_out"]
        next_captain = event["next_captain"]
        continue_playing = event["continue_playing"]
        actual_users = event["actual_users"]

        if player_out:
            if player_out["id"] == self.user.id:
                self.user.state = State.OUT
                if self.user.captain == True:
                    self.user.captain = False

            elif next_captain and next_captain["id"] == self.user.id:
                self.user.captain = True

        await self.send_json(
            content={
                "message_type": "votingComplete",
                "player_out": player_out,
                "continue_playing": continue_playing,
                "number_outsiders": event["number_outsiders"],
                "actual_users": json.dumps(actual_users, default=lambda x: x.__dict__),
            }
        )

    async def lastChance(self, event):
        last_chance_guess = event["message"]["last_chance_guess"]

        await self.send_json(
            content={
                "message_type": "lastChanceGuess",
                "last_chance_guess": last_chance_guess,
            }
        )

    async def nextRound(self, event):
        self.votes = []
        key_word, turn_order = await self.startGameLogicRoomGroup(event=event)

        await self.send_json(
            content={
                "message_type": "nextRound",
                "user": json.dumps(self.user.__dict__),
                "key_word": key_word,
                "actual_users": json.dumps(turn_order, default=lambda x: x.__dict__),
            }
        )

    async def endGame(self, event):
        self.finish_game = True
        await self.send_json(
            content={
                "message_type": "endGame",
            }
        )

    # endregion
