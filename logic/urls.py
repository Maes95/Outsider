# logic/urls.py
from rest_framework import routers
from .viewsets import RoomViewSet, WordListViewSet

router = routers.SimpleRouter()
router.register("rooms", RoomViewSet)
router.register("word_lists", WordListViewSet)

urlpatterns = router.urls
