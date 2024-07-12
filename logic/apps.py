from django.apps import AppConfig
import json
import sys


def import_current_word_list():
    from logic.models import WordsListModel

    try:
        current_list = WordsListModel.objects.get(name="Current")
    except WordsListModel.DoesNotExist:
        current_list = WordsListModel.objects.create(name="Current", word_list="")

    if current_list.word_list == "":
        print("Updating current word_list with local...")
        current_list.word_list = json.load(open("logic/utils/word_list.json"))
        current_list.save()
    else:
        print("Current 'word_list' already uploaded")

    return


def clean_rooms():
    from logic.models import RoomModel

    try:
        print("Deleting 'zombie' rooms...")
        RoomModel.objects.all().delete()
    except Exception as e:
        print(e)
    return


class LogicConfig(AppConfig):
    name = "logic"
    verbose_name = "logic"

    def ready(self):
        # Must migrate to update the database, ignore if testing via 'pytest'
        if "migrate" in sys.argv or "pytest" in sys.modules:
            return
        else:
            clean_rooms()
            import_current_word_list()
