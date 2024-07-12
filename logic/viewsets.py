from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action


from .models import RoomModel, WordsListModel


class RoomViewSet(GenericViewSet, RetrieveModelMixin, DestroyModelMixin):
    lookup_field = "name"
    queryset = RoomModel.objects.all()

    def get_serializer_class(self):
        return RoomSerializer

    def create(self, request, *args, **kwargs):
        if not "name" in request.data:
            return Response(
                "Wrong request (a room name is needed)",
                status.HTTP_400_BAD_REQUEST,
            )

        # Check the existence of a Room with the same code/name
        room_name = request.data["name"]
        room = RoomModel.objects.filter(name=room_name)

        if room:
            return Response(
                "Room name: '" + room_name + "' already taken",
                status.HTTP_302_FOUND,
            )

        # Create the room with the given name
        created_room = RoomModel.objects.create(name=room_name)

        serializer = RoomSerializer(instance=created_room, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomModel
        fields = ["id", "name", "started_game"]


class WordListViewSet(GenericViewSet, RetrieveModelMixin):
    lookup_field = "name"
    queryset = WordsListModel.objects.all()

    def get_serializer_class(self):
        return WordListSerializer


class WordListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordsListModel
        fields = ["id", "name", "word_list"]
