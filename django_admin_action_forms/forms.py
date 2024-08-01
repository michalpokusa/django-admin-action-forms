from django.contrib.admin.helpers import Fieldset
from django.contrib.admin.widgets import (
    AdminDateWidget,
    AdminTimeWidget,
    AdminSplitDateTime,
)
from django.forms import (
    Form,
    Field,
    ModelChoiceField,
    ModelMultipleChoiceField,
    DateField,
    TimeField,
    SplitDateTimeField,
)

from .widgets import (
    FilterHorizontalWidget,
    FilterVerticalWidget,
    AutocompleteModelChoiceWidget,
    AutocompleteModelMultiChoiceWidget,
)


class ActionForm(Form):

    def __init_subclass__(cls):

        meta: ActionForm.Meta = getattr(cls, "Meta", None)
        autocomplete_fields = getattr(meta, "autocomplete_fields", [])
        filter_horizontal = getattr(meta, "filter_horizontal", [])
        filter_vertical = getattr(meta, "filter_vertical", [])

        fields: "dict[str, Field]" = {
            **cls.base_fields,
            **cls.declared_fields,
        }

        for field_name, field in fields.items():
            if field_name in filter_horizontal:
                if isinstance(field, ModelMultipleChoiceField):
                    field.widget = FilterHorizontalWidget(
                        verbose_name=field.label,
                        is_stacked=False,
                        choices=field.choices,
                    )

            if field_name in filter_vertical:
                if isinstance(field, ModelMultipleChoiceField):
                    field.widget = FilterVerticalWidget(
                        verbose_name=field.label,
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

        return super().__init_subclass__()

    def get_fieldsets(self) -> "list[Fieldset]":
        meta: ActionForm.Meta = getattr(self, "Meta", None)

        if hasattr(meta, "fieldsets"):
            return [
                Fieldset(
                    form=self,
                    name=fieldset[0],
                    fields=tuple(fieldset[1].get("fields", [])),
                    classes=tuple(fieldset[1].get("classes", [])),
                    description=fieldset[1].get("description", None),
                )
                for fieldset in meta.fieldsets
            ]

        if hasattr(meta, "fields"):
            return [
                Fieldset(
                    form=self,
                    fields=tuple(getattr(meta, "fields", [])),
                )
            ]

        return [
            Fieldset(
                form=self,
                fields=tuple(self.fields.keys()),
            )
        ]

    class Meta:
        list_objects: bool
        help_text: str

        fields: "list[str]"
        fieldsets: "list[tuple[str|None, dict[str, list[str]]]]"

        autocomplete_fields: "list[str]"
        filter_horizontal: "list[str]"
        filter_vertical: "list[str]"


class AdminActionForm(ActionForm):

    def __init_subclass__(cls):
        fields = {
            **cls.base_fields,
            **cls.declared_fields,
        }

        for field in fields.values():

            if isinstance(field, DateField):
                field.widget = AdminDateWidget()
                continue

            if isinstance(field, TimeField):
                field.widget = AdminTimeWidget()
                continue

            if isinstance(field, SplitDateTimeField):
                field.widget = AdminSplitDateTime()
                continue

        return super().__init_subclass__()
