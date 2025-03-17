from django.http import HttpRequest
from django.utils.translation import gettext_lazy

from .forms import ActionForm


class Options:

    def __init__(self, meta: type):
        self._meta: ActionForm.Meta = meta

    @property
    def list_objects(self) -> bool:
        return getattr(self._meta, "list_objects", False)

    @property
    def help_text(self) -> "str | None":
        return getattr(self._meta, "help_text", None)

    @property
    def fields(self) -> "list[str | tuple[str, ...]] | None":
        return getattr(self._meta, "fields", None)

    @property
    def fieldsets(
        self,
    ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None":
        return getattr(self._meta, "fieldsets", None)

    @property
    def autocomplete_fields(self) -> "list[str]":
        return getattr(self._meta, "autocomplete_fields", [])

    @property
    def filter_horizontal(self) -> "list[str]":
        return getattr(self._meta, "filter_horizontal", [])

    @property
    def filter_vertical(self) -> "list[str]":
        return getattr(self._meta, "filter_vertical", [])

    @property
    def confirm_button_text(self) -> str:
        return getattr(self._meta, "confirm_button_text", gettext_lazy("Confirm"))

    @property
    def cancel_button_text(self) -> str:
        return getattr(self._meta, "cancel_button_text", gettext_lazy("Cancel"))

    def get_fields(self, request: HttpRequest) -> "list[str | tuple[str, ...]] | None":
        if hasattr(self, "get_fields") and callable(self.get_fields):
            return self.get_fields(request)
        return self.fields

    def get_fieldsets(
        self, request: HttpRequest
    ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None":
        if hasattr(self, "get_fieldsets") and callable(self.get_fieldsets):
            return self.get_fieldsets(request)
        return self.fieldsets
