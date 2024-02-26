from enum import Enum
import uuid


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
