from django.contrib.admin import ModelAdmin
from django.contrib.admin.helpers import Fieldset
from django.contrib.admin.widgets import (
    AdminDateWidget,
    AdminEmailInputWidget,
    AdminFileWidget,
    AdminIntegerFieldWidget,
    AdminSplitDateTime,
    AdminTextInputWidget,
    AdminTimeWidget,
    AdminURLFieldWidget,
    AdminUUIDInputWidget,
)
from django.db.models import QuerySet
from django.forms import (
    CharField,
    DateField,
    EmailField,
    Field,
    FileField,
    Form,
    IntegerField,
    ModelChoiceField,
    ModelMultipleChoiceField,
    SplitDateTimeField,
    TimeField,
    URLField,
    UUIDField,
)
from django.forms.widgets import CheckboxSelectMultiple, SelectMultiple
from django.http import HttpRequest
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

from .widgets import (
    FilterHorizontalWidget,
    FilterVerticalWidget,
    ActionFormAutocompleteMixin,
    AutocompleteModelChoiceWidget,
    AutocompleteModelMultiChoiceWidget,
)


class ActionForm(Form):
    """
    Base class for action forms used in admin actions.
    """

    def __init__(
        self,
        modeladmin: ModelAdmin,
        request: HttpRequest,
        queryset: QuerySet,
        *args,
        **kwargs
    ) -> None:
        self.modeladmin = modeladmin
        self.request = request
        self.queryset = queryset

        try:
            action_index = int(request.POST.get("index", 0))
        except ValueError:
            action_index = 0

        self.action = request.POST.getlist("action")[action_index]

        super().__init__(*args, **kwargs)
        self.__post_init__(modeladmin, request, queryset)

        self._remove_excluded_fields()
        self._apply_limit_choices_to_on_model_choice_fields()
        self._replace_widgets_for_filter_and_autocomplete_fields()
        self._add_default_selectmultiple_widget_help_text()
        self._add_autocomplete_fields_widget_attrs()

    def __post_init__(
        self, modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet
    ) -> None: ...

    def _remove_excluded_fields(self) -> None:
        for field_name in self._get_excluded_fields():
            self.fields.pop(field_name)

    def _apply_limit_choices_to_on_model_choice_fields(self) -> None:
        for field in self.fields.values():
            if isinstance(field, (ModelChoiceField, ModelMultipleChoiceField)):
                queryset: QuerySet = field.queryset

                limit_choices_to = field.get_limit_choices_to()

                if limit_choices_to is not None:
                    field.queryset = queryset.complex_filter(limit_choices_to)

    def _replace_widgets_for_filter_and_autocomplete_fields(self) -> None:
        autocomplete_fields = getattr(self.Meta, "autocomplete_fields", [])
        filter_horizontal = getattr(self.Meta, "filter_horizontal", [])
        filter_vertical = getattr(self.Meta, "filter_vertical", [])

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

    def _add_default_selectmultiple_widget_help_text(self) -> None:
        for field in self.fields.values():
            field: Field
            if (
                isinstance(field.widget, SelectMultiple)
                and field.widget.allow_multiple_selected
                and not isinstance(
                    field.widget,
                    (CheckboxSelectMultiple, AutocompleteModelMultiChoiceWidget),
                )
            ):
                msg = gettext_lazy(
                    "Hold down “Control”, or “Command” on a Mac, to select more than one."
                )
                help_text = field.help_text
                field.help_text = (
                    format_lazy("{} {}", help_text, msg) if help_text else msg
                )

    def _add_autocomplete_fields_widget_attrs(self) -> None:
        for field_name, field in self.fields.items():
            if isinstance(field.widget, ActionFormAutocompleteMixin):
                field.widget.attrs.update(
                    {
                        "data-admin-site": self.modeladmin.admin_site.name,
                        "data-app-label": self.modeladmin.opts.app_config.label,
                        "data-model-name": self.modeladmin.opts.model_name,
                        "data-action-name": self.action,
                        "data-field-name": field_name,
                    }
                )

    @cached_property
    def fieldsets(self) -> "list[Fieldset]":
        fieldsets = None
        fields = None

        if hasattr(self.Meta, "get_fieldsets") and callable(self.Meta.get_fieldsets):
            fieldsets = self.Meta.get_fieldsets(self.request)
        elif hasattr(self.Meta, "fieldsets"):
            fieldsets = self.Meta.fieldsets
        elif hasattr(self.Meta, "get_fields") and callable(self.Meta.get_fields):
            fields = self.Meta.get_fields(self.request)
        elif hasattr(self.Meta, "fields"):
            fields = self.Meta.fields

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

    def _get_included_fields(self) -> "set[str]":
        field_names: "set[str]" = set()
        for fieldset in self.fieldsets:
            for field in fieldset.fields:
                if isinstance(field, (list, tuple)):
                    field_names.update(field)
                else:
                    field_names.add(field)

        return field_names

    def _get_excluded_fields(self) -> "set[str]":
        all_fields = set(self.fields.keys())
        included_fields = self._get_included_fields()

        return all_fields.difference(included_fields)

    @property
    def media(self):
        media = super().media

        # Adds "admin/js/collapse.js" in django<5.1 when any fieldset has "collapse" class
        for fieldset in self.fieldsets:
            media += fieldset.media

        return media

    class Meta:
        list_objects: bool
        help_text: str

        fields: "list[str | tuple[str, ...]]"
        fieldsets: "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]]"

        autocomplete_fields: "list[str]"
        filter_horizontal: "list[str]"
        filter_vertical: "list[str]"

        confirm_button_text: str
        cancel_button_text: str

        @classmethod
        def get_fields(cls, request: HttpRequest) -> "list[str | tuple[str, ...]]":
            return getattr(cls, "fields", None)

        @classmethod
        def get_fieldsets(
            cls, request: HttpRequest
        ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]]":
            return getattr(cls, "fieldsets", None)


def is_field_with_default_widget(field: Field, field_type: "type[Field]") -> bool:
    """
    Checks if the field is exactly of the specified type and has the default widget.
    """
    return type(field) is field_type and type(field.widget) is field_type.widget


class AdminActionForm(ActionForm):
    """
    Extended `ActionForm` class for admin actions. It replaces default field widgets
    with corresponding admin widgets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._replace_default_field_widgets_with_admin_widgets()

    def _replace_default_field_widgets_with_admin_widgets(self) -> None:
        for field in self.fields.values():
            widget_attrs = field.widget.attrs

            if is_field_with_default_widget(field, CharField):
                field.widget = AdminTextInputWidget()

            elif is_field_with_default_widget(field, DateField):
                field.widget = AdminDateWidget()

            elif is_field_with_default_widget(field, EmailField):
                field.widget = AdminEmailInputWidget()

            elif is_field_with_default_widget(field, FileField):
                field.widget = AdminFileWidget()

            elif is_field_with_default_widget(field, IntegerField):
                field.widget = AdminIntegerFieldWidget()

            elif is_field_with_default_widget(field, SplitDateTimeField):
                field.widget = AdminSplitDateTime()

            elif is_field_with_default_widget(field, TimeField):
                field.widget = AdminTimeWidget()

            elif is_field_with_default_widget(field, URLField):
                field.widget = AdminURLFieldWidget()

            elif is_field_with_default_widget(field, UUIDField):
                field.widget = AdminUUIDInputWidget()

            field.widget.is_required = field.required
            field.widget.attrs.update(widget_attrs)
