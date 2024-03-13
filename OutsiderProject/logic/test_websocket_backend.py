import pytest
import json

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path

from .consumers import RoomConsumer
from .utils.consumer_classes import State
from .utils import sync_rest_calls


# Aux. methods and fixtures

test_room = "test_room"


async def check_room_does_not_exist(room_name):
    try:
        await sync_rest_calls.get_room(room_name=room_name)
        return False
    except:
        return True


async def communicator_connection(username, room=test_room):
    communicator = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/{room}/",
    )

    connected, subprotocol = await communicator.connect()

    if not connected:
        return None, None

    await communicator.send_json_to(
        {"action": "connection", "message": "", "username": username}
    )
    response = await communicator.receive_json_from()

    return communicator, response


@pytest.fixture
async def add_test_word_list():
    return await sync_rest_calls.set_word_list()


@pytest.fixture
async def create_test_room(request):
    return await sync_rest_calls.create_room(room_name=request.param)


# Testing -> pytest.py

# NOTE: On the first test, add current word_list via fixture 'add_test_word_list'
# NOTE: To run the tests correctly it is needed the use of Redis server and a clear environment (empty database, no active websocket connections, ...)


@pytest.mark.django_db()
async def test_none_room_connection(add_test_word_list):

    communicator = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/{test_room}/",
    )

    connected, subprotocol = await communicator.connect()
    assert connected == False


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_room_connection(create_test_room):

    communicator = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/{test_room}/",
    )

    connected, subprotocol = await communicator.connect()
    assert connected == True

    # If there's already websocket-connected, the client must send a 'connection' message with its credentials (name)

    await communicator.send_json_to(
        {"action": "connection", "message": "", "username": "User1"}
    )
    response = await communicator.receive_json_from()
    user = json.loads(response["user"])

    assert response["message_type"] == "connection"
    assert response["message"] == "Se ha unido a la sala"
    assert response["username"] == "User1"
    assert response["disconnected_user"] == None
    assert user["username"] == "User1"
    assert user["captain"] == True
    assert user["outsider"] == False
    assert user["state"] == State.LOBBY
    assert user["guessWord"] == ""

    test_room_instance = await sync_rest_calls.get_room(room_name=test_room)
    assert test_room_instance

    await communicator.disconnect()

    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_room_connection_wrong_room(create_test_room):

    test_room_instance = await sync_rest_calls.get_room(room_name=test_room)
    assert test_room_instance

    communicator = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/wrong_room/",
    )

    connected, subprotocol = await communicator.connect()
    assert connected == False

    test_room_instance = await sync_rest_calls.delete_room(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_room_connection_started_game_room(create_test_room):

    room = create_test_room
    room.started_game = True
    await sync_rest_calls.update_room(room)

    communicator = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/{test_room}/",
    )

    connected, subprotocol = await communicator.connect()
    assert connected == False

    await sync_rest_calls.delete_room(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_room_connection_multiple_connections_behavior(create_test_room):

    # User1 and User2 'connection' and 'disconnection' spected behavior included the room state

    communicator_1 = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/{test_room}/",
    )

    communicator_2 = WebsocketCommunicator(
        application=URLRouter(
            [re_path(r"ws/room/(?P<room_name>\w+)/$", RoomConsumer.as_asgi())]
        ),
        path=f"ws/room/{test_room}/",
    )

    connected, subprotocol = await communicator_1.connect()
    assert connected == True

    connected, subprotocol = await communicator_2.connect()
    assert connected == True

    # User 1
    await communicator_1.send_json_to(
        {"action": "connection", "message": "", "username": "User1"}
    )
    response_u1 = await communicator_1.receive_json_from()
    u1 = json.loads(response_u1["user"])
    response_u2 = await communicator_2.receive_json_from()

    assert response_u1["message_type"] == response_u2["message_type"] == "connection"
    assert response_u1["message"] == response_u2["message"] == "Se ha unido a la sala"
    assert response_u1["username"] == response_u2["username"] == "User1"
    assert response_u1["disconnected_user"] == response_u2["disconnected_user"] == None
    assert u1["username"] == "User1"
    assert u1["captain"] == True
    assert response_u2["user"] == ""

    # User 2
    await communicator_2.send_json_to(
        {"action": "connection", "message": "", "username": "User2"}
    )
    response_u1 = await communicator_1.receive_json_from()
    u1 = json.loads(response_u1["user"])
    response_u2 = await communicator_2.receive_json_from()
    u2 = json.loads(response_u2["user"])
    room = await sync_rest_calls.get_room(room_name=test_room)

    assert response_u1["message_type"] == response_u2["message_type"] == "connection"
    assert response_u1["message"] == response_u2["message"] == "Se ha unido a la sala"
    assert response_u1["username"] == response_u2["username"] == "User2"
    assert response_u1["disconnected_user"] == response_u2["disconnected_user"] == None
    assert u1["username"] == "User1"
    assert u1["captain"] == True
    assert u2["username"] == "User2"
    assert u2["captain"] == False

    assert (
        len(json.loads(response_u1["actual_users"]))
        == len(json.loads(response_u2["actual_users"]))
        == 2
        == len(room.current_connections)
    )

    await communicator_1.disconnect()

    response_u2 = await communicator_2.receive_json_from()
    u2 = json.loads(response_u2["user"])

    assert response_u2["message_type"] == "disconnection"
    assert response_u2["message"] == "Se ha desconectado"
    assert response_u2["username"] == "User1"
    assert response_u2["disconnected_user"]["username"] == "User1"
    assert response_u2["disconnected_user"]["captain"] == True
    assert response_u2["disconnected_user"]["outsider"] == False
    assert response_u2["disconnected_user"]["state"] == State.LOBBY
    assert response_u2["disconnected_user"]["guessWord"] == ""
    assert u2["username"] == "User2"
    assert u2["captain"] == True

    test_room_instance = await sync_rest_calls.get_room(room_name=test_room)
    assert test_room_instance

    await communicator_2.disconnect()

    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_disconnection(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    await communicator_2.disconnect()

    response_1 = await communicator_1.receive_json_from()
    assert response_1["message_type"] == "disconnection"
    assert response_1["username"] == user_2["username"]
    assert response_1["disconnected_user"] == user_2

    await communicator_1.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_send_and_receive_chat_message(create_test_room):

    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")

    # Recieve "User2" connection message
    response_1 = await communicator_1.receive_json_from()

    await sync_rest_calls.create_room(room_name="other_room")
    # User3 is located in 'other_room' so he wont be able to interact the 'test_room' chat
    communicator_3, response_3 = await communicator_connection(
        username="User3", room="other_room"
    )

    # 'default' -> Chat message
    await communicator_1.send_json_to(
        {"action": "default", "message": "Testing chat... by User1"}
    )
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()

    assert response_1["message_type"] == response_2["message_type"] == "default"
    assert response_1["message"] == response_2["message"] == "Testing chat... by User1"

    assert await communicator_3.receive_nothing()

    # 'default' -> Chat/default message
    await communicator_1.send_json_to(
        {"action": "default", "message": "Testing chat... by User1"}
    )
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()

    assert response_1["message_type"] == response_2["message_type"] == "default"
    assert response_1["message"] == response_2["message"] == "Testing chat... by User1"

    # None action -> Chat/default message
    await communicator_2.send_json_to({"message": "Testing chat... by User2"})
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()

    assert response_1["message_type"] == response_2["message_type"] == "default"
    assert response_1["message"] == response_2["message"] == "Testing chat... by User2"

    assert await communicator_3.receive_nothing()

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    await communicator_3.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)
    assert await check_room_does_not_exist(room_name="other_room")


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_start_game(create_test_room):
    # The min-max number of players necessary to start a game are defined on the frontend
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    assert response_1["message_type"] == response_2["message_type"] == "startGame"
    assert response_1["actual_users"] == response_2["actual_users"]
    assert user_1["state"] in [State.PLAYING, State.PLAYER_TURN]
    assert user_2["state"] in [State.PLAYING, State.PLAYER_TURN]

    # One of the players must selected as an 'outsider'

    if (user_1["outsider"] and not user_2["outsider"]) or (
        not user_1["outsider"] and user_2["outsider"]
    ):
        assert True
    else:
        assert False

    assert response_1["key_word"]
    assert response_2["key_word"]

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_next_turn(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()

    order = json.loads(response_1["actual_users"])

    await communicator_1.send_json_to(
        {"action": "nextTurn", "message": "guessWord", "order": order}
    )

    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    assert response_1["message_type"] == response_2["message_type"] == "nextTurn"
    assert response_1["actual_users"] == response_2["actual_users"]

    if (user_1["state"] == State.PLAYING and user_2["state"] == State.PLAYER_TURN) or (
        user_1["state"] == State.PLAYER_TURN and user_2["state"] == State.PLAYING
    ):
        assert True
    else:
        assert False

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_voting_outsider(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})

    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    # User1 votes (to User2), to proceed the User2 must vote too
    await communicator_1.send_json_to(
        {"action": "votingOutsider", "message": user_2["id"]}
    )

    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()

    # User2 votes (to User2) and User1 counts and send the results because he's the captain
    await communicator_2.send_json_to(
        {"action": "votingOutsider", "message": user_2["id"]}
    )

    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    assert response_1["message_type"] == response_2["message_type"] == "votingComplete"
    assert response_1["player_out"] == response_2["player_out"] == user_2
    assert response_1["actual_users"] == response_2["actual_users"]

    # Because in this test is only played by 2 players, the continue condition it is of course false
    assert response_1["continue_playing"] == response_2["continue_playing"] == False

    # Check if the User2 was voted as an outsider
    if user_2["outsider"]:
        assert response_1["number_outsiders"] == response_2["number_outsiders"] == 0
    else:
        assert response_1["number_outsiders"] == response_2["number_outsiders"] == 1

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_voting_outsider_voting_game_captain(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})

    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    await communicator_1.send_json_to(
        {"action": "votingOutsider", "message": user_1["id"]}
    )

    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()

    await communicator_2.send_json_to(
        {"action": "votingOutsider", "message": user_1["id"]}
    )

    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    assert response_1["message_type"] == response_2["message_type"] == "votingComplete"
    assert response_1["actual_users"] == response_2["actual_users"]

    assert response_1["continue_playing"] == response_2["continue_playing"] == False

    if user_1["outsider"]:
        assert response_1["number_outsiders"] == response_2["number_outsiders"] == 0
    else:
        assert response_1["number_outsiders"] == response_2["number_outsiders"] == 1

    # Because the voted user it's the captain, for game logic reasons, it's role does the next capable user
    assert response_1["player_out"] == response_2["player_out"]
    assert not user_1["captain"]
    assert user_2["captain"]

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_voting_outsider_continue_playing(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    communicator_3, response_3 = await communicator_connection(username="User3")
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()

    communicator_4, response_4 = await communicator_connection(username="User4")
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    response_3 = await communicator_3.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})

    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])

    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    response_3 = await communicator_3.receive_json_from()
    user_3 = json.loads(response_3["user"])

    response_4 = await communicator_4.receive_json_from()
    user_4 = json.loads(response_4["user"])

    # Voting to a non-outsider player...
    voted_user = user_2 if not user_2["outsider"] else user_3

    await communicator_1.send_json_to(
        {"action": "votingOutsider", "message": voted_user["id"]}
    )
    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()
    assert await communicator_3.receive_nothing()
    assert await communicator_4.receive_nothing()

    await communicator_2.send_json_to(
        {"action": "votingOutsider", "message": voted_user["id"]}
    )
    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()
    assert await communicator_3.receive_nothing()
    assert await communicator_4.receive_nothing()

    await communicator_3.send_json_to(
        {"action": "votingOutsider", "message": voted_user["id"]}
    )
    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()
    assert await communicator_3.receive_nothing()
    assert await communicator_4.receive_nothing()

    await communicator_4.send_json_to(
        {"action": "votingOutsider", "message": voted_user["id"]}
    )
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    response_3 = await communicator_3.receive_json_from()
    response_4 = await communicator_4.receive_json_from()

    assert (
        response_1["message_type"]
        == response_2["message_type"]
        == response_3["message_type"]
        == response_4["message_type"]
        == "votingComplete"
    )

    assert (
        response_1["player_out"]["id"]
        == response_2["player_out"]["id"]
        == response_3["player_out"]["id"]
        == response_4["player_out"]["id"]
        == voted_user["id"]
    )

    # The voted user was an innocent player, then the game can continue between the remaining players because
    # there are more current players than -> 2 * number_outsiders

    assert (
        response_1["continue_playing"]
        == response_2["continue_playing"]
        == response_3["continue_playing"]
        == response_4["continue_playing"]
        == True
    )

    ###

    # Next round message
    await communicator_1.send_json_to({"action": "nextRound", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    response_3 = await communicator_3.receive_json_from()
    response_4 = await communicator_4.receive_json_from()

    ###

    # If there's another conclusive voting (for example all vote to the User4), the game is concluded because
    # there'll be none outsiders (User4 -> Outisder) or there'll be 1 outsider agaisnt only 1 innocent player

    if voted_user == user_2:
        await communicator_3.send_json_to(
            {"action": "votingOutsider", "message": user_4["id"]}
        )
    else:
        await communicator_2.send_json_to(
            {"action": "votingOutsider", "message": user_4["id"]}
        )

    await communicator_1.send_json_to(
        {"action": "votingOutsider", "message": user_4["id"]}
    )

    await communicator_4.send_json_to(
        {"action": "votingOutsider", "message": user_4["id"]}
    )

    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    response_3 = await communicator_3.receive_json_from()
    response_4 = await communicator_4.receive_json_from()

    assert (
        response_1["message_type"]
        == response_2["message_type"]
        == response_3["message_type"]
        == response_4["message_type"]
        == "votingComplete"
    )

    assert (
        response_1["player_out"]["id"]
        == response_2["player_out"]["id"]
        == response_3["player_out"]["id"]
        == response_4["player_out"]["id"]
        == user_4["id"]
    )

    assert (
        response_1["continue_playing"]
        == response_2["continue_playing"]
        == response_3["continue_playing"]
        == response_4["continue_playing"]
        == False
    )

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    await communicator_3.disconnect()
    await communicator_4.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_next_round(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    first_key_word = (
        response_1["key_word"] if user_2["outsider"] else response_2["key_word"]
    )

    await communicator_1.send_json_to({"action": "nextRound", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    user_1_next_round = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2_next_round = json.loads(response_2["user"])

    assert response_1["message_type"] == response_2["message_type"] == "nextRound"
    assert response_1["actual_users"] == response_2["actual_users"]
    assert user_1_next_round["state"] in [State.PLAYING, State.PLAYER_TURN]
    assert user_2_next_round["state"] in [State.PLAYING, State.PLAYER_TURN]

    assert user_1["outsider"] == user_1_next_round["outsider"]
    assert user_2["outsider"] == user_2_next_round["outsider"]

    assert response_1["key_word"] != first_key_word
    assert response_2["key_word"] != first_key_word

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_last_chance_messages(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    key_word = response_1["key_word"] if user_2["outsider"] else response_2["key_word"]

    await communicator_1.send_json_to({"action": "lastChance", "message": "wrong"})
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    assert response_1["last_chance_guess"] == response_2["last_chance_guess"] == False

    await communicator_1.send_json_to({"action": "lastChance", "message": key_word})
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    assert response_1["last_chance_guess"] == response_2["last_chance_guess"] == True

    await communicator_1.send_json_to(
        {"action": "lastChance", "message": key_word.lower()}
    )
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    assert response_1["last_chance_guess"] == response_2["last_chance_guess"] == True

    await communicator_1.send_json_to(
        {"action": "lastChance", "message": key_word.upper()}
    )
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()
    assert response_1["last_chance_guess"] == response_2["last_chance_guess"] == True

    await communicator_1.disconnect()
    await communicator_2.disconnect()
    assert await check_room_does_not_exist(room_name=test_room)


@pytest.mark.django_db()
@pytest.mark.parametrize("create_test_room", [test_room], indirect=True)
async def test_end_game(create_test_room):
    communicator_1, response_1 = await communicator_connection(username="User1")
    communicator_2, response_2 = await communicator_connection(username="User2")
    response_1 = await communicator_1.receive_json_from()

    await communicator_1.send_json_to({"action": "startGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    user_1 = json.loads(response_1["user"])
    response_2 = await communicator_2.receive_json_from()
    user_2 = json.loads(response_2["user"])

    key_word = response_1["key_word"] if user_2["outsider"] else response_2["key_word"]

    # Correct disconnection via 'endGame' message
    await communicator_1.send_json_to({"action": "endGame", "message": ""})
    response_1 = await communicator_1.receive_json_from()
    response_2 = await communicator_2.receive_json_from()

    assert await check_room_does_not_exist(room_name=test_room)
