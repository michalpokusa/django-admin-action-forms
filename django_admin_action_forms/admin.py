try:
    from typing import Any, override
except ImportError:

    def override(func):
        return func


from django.contrib.admin import ModelAdmin
from django.contrib.admin.helpers import ActionForm
from django.forms import CharField, HiddenInput
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.urls import path

from .views import ActionFormAutocompleteJsonView


class AdminActionFormsMixin(ModelAdmin):
    @override
    def get_urls(self):
        return [
            path(
                "action-form-autocomplete/",
                ActionFormAutocompleteJsonView.as_view(model_admin=self),
                name="%s_%s_action_form_autocomplete"
                % (self.opts.app_label, self.opts.model_name),
            ),
        ] + super().get_urls()

    @override
    def changelist_view(
        self, request: HttpRequest, extra_context: "dict[str, Any] | None" = None
    ):
        response = super().changelist_view(request, extra_context)

        if not isinstance(response, TemplateResponse):
            return response

        action_form = response.context_data.get("action_form")
        if not isinstance(action_form, ActionForm):
            return response

        action_form.fields.setdefault(
            "submitted_from_changelist_view",
            CharField(initial="1", label="", widget=HiddenInput),
        )

        return response
