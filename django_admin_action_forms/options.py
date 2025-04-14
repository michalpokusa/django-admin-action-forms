from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .forms import ActionForm


from django.http import HttpRequest
from django.utils.translation import gettext_lazy


class Options:

    list_objects: bool
    help_text: "str | None"
    fields: "list[str | tuple[str, ...]] | None"
    fieldsets: "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None"
    autocomplete_fields: "list[str]"
    filter_horizontal: "list[str]"
    filter_vertical: "list[str]"
    confirm_button_text: str
    cancel_button_text: str

    def __init__(self, meta: type):
        self._meta: "ActionForm.Meta" = meta()

        self.list_objects = getattr(self._meta, "list_objects", False)
        self.help_text = getattr(self._meta, "help_text", None)
        self.fields = getattr(self._meta, "fields", None)
        self.fieldsets = getattr(self._meta, "fieldsets", None)
        self.autocomplete_fields = getattr(self._meta, "autocomplete_fields", [])
        self.filter_horizontal = getattr(self._meta, "filter_horizontal", [])
        self.filter_vertical = getattr(self._meta, "filter_vertical", [])
        self.confirm_button_text = getattr(
            self._meta, "confirm_button_text", gettext_lazy("Confirm")
        )
        self.cancel_button_text = getattr(
            self._meta, "cancel_button_text", gettext_lazy("Cancel")
        )

    def get_fields(self, request: HttpRequest) -> "list[str | tuple[str, ...]] | None":
        if hasattr(self._meta, "get_fields"):
            return self._meta.get_fields(request)
        return self.fields

    def get_fieldsets(
        self, request: HttpRequest
    ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None":
        if hasattr(self._meta, "get_fieldsets"):
            return self._meta.get_fieldsets(request)
        return self.fieldsets
