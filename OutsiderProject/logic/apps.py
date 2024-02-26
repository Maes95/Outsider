from django.apps import AppConfig
import json


class MyAppConfig(AppConfig):
    name = "logic"
    verbose_name = "logic"

    def ready(self):
        from django.db import models
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
