from django.contrib import admin
from logic.models import RoomModel


class RoomAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


admin.site.register(RoomModel, RoomAdmin)
