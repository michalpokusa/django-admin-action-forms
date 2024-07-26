from django import forms
from django.contrib.admin.helpers import Fieldset
from django.contrib.admin.widgets import (
    AdminDateWidget,
    AdminTimeWidget,
    AdminSplitDateTime,
)

from .widgets import (
    FilterHorizontalWidget,
    FilterVerticalWidget,
)


class ActionForm(forms.Form):

    def __init_subclass__(cls):

        meta: ActionForm.Meta = getattr(cls, "Meta", None)
        filter_horizontal = getattr(meta, "filter_horizontal", [])
        filter_vertical = getattr(meta, "filter_vertical", [])

        fields = {
            **cls.base_fields,
            **cls.declared_fields,
        }

        for field_name, field in fields.items():
            if field_name in filter_horizontal:
                field.widget = FilterHorizontalWidget(
                    verbose_name=field.label,
                    is_stacked=False,
                    choices=field.choices,
                )

            if field_name in filter_vertical:
                field.widget = FilterVerticalWidget(
                    verbose_name=field.label,
                    is_stacked=True,
                    choices=field.choices,
                )

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
        fieldsets: "list[tuple[str|None, dict[str, int]]]"

        filter_horizontal: "list[str]"
        filter_vertical: "list[str]"


class AdminActionForm(ActionForm):

    def __init_subclass__(cls):
        fields = {
            **cls.base_fields,
            **cls.declared_fields,
        }

        for field in fields.values():

            if isinstance(field, forms.DateField):
                field.widget = AdminDateWidget()
                continue

            if isinstance(field, forms.TimeField):
                field.widget = AdminTimeWidget()
                continue

            if isinstance(field, forms.SplitDateTimeField):
                field.widget = AdminSplitDateTime()
                continue

        return super().__init_subclass__()
