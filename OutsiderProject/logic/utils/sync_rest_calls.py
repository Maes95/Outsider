from asgiref.sync import sync_to_async
from ..models import RoomModel, WordsListModel


@sync_to_async
def get_room(room_name):
    room = RoomModel.objects.get(name=room_name)
    return room


@sync_to_async
def update_room(room):
    return room.save()


@sync_to_async
def delete_room(room_name):
    return RoomModel.objects.get(name=room_name).delete()


@sync_to_async
def get_word_list():
    return WordsListModel.objects.get(name="Current")
