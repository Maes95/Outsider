from django.db import models


class WordsListModel(models.Model):
    class Meta:
        app_label = "logic"
        verbose_name = "Word list"
        verbose_name_plural = "Word lists"

    name = models.CharField(
        max_length=256,
        unique=True,
        verbose_name="Nombre",
        help_text="Nombre de la lista",
    )

    word_list = models.JSONField(
        verbose_name="Lista de palabras",
        help_text="Donde 'a' es la pista para los jugadores y 'b' es la pista para los outsiders",
    )

    def __str__(self):
        return self.name
