from django.apps import apps
from django.contrib.admin import AdminSite, ModelAdmin, sites
from django.core.paginator import Paginator
from django.db.models import Model
from django.db.models import QuerySet
from django.forms import (
    ChoiceField,
    MultipleChoiceField,
    ModelChoiceField,
    ModelMultipleChoiceField,
)
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

        Returned objects are filtered from queryset specified on field.
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

        # AdminSite -> Model
        try:
            model = apps.get_model(GET_app_label, GET_model_name)
        except LookupError:
            return HttpResponseBadRequest()

        # Model -> ModelAdmin
        model_admin: ModelAdmin = admin_site._registry[model]

        if not model_admin.has_view_permission(request):
            return HttpResponseForbidden()

        # ModelAdmin -> Action
        try:
            action, _, _ = model_admin.get_action(GET_action_name)
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

        if isinstance(field, (ChoiceField, MultipleChoiceField)):

            # Field -> Choices
            choices = field.choices

            choices = sorted(
                [choice for choice in choices if GET_term.lower() in choice[1].lower()],
                key=lambda choice: choice[1],
            )

            # Choices -> Paginator & Page
            paginator = Paginator(choices, self.paginate_by)
            page = paginator.get_page(GET_page)

            return JsonResponse(
                {
                    "results": [
                        {"id": str(value), "text": str(label)} for value, label in page
                    ],
                    "pagination": {"more": page.has_next()},
                }
            )

        if isinstance(field, (ModelChoiceField, ModelMultipleChoiceField)):

            # Field -> QuerySet
            queryset: "QuerySet[Model]" = field.queryset

            queryset, may_have_duplicates = model_admin.get_search_results(
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
