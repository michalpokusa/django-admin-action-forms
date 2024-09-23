import json
from typing import Any

from django.conf import settings
from django.forms import Select, SelectMultiple, Media, Widget
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin.widgets import FilteredSelectMultiple

# Django 4.1.x and above
try:
    from django.contrib.admin.widgets import get_select2_language
# Backwards compatibility for Django 3.2.x
except ImportError:
    from django.contrib.admin.widgets import SELECT2_TRANSLATIONS
    from django.utils.translation import get_language

    # Copied django.contrib.admin.widgets.get_select2_language
    def get_select2_language():
        lang_code = get_language()
        supported_code = SELECT2_TRANSLATIONS.get(lang_code)
        if supported_code is None and lang_code is not None:
            # If 'zh-hant-tw' is not supported, try subsequent language codes i.e.
            # 'zh-hant' and 'zh'.
            i = None
            while (i := lang_code.rfind("-", 0, i)) > -1:
                if supported_code := SELECT2_TRANSLATIONS.get(lang_code[:i]):
                    return supported_code
        return supported_code


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
        attrs.update(
            {
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
                        "admin-actionform-autocomplete",
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
