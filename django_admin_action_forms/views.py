from django.contrib.admin import ModelAdmin
from django.db.models import Model
from django.db.models import QuerySet
from django.forms import Field, ModelChoiceField, ModelMultipleChoiceField
from django.http import (
    HttpRequest,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.views.generic.list import BaseListView

from .forms import ActionForm
from .formsets import InlineAdminActionFormSet


class ActionFormAutocompleteJsonView(BaseListView):
    """
    Modified `django.contrib.admin.views.autocomplete.AutocompleteJsonView` customized to work with
    action form autocomplete widgets.
    """

    paginate_by: int = 20
    model_admin: ModelAdmin

    def _get_field_by_name(
        self,
        form: "type[ActionForm]",
        field_name: str,
        inline_name: "str | None" = None,
    ) -> "Field | None":

        # Fields on the action form
        if inline_name is None:
            return form.base_fields.get(field_name, None)

        # Fields on the inline
        form_meta: "ActionForm.Meta | None" = getattr(form, "Meta", None)
        if form_meta is None:
            return None

        inlines: "list[InlineAdminActionFormSet]" = getattr(form_meta, "inlines", [])

        for inline in inlines:
            if inline.name != inline_name:
                continue

            return inline.form.base_fields.get(field_name, None)

        return None

    def get(self, request: HttpRequest):
        """
        Handles autocomplete requests made by the `AutocompleteModelChoiceWidget` and `AutocompleteModelMultiChoiceWidget` widgets.

        Depending on GET parameters and user permissions may return a `400 Bad Request`, `403 Forbidden`, or `200 OK` response
        with a JSON object containing the results and pagination information.

        Returned objects are filtered from `queryset` specified on field and restricted by the `limit_choices_to` attribute.
        """
        if not request.user.is_staff:
            return HttpResponseForbidden()

        action_name = request.GET.get("action_name")
        field_name = request.GET.get("field_name")
        inline_name = request.GET.get("inline_name")
        page_nr = int(request.GET.get("page", "1"))
        term = request.GET.get("term", "")

        if action_name is None or field_name is None:
            return HttpResponseBadRequest()

        if not self.model_admin.has_view_permission(request):
            return HttpResponseForbidden()

        # ModelAdmin -> Action
        try:
            action, _, _ = self.model_admin.get_actions(request).get(action_name)
        except TypeError:
            return HttpResponseBadRequest()

        # Action -> ActionForm
        action_form = getattr(action, "form_class", None)

        if action_form is None or not issubclass(action_form, ActionForm):
            return HttpResponseBadRequest()

        # ActionForm -> Field
        field = self._get_field_by_name(action_form, field_name, inline_name)

        if not isinstance(field, (ModelChoiceField, ModelMultipleChoiceField)):
            return HttpResponseBadRequest()

        # Field -> QuerySet
        queryset: "QuerySet[Model]" = field.queryset

        limit_choices_to = field.get_limit_choices_to()

        if limit_choices_to is not None:
            queryset = queryset.complex_filter(limit_choices_to)

        queryset_modeladmin: "ModelAdmin | None" = (
            self.model_admin.admin_site._registry.get(queryset.model, None)
        )

        if queryset_modeladmin is None:
            return HttpResponseBadRequest()

        queryset, may_have_duplicates = queryset_modeladmin.get_search_results(
            request, queryset, term
        )

        if may_have_duplicates:
            queryset = queryset.distinct()

        if not queryset.ordered:
            queryset = queryset.order_by("pk")

        # QuerySet -> Paginator & Page
        paginator = self.model_admin.get_paginator(request, queryset, self.paginate_by)
        page = paginator.get_page(page_nr)

        return JsonResponse(
            {
                "results": [{"id": str(obj.pk), "text": str(obj)} for obj in page],
                "pagination": {"more": page.has_next()},
            }
        )
