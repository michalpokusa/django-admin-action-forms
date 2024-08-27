from django.contrib.admin.helpers import Fieldset
from django.contrib.admin.widgets import (
    AdminDateWidget,
    AdminTimeWidget,
    AdminSplitDateTime,
)
from django.forms import (
    Form,
    ModelChoiceField,
    ModelMultipleChoiceField,
    DateField,
    TimeField,
    SplitDateTimeField,
)
from django.http import HttpRequest

from .widgets import (
    FilterHorizontalWidget,
    FilterVerticalWidget,
    AutocompleteModelChoiceWidget,
    AutocompleteModelMultiChoiceWidget,
)


class ActionForm(Form):
    """
    Base class for action forms used in admin actions.
    """

    def _replace_default_field_widgets(self, request: HttpRequest) -> None:
        meta: ActionForm.Meta = getattr(self, "Meta", None)
        autocomplete_fields = getattr(meta, "autocomplete_fields", [])
        filter_horizontal = getattr(meta, "filter_horizontal", [])
        filter_vertical = getattr(meta, "filter_vertical", [])

        for field_name, field in self.fields.items():
            if field_name in filter_horizontal:
                if isinstance(field, ModelMultipleChoiceField):
                    field.widget = FilterHorizontalWidget(
                        verbose_name=field.get_bound_field(self, field_name).label,
                        is_stacked=False,
                        choices=field.choices,
                    )

            if field_name in filter_vertical:
                if isinstance(field, ModelMultipleChoiceField):
                    field.widget = FilterVerticalWidget(
                        verbose_name=field.get_bound_field(self, field_name).label,
                        is_stacked=True,
                        choices=field.choices,
                    )

            if field_name in autocomplete_fields:
                if isinstance(field, ModelChoiceField):
                    field.widget = AutocompleteModelChoiceWidget(
                        choices=field.choices,
                    )

                if isinstance(field, ModelMultipleChoiceField):
                    field.widget = AutocompleteModelMultiChoiceWidget(
                        choices=field.choices,
                    )

            field.widget.is_required = field.required

    def _get_fieldsets_for_context(self, request: HttpRequest) -> "list[Fieldset]":
        meta: ActionForm.Meta = getattr(self, "Meta", None)

        fieldsets = None
        fields = None

        if hasattr(meta, "get_fieldsets") and callable(meta.get_fieldsets):
            fieldsets = meta.get_fieldsets(request)
        elif hasattr(meta, "fieldsets"):
            fieldsets = meta.fieldsets
        elif hasattr(meta, "get_fields") and callable(meta.get_fields):
            fields = meta.get_fields(request)
        elif hasattr(meta, "fields"):
            fields = meta.fields

        if fields:
            some_fields_in_same_line = any(
                isinstance(field_name, (list, tuple)) for field_name in fields or []
            )

            if some_fields_in_same_line:
                fieldsets = [(None, {"fields": fields})]
                fields = None

        if fieldsets is not None:
            return [
                Fieldset(
                    form=self,
                    name=fieldset[0],
                    fields=tuple(fieldset[1].get("fields", [])),
                    classes=tuple(fieldset[1].get("classes", [])),
                    description=fieldset[1].get("description", None),
                )
                for fieldset in fieldsets
            ]

        if fields is not None:
            return [Fieldset(form=self, fields=tuple(fields))]

        return [Fieldset(form=self, fields=tuple(self.fields.keys()))]

    def _get_included_fields(self, request: HttpRequest) -> "set[str]":
        field_names: "set[str]" = set()
        for fieldset in self._get_fieldsets_for_context(request):
            for field in fieldset.fields:
                if isinstance(field, (list, tuple)):
                    field_names.update(field)
                else:
                    field_names.add(field)

        return field_names

    def _get_excluded_fields(self, request: HttpRequest) -> "set[str]":
        all_fields = set(self.fields.keys())
        included_fields = self._get_included_fields(request)

        return all_fields.difference(included_fields)

    def _remove_excluded_fields(self, request: HttpRequest) -> None:
        for field_name in self._get_excluded_fields(request):
            self.fields.pop(field_name)

    class Meta:
        list_objects: bool
        help_text: str

        fields: "list[str | tuple[str, ...]]"
        fieldsets: "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]]"

        autocomplete_fields: "list[str]"
        filter_horizontal: "list[str]"
        filter_vertical: "list[str]"

        @classmethod
        def get_fields(cls, request: HttpRequest) -> "list[str | tuple[str, ...]]":
            return getattr(cls, "fields", None)

        @classmethod
        def get_fieldsets(
            cls, request: HttpRequest
        ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]]":
            return getattr(cls, "fieldsets", None)


class AdminActionForm(ActionForm):
    """
    Extended `ActionForm` class for admin actions. It replaces default field widgets
    with corresponding admin widgets.
    """

    def _replace_default_field_widgets(self, request: HttpRequest) -> None:
        super()._replace_default_field_widgets(request)

        for field in self.fields.values():

            if isinstance(field, DateField):
                field.widget = AdminDateWidget()
            elif isinstance(field, TimeField):
                field.widget = AdminTimeWidget()
            elif isinstance(field, SplitDateTimeField):
                field.widget = AdminSplitDateTime()
