from typing import Any

from django.contrib.admin import ModelAdmin
from django.contrib.admin.helpers import ActionForm
from django.forms import CharField, HiddenInput
from django.http import HttpRequest
from django.template.response import TemplateResponse


class AdminActionFormsMixin(ModelAdmin):

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
