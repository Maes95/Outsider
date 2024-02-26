import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .utils.consumer_classes import State, WebsocketUser
from .utils import sync_rest_calls, consumer_methods


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

    # region Websocket methods

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"room_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.db_room = await sync_rest_calls.get_room(room_name=self.room_name)

    async def disconnect(self, close_code):
        if self.finish_game:
            return

        self.db_room = await sync_rest_calls.get_room(room_name=self.room_name)

        if self.user and self.db_room.current_connections:
            for player in self.db_room.current_connections:
                if player["id"] == self.user.id:
                    self.db_room.current_connections.remove(player)
                    break

            if self.db_room.current_connections:
                if self.user.captain:
                    for player in self.db_room.current_connections:
                        if player["state"] != State.OUT:
                            player["captain"] = True
                            break

                if self.user.outsider:
                    self.db_room.number_outsiders -= 1

                await sync_rest_calls.update_room(self.db_room)
            else:
                # Delete current room if there's no users left
                await sync_rest_calls.delete_room(room_name=self.room_name)

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
                captain = True if len(self.db_room.current_connections) == 0 else False
                self.user = WebsocketUser(username=username, captain=captain)
                self.db_room.current_connections.append(self.user.__dict__)
                await sync_rest_calls.update_room(self.db_room)

            # Start game by selecting the posibles 'outsiders', shuffling the players and selecting a word
            elif action == "startGame":
                self = await consumer_methods.startGameLogic(self, restart=False)

                message = {
                    "outsiders": self.outsiders,
                    "selected_word": self.selected_word,
                    "first_player": self.first_player,
                    "turn_order": self.db_room.current_connections,
                }

            # Add guessWord and pass the turn to the next player
            elif action == "nextTurn":
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
                message = {
                    "player_vote": message,
                }

            # Check if the Ousider guessed correctly the password
            elif action == "lastChance":
                guess = message.casefold()
                key_word = self.selected_word["a"].casefold()

                message = {
                    "last_chance_guess": guess == key_word,
                }

            # "Restart" the game state with a new word and turn order
            elif action == "nextRound":
                self = await consumer_methods.startGameLogic(self, restart=True)

                message = {
                    "outsiders": self.outsiders,
                    "selected_word": self.selected_word,
                    "first_player": self.first_player,
                    "turn_order": self.db_room.current_connections,
                }

            # End the current game for all the users/connections
            elif action == "endGame":
                try:
                    await sync_rest_calls.delete_room(room_name=self.room_name)
                except:
                    pass

        message_type = action

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": message_type, "message": message, "username": username},
        )

    # endregion

    # region Room group methods

    async def connection(self, event):
        self.db_room = await sync_rest_calls.get_room(room_name=self.room_name)
        await self.updateConnections(type="connection", username=event["username"])

    async def disconnection(self, event):
        self.db_room = await sync_rest_calls.get_room(room_name=self.room_name)
        disconnected_user = event["disconnected_user"]

        if disconnected_user["captain"] == True:
            if self.db_room.current_connections[0]["id"] == self.user.id:
                self.user.captain = True

        await self.updateConnections(
            type="disconnection",
            username=disconnected_user["username"],
            disconnected_user=disconnected_user,
        )

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

    async def default(self, event):
        # Send message to WebSocket
        await self.send_json(
            content={
                "message_type": "default",
                "message": event["message"],
                "username": event["username"] if "username" in event else "",
            }
        )

    async def startGame(self, event):
        self.outsiders = event["message"]["outsiders"]

        self, key_word, turn_order = await consumer_methods.startGameLogicRoomGroup(
            self=self, event=event
        )

        await self.send_json(
            content={
                "message_type": "startGame",
                "user": json.dumps(self.user.__dict__),
                "key_word": key_word,
                "actual_users": json.dumps(turn_order, default=lambda x: x.__dict__),
            }
        )

        self.db_room = await sync_rest_calls.get_room(room_name=self.room_name)

    async def nextTurn(self, event):
        if event["message"]["next_player"] == self.user.id:
            self.user.state = State.PLAYER_TURN

        await self.send_json(
            content={
                "message_type": "nextTurn",
                "user": json.dumps(self.user.__dict__),
                "actual_users": json.dumps(
                    event["message"]["turn_order"], default=lambda x: x.__dict__
                ),
            }
        )

    async def votingOutsider(self, event):
        # ONLY THE CAPTAIN COUNT THE VOTES
        if not self.user.captain:
            return

        self, continue_voting, player_out, can_continue, next_captain = (
            await consumer_methods.votingOutsider(
                self=self, player_vote=event["message"]["player_vote"]
            )
        )

        # Keep counting ALL the votes...
        if continue_voting:
            return

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

        await sync_rest_calls.update_room(self.db_room)

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
                "user": json.dumps(self.user.__dict__),
                "player_out": player_out,
                "continue_playing": continue_playing,
                "number_outsiders": event["number_outsiders"],
                "actual_users": json.dumps(actual_users, default=lambda x: x.__dict__),
            }
        )

    async def lastChance(self, event):
        await self.send_json(
            content={
                "message_type": "lastChanceGuess",
                "last_chance_guess": event["message"]["last_chance_guess"],
            }
        )

    async def nextRound(self, event):
        self, key_word, turn_order = await consumer_methods.startGameLogicRoomGroup(
            self=self, event=event
        )

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
