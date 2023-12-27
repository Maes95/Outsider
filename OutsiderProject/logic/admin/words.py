import json
from django.db.models import JSONField
from django.contrib import admin
from django.forms import widgets

from logic.models import WordsListModel


class PrettyJSONWidget(widgets.Textarea):
    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
            # These lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in value.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 120)
            return value
        except Exception as e:
            return super(PrettyJSONWidget, self).format_value(value)


class WordsListAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget}}


admin.site.register(WordsListModel, WordsListAdmin)
