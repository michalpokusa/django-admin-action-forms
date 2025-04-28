from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .formsets import InlineAdminActionFormSet

from django.contrib.admin import ModelAdmin
from django.contrib.admin.helpers import Fieldset
from django.contrib.admin.options import get_ul_class
from django.contrib.admin.utils import flatten_fieldsets
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
    ChoiceField,
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
    Widget,
)
from django.forms.widgets import CheckboxSelectMultiple, SelectMultiple
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

from .options import Options
from .widgets import (
    FilterHorizontalWidget,
    FilterVerticalWidget,
    ActionFormAutocompleteMixin,
    AutocompleteModelChoiceWidget,
    AutocompleteModelMultiChoiceWidget,
    RadioFieldsWidget,
)


class ActionForm(Form):
    """
    Base class for action forms used in admin actions.
    """

    template = "django_admin_action_forms/action_form.html"

    def __init__(
        self,
        modeladmin: ModelAdmin,
        action: str,
        request: HttpRequest,
        queryset: QuerySet,
        *args,
        **kwargs,
    ) -> None:
        self.modeladmin = modeladmin
        self.action = action
        self.request = request
        self.queryset = queryset

        super().__init__(*args, **kwargs)
        self.opts = Options(self)

        self._remove_excluded_fields()
        self._apply_limit_choices_to_on_model_choice_fields()
        self._replace_widgets_for_filter_horizontal_and_vertical()
        self._replace_widgets_for_autocomplete_fields()
        self._replace_widgets_for_radio_fields()
        self._add_default_selectmultiple_widget_help_text()
        self._add_autocomplete_widget_attrs()

    def _remove_excluded_fields(self) -> None:
        all_fields = set(self.fields.keys())
        included_fields = set(flatten_fieldsets(self.opts.get_fieldsets(self.request)))
        excluded_fields = all_fields.difference(included_fields)

        for field_name in excluded_fields:
            self.fields.pop(field_name)

    def _apply_limit_choices_to_on_model_choice_fields(self) -> None:
        for field in self.fields.values():
            if isinstance(field, (ModelChoiceField, ModelMultipleChoiceField)):
                queryset: QuerySet = field.queryset

                limit_choices_to = field.get_limit_choices_to()

                if limit_choices_to is not None:
                    field.queryset = queryset.complex_filter(limit_choices_to)

    def _replace_widgets_for_filter_horizontal_and_vertical(self) -> None:
        filter_horizontal = self.opts.filter_horizontal
        filter_vertical = self.opts.filter_vertical

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

            field.widget.is_required = field.required

    def _replace_widgets_for_autocomplete_fields(self) -> None:
        autocomplete_fields = self.opts.autocomplete_fields

        for field_name, field in self.fields.items():
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

    def _replace_widgets_for_radio_fields(self) -> None:
        radio_fields = self.opts.radio_fields
        for field_name, field in self.fields.items():
            if field_name in radio_fields:
                if isinstance(field, ChoiceField):
                    field.widget = RadioFieldsWidget(
                        attrs={"class": get_ul_class(radio_fields[field_name])},
                        choices=field.choices,
                    )

            field.widget.is_required = field.required

    def _add_default_selectmultiple_widget_help_text(self) -> None:
        for field in self.fields.values():
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

    def _add_autocomplete_widget_attrs(self) -> None:
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
        return [
            Fieldset(
                form=self,
                name=name,
                fields=field_options.get("fields", ()),
                classes=field_options.get("classes", ()),
                description=field_options.get("description", None),
            )
            for name, field_options in self.opts.get_fieldsets(self.request)
        ]

    @cached_property
    def inlines(self) -> "list[InlineAdminActionFormSet]":
        return [
            InlineFormSet(
                self.modeladmin, self.action, self.request, self.queryset, self.is_bound
            )
            for InlineFormSet in self.opts.get_inlines(self.request)
        ]

    @property
    def media(self):
        media = super().media

        # In Django<5.1, this adds "admin/js/collapse.js" when any fieldset has "collapse" class
        for fieldset in self.fieldsets:
            media += fieldset.media

        for inline in self.inlines:
            media += inline.media

        return media

    def inlines_are_valid(self) -> bool:
        return all(inline.is_valid() for inline in self.inlines)

    @property
    def inlines_cleaned_data(self):
        return {
            f"{inline.name}": [data for data in inline.cleaned_data if data]
            for inline in self.inlines
        }

    def action_form_view(self, request: HttpRequest, extra_context: dict = None):
        admin_site = self.modeladmin.admin_site
        app_config = self.modeladmin.opts.app_config

        context = {
            **admin_site.each_context(request),
            "title": self.modeladmin.get_actions(request).get(self.action)[2],
            "subtitle": None,
            "app_label": app_config.label,
            "app_verbose_name": app_config.verbose_name,
            "model_name": self.modeladmin.opts.model_name,
            "model_verbose_name": self.modeladmin.opts.verbose_name,
            "model_verbose_name_plural": self.modeladmin.opts.verbose_name_plural,
            "help_text": self.opts.help_text,
            "list_objects": self.opts.list_objects,
            "queryset": self.queryset,
            "form": self,
            "fieldsets": self.fieldsets,
            "inlines": self.inlines,
            "action": self.action,
            "select_across": request.POST.get("select_across", "0"),
            "selected_action": request.POST.getlist("_selected_action"),
            "confirm_button_text": self.opts.confirm_button_text,
            "cancel_button_text": self.opts.cancel_button_text,
            **(extra_context or {}),
        }

        return TemplateResponse(request, self.template, context)

    if TYPE_CHECKING:

        class Meta:
            list_objects: bool
            help_text: "str | None"

            fields: "list[str | tuple[str, ...]] | None"
            fieldsets: (
                "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None"
            )

            filter_horizontal: "list[str]"
            filter_vertical: "list[str]"
            autocomplete_fields: "list[str]"
            radio_fields: "dict[str, int]"

            inlines: "list[type[InlineAdminActionFormSet]]"

            confirm_button_text: str
            cancel_button_text: str

            def get_fields(
                self, request: HttpRequest
            ) -> "list[str | tuple[str, ...]]": ...

            def get_fieldsets(
                self, request: HttpRequest
            ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]]": ...

            def get_inlines(
                self, request: HttpRequest
            ) -> "list[type[InlineAdminActionFormSet]]": ...


