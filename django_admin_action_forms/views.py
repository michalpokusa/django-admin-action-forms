from django.apps import apps
from django.contrib.admin import AdminSite, ModelAdmin, sites
from django.db.models import Model
from django.db.models import QuerySet
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.http import (
    HttpRequest,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.views.generic.list import BaseListView

from .forms import ActionForm


class ActionFormAutocompleteJsonView(BaseListView):
    """
    Modified `django.contrib.admin.views.autocomplete.AutocompleteJsonView` customized to work with
    action form autocomplete widgets.
    """

    paginate_by = 20

    def get(self, request: HttpRequest):
        """
        Handles autocomplete requests made by the `AutocompleteModelChoiceWidget` and `AutocompleteModelMultiChoiceWidget` widgets.

        Depending on GET parameters and user permissions may return a `400 Bad Request`, `403 Forbidden`, or `200 OK` response
        with a JSON object containing the results and pagination information.

        Returned objects are filtered from `queryset` specified on field and restricted by the `limit_choices_to` attribute.
        """
        if not request.user.is_staff:
            return HttpResponseForbidden()

        GET_admin_site = request.GET.get("admin_site")
        GET_app_label = request.GET.get("app_label")
        GET_model_name = request.GET.get("model_name")
        GET_action_name = request.GET.get("action_name")
        GET_field_name = request.GET.get("field_name")
        GET_page = request.GET.get("page", "1")
        GET_term = request.GET.get("term", "")

        if (
            GET_admin_site is None
            or GET_app_label is None
            or GET_model_name is None
            or GET_action_name is None
            or GET_field_name is None
        ):
            return HttpResponseBadRequest()

        # AdminSite
        admin_site: "AdminSite | None" = [
            *[site for site in sites.all_sites if site.name == GET_admin_site],
            None,
        ][0]
        if admin_site is None:
            return HttpResponseBadRequest()

        # Model
        try:
            model = apps.get_model(GET_app_label, GET_model_name)
        except LookupError:
            return HttpResponseBadRequest()

        # AdminSite & Model -> ModelAdmin
        model_admin: "ModelAdmin | None" = admin_site._registry.get(model, None)

        if model_admin is None:
            return HttpResponseBadRequest()

        if not model_admin.has_view_permission(request):
            return HttpResponseForbidden()

        # ModelAdmin -> Action
        try:
            action, _, _ = model_admin.get_actions(request).get(GET_action_name)
        except TypeError:
            return HttpResponseBadRequest()

        # Action -> ActionForm
        action_form = getattr(action, "form_class", None)

        if action_form is None or not issubclass(action_form, ActionForm):
            return HttpResponseBadRequest()

        # ActionForm -> Field
        field = {
            **action_form.base_fields,
            **action_form.declared_fields,
        }.get(GET_field_name)

        if not isinstance(field, (ModelChoiceField, ModelMultipleChoiceField)):
            return HttpResponseBadRequest()

        # Field -> QuerySet
        queryset: "QuerySet[Model]" = field.queryset

        limit_choices_to = field.get_limit_choices_to()

        if limit_choices_to is not None:
            queryset = queryset.complex_filter(limit_choices_to)

        queryset_modeladmin: "ModelAdmin | None" = admin_site._registry.get(
            queryset.model, None
        )

        if queryset_modeladmin is None:
            return HttpResponseBadRequest()

        queryset, may_have_duplicates = queryset_modeladmin.get_search_results(
            request, queryset, GET_term
        )

        if may_have_duplicates:
            queryset = queryset.distinct()

        if not queryset.ordered:
            queryset = queryset.order_by("pk")

        # QuerySet -> Paginator & Page
        paginator = model_admin.get_paginator(request, queryset, self.paginate_by)
        page = paginator.get_page(GET_page)

        return JsonResponse(
            {
                "results": [{"id": str(obj.pk), "text": str(obj)} for obj in page],
                "pagination": {"more": page.has_next()},
            }
        )
