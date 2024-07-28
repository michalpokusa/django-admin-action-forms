import json
from typing import Any

from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple, get_select2_language
from django.forms import Select, SelectMultiple, Media, Widget
from django.urls import reverse
from django.utils.html import format_html


class RenderInsideDivMixin(Widget):
    """
    Renders the original widget inside a div element.

    Simulates `RelatedFieldWidgetWrapper`, as Select2 expects a parent div element.
    """

    def render(self, *args, **kwargs):
        rendered_widget = super().render(*args, **kwargs)

        return format_html(f"<div>{rendered_widget}</div>")


class ActionFormAutocompleteMixin(Widget):
    """
    Modified `django.contrib.admin.widgets.AutocompleteMixin` customized to work with
    action form autocomplete widgets.
    """

    def build_attrs(
        self, base_attrs: "dict[str, Any]", extra_attrs: "dict[str, Any] | None" = None
    ) -> "dict[str, Any]":
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("class", "")
        attrs.update(
            {
                **base_attrs,
                **(extra_attrs or {}),
                "data-ajax--cache": "true",
                "data-ajax--delay": 250,
                "data-ajax--type": "GET",
                "data-ajax--url": reverse("django_admin_action_forms:autocomplete"),
                "data-theme": "admin-autocomplete",
                "data-allow-clear": json.dumps(not self.is_required),
                "data-placeholder": "",
                "lang": get_select2_language(),
                "class": " ".join(
                    [
                        *attrs.get("class", "").split(),
                        "admin-autocomplete",
                    ]
                ),
            }
        )

        return attrs

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"

        select2_language = get_select2_language()
        i18n_file = (
            (f"admin/js/vendor/select2/i18n/{select2_language}.js",)
            if select2_language
            else ()
        )

        return Media(
            js=(
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/vendor/select2/select2.full%s.js" % extra,
            )
            + i18n_file
            + (
                "admin/js/jquery.init.js",
                "django_admin_action_forms/js/action_form_autocomplete.js",
            ),
            css={
                "screen": (
                    "admin/css/vendor/select2/select2%s.css" % extra,
                    "admin/css/autocomplete.css",
                ),
            },
        )


class FilterHorizontalWidget(RenderInsideDivMixin, FilteredSelectMultiple): ...


class FilterVerticalWidget(RenderInsideDivMixin, FilteredSelectMultiple): ...


class AutocompleteModelChoiceWidget(
    ActionFormAutocompleteMixin, RenderInsideDivMixin, Select
): ...


class AutocompleteModelMultiChoiceWidget(
    ActionFormAutocompleteMixin, RenderInsideDivMixin, SelectMultiple
): ...
