from django import forms
from django.contrib.admin.helpers import Fieldset
from django.contrib.admin.widgets import (
    AdminDateWidget,
    AdminTimeWidget,
    AdminSplitDateTime,
)


class ActionForm(forms.Form):

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
