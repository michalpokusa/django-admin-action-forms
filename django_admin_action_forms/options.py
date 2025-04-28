from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .forms import ActionForm

from django.http import HttpRequest
from django.utils.translation import gettext_lazy

from .formsets import InlineAdminActionFormSet


class Options:

    list_objects: bool
    help_text: "str | None"
    fields: "list[str | tuple[str, ...]] | None"
    fieldsets: "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None"
    filter_horizontal: "list[str]"
    filter_vertical: "list[str]"
    autocomplete_fields: "list[str]"
    radio_fields: "dict[str, int]"
    inlines: "list[type[InlineAdminActionFormSet]]"
    confirm_button_text: str
    cancel_button_text: str

    def __init__(self, form: "ActionForm"):
        self._form = form
        self._meta = form.Meta() if hasattr(form, "Meta") else None

        self.list_objects = getattr(self._meta, "list_objects", False)
        self.help_text = getattr(self._meta, "help_text", None)
        self.fields = getattr(self._meta, "fields", None)
        self.fieldsets = getattr(self._meta, "fieldsets", None)
        self.filter_horizontal = getattr(self._meta, "filter_horizontal", [])
        self.filter_vertical = getattr(self._meta, "filter_vertical", [])
        self.autocomplete_fields = getattr(self._meta, "autocomplete_fields", [])
        self.radio_fields = getattr(self._meta, "radio_fields", {})
        self.inlines = getattr(self._meta, "inlines", None)
        self.confirm_button_text = getattr(
            self._meta, "confirm_button_text", gettext_lazy("Confirm")
        )
        self.cancel_button_text = getattr(
            self._meta, "cancel_button_text", gettext_lazy("Cancel")
        )

    def get_fields(self, request: HttpRequest) -> "list[str | tuple[str, ...]]":
        if hasattr(self._meta, "get_fields"):
            return self._meta.get_fields(request)
        if self.fields is not None:
            return self.fields
        return tuple(self._form.fields.keys())

    def get_fieldsets(
        self, request: HttpRequest
    ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]]":
        if hasattr(self._meta, "get_fieldsets"):
            return self._meta.get_fieldsets(request)
        if self.fieldsets is not None:
            return self.fieldsets
        return [(None, {"fields": self.get_fields(request)})]

    def get_inlines(
        self, request: HttpRequest
    ) -> "list[type[InlineAdminActionFormSet]]":
        if hasattr(self._meta, "get_inlines"):
            return self._meta.get_inlines(request)
        if self.inlines is not None:
            return self.inlines
        return []