class AdminActionForm(ActionForm):
    """
    Extended `ActionForm` class for admin actions. It replaces default field widgets
    with corresponding admin widgets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._replace_default_field_widgets_with_admin_widgets()

    ADMIN_WIDGETS_FOR_FIELDS: "dict[type[Field], type[Widget]]" = {
        CharField: AdminTextInputWidget,
        DateField: AdminDateWidget,
        EmailField: AdminEmailInputWidget,
        FileField: AdminFileWidget,
        IntegerField: AdminIntegerFieldWidget,
        SplitDateTimeField: AdminSplitDateTime,
        TimeField: AdminTimeWidget,
        URLField: AdminURLFieldWidget,
        UUIDField: AdminUUIDInputWidget,
    }

    def _replace_default_field_widgets_with_admin_widgets(self) -> None:
        for field in self.fields.values():
            if type(field.widget) is type(field).widget:
                admin_widget_type = self.ADMIN_WIDGETS_FOR_FIELDS.get(type(field))

                if admin_widget_type is not None:
                    widget_attrs = field.widget.attrs

                    field.widget = admin_widget_type()
                    field.widget.is_required = field.required
                    field.widget.attrs.update(widget_attrs)


class InlineActionForm(ActionForm):

    def __init__(self, formset: "InlineAdminActionFormSet", *args, **kwargs):
        self.formset = formset
        super().__init__(*args, **kwargs)

    def _add_autocomplete_widget_attrs(self):
        super()._add_autocomplete_widget_attrs()
        for field_name, field in self.fields.items():
            if isinstance(field.widget, ActionFormAutocompleteMixin):
                field.widget.attrs["data-inline-name"] = self.formset.name


class InlineAdminActionForm(AdminActionForm, InlineActionForm): ...
