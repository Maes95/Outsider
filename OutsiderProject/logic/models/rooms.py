from django.db import models


class RoomModel(models.Model):
    class Meta:
        app_label = "logic"
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    name = models.CharField(
        max_length=256,
        unique=True,
        verbose_name="Nombre",
        help_text="Nombre de la sala",
    )

    current_connections = models.JSONField(
        verbose_name="Lista de conexiones actuales",
        default=list,
        blank=True,
        null=True,
    )

    number_outsiders = models.IntegerField(
        verbose_name="Outsiders",
        help_text="Número actual de outsiders en la partida",
        default=1,
    )

    repeated_words = models.JSONField(
        verbose_name="Palabras repetidas",
        help_text="Lista de palabras usadas en la partida",
        default=list,
        blank=True,
        null=True,
    )

    started_game = models.BooleanField(
        verbose_name="Partida en transcurso",
        help_text="Indica si la partida ha empezado",
        default=False,
    )

    def __str__(self):
        return self.name
