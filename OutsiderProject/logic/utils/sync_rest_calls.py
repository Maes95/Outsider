from asgiref.sync import sync_to_async
from ..models import RoomModel, WordsListModel
from ..apps import import_current_word_list


@sync_to_async
def get_room(room_name):
    room = RoomModel.objects.get(name=room_name)
    return room


@sync_to_async
def print_get_all_rooms():
    query = RoomModel.objects.all().values_list()
    print(query)


@sync_to_async
def create_room(room_name):
    try:
        room = RoomModel.objects.create(name=room_name)
        return room
    except:
        return "Room with that name already created in the database"


@sync_to_async
def update_room(room):
    return room.save()


@sync_to_async
def delete_room(room_name):
    return RoomModel.objects.get(name=room_name).delete()


@sync_to_async
def get_word_list():
    return WordsListModel.objects.get(name="Current")


@sync_to_async
def set_word_list():
    import_current_word_list()
