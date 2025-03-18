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
)


class ActionForm(Form):
    """
    Base class for action forms used in admin actions.
    """

    template = "django_admin_action_forms/action_form.html"

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
        self.opts = Options(self.Meta)

        self._remove_excluded_fields()
        self._apply_limit_choices_to_on_model_choice_fields()
        self._replace_widgets_for_filter_and_autocomplete_fields()
        self._add_default_selectmultiple_widget_help_text()
        self._add_autocomplete_widget_attrs()

    def _remove_excluded_fields(self) -> None:
        all_fields = set(self.fields.keys())
        included_fields: "set[str]" = set()

        fieldsets = self.opts.get_fieldsets(self.request)
        fields = self.opts.get_fields(self.request)

        if fieldsets is not None:
            for name, field_options in fieldsets:
                for field in field_options.get("fields", ()):
                    if isinstance(field, (list, tuple)):
                        included_fields.update(field)
                    else:
                        included_fields.add(field)

        elif fields is not None:
            for field in fields:
                if isinstance(field, (list, tuple)):
                    included_fields.update(field)
                else:
                    included_fields.add(field)

        else:
            included_fields = all_fields

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

    def _replace_widgets_for_filter_and_autocomplete_fields(self) -> None:
        autocomplete_fields = self.opts.autocomplete_fields
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

        fieldsets = self.opts.get_fieldsets(self.request)
        if fieldsets is not None:
            return [
                Fieldset(
                    form=self,
                    name=name,
                    fields=field_options.get("fields", ()),
                    classes=field_options.get("classes", ()),
                    description=field_options.get("description", None),
                )
                for name, field_options in fieldsets
            ]

        fields = self.opts.get_fields(self.request)
        if fields is not None:
            return [Fieldset(form=self, fields=tuple(fields))]

        return [Fieldset(form=self, fields=tuple(self.fields.keys()))]

    @property
    def media(self):
        media = super().media

        # In Django<5.1, this adds "admin/js/collapse.js" when any fieldset has "collapse" class
        for fieldset in self.fieldsets:
            media += fieldset.media

        return media

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
            "action": self.action,
            "select_across": request.POST.get("select_across", "0"),
            "selected_action": request.POST.getlist("_selected_action"),
            "confirm_button_text": self.opts.confirm_button_text,
            "cancel_button_text": self.opts.cancel_button_text,
            **(extra_context or {}),
        }

        return TemplateResponse(request, self.template, context)

    class Meta:
        list_objects: bool
        help_text: "str | None"

        fields: "list[str | tuple[str, ...]] | None"
        fieldsets: (
            "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None"
        )

        autocomplete_fields: "list[str]"
        filter_horizontal: "list[str]"
        filter_vertical: "list[str]"

        confirm_button_text: str
        cancel_button_text: str

        def get_fields(
            self, request: HttpRequest
        ) -> "list[str | tuple[str, ...]] | None": ...

        def get_fieldsets(
            self, request: HttpRequest
        ) -> "list[tuple[str|None, dict[str, list[str | tuple[str, ...]]]]] | None": ...


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
