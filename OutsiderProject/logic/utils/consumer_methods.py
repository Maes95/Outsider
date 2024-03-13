import random

from collections import Counter

from .consumer_classes import State
from . import sync_rest_calls


# WebSocket methods


async def startGameLogic(self, restart=False):
    if not self.word_list:
        try:
            self.word_list = await sync_rest_calls.get_word_list()
        except Exception as e:
            print("EXCEPTION -> There's no 'Current' word list.")
            print(e)
            return None

    if restart:
        self.db_room = await sync_rest_calls.get_room(room_name=self.room_name)
        self.filtered_players = []
        try:
            self.selected_word = random.choice(
                [
                    word
                    for word in self.word_list.word_list
                    if word not in self.db_room.repeated_words
                ]
            )
        except Exception as e:
            print("EXCEPTION -> No more words to select, restarting...")
            print(e)
            self.selected_word = random.choice(self.word_list.word_list)
            self.db_room.repeated_words = []

    else:
        self.selected_word = random.choice(self.word_list.word_list)
        self.db_room.started_game = True
        self.outsiders = await setOutsiders(
            db_room=self.db_room, outsiders=self.outsiders
        )

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

    await sync_rest_calls.update_room(self.db_room)

    return self


async def setOutsiders(db_room, outsiders):
    if len(db_room.current_connections) >= 6:
        db_room.number_outsiders = 2

    if db_room.number_outsiders > 1:
        k = db_room.number_outsiders
        select_outsiders = random.sample(db_room.current_connections, k)
        for outsider in select_outsiders:
            outsiders.append(outsider["id"])

    else:
        outsiders.append(random.choice(db_room.current_connections)["id"])

    return outsiders


# RoomGroup methods


async def startGameLogicRoomGroup(self, event):
    self.votes = []

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

    return self, key_word, turn_order


async def votingOutsider(self, player_vote):

    self.votes.append(player_vote)

    if not self.filtered_players:
        self.filtered_players = [
            player
            for player in self.db_room.current_connections
            if player["state"] == State.PLAYER_TURN or player["state"] == State.PLAYING
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
                    for player in self.db_room.current_connections:
                        if player["state"] != State.OUT:
                            player["captain"] = True
                            next_captain = player
                            break

                if player_out["id"] in self.outsiders:
                    player_out["outsider"] = True

            elif player["state"] != State.OUT:
                current_playing = current_playing + 1

        # Check if the players can continue playing without the eliminated player
        if player_out and player_out["outsider"]:
            self.db_room.number_outsiders -= 1

        can_continue = (
            current_playing > self.db_room.number_outsiders * 2
            if self.db_room.number_outsiders > 0
            else False
        )

        return self, False, player_out, can_continue, next_captain

    else:
        return self, True, None, False, None
