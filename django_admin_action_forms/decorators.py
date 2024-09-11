from functools import wraps
from types import FunctionType

from django.apps import AppConfig
from django.contrib.admin import ModelAdmin
from django.db.models import Model, QuerySet
from django.forms import Field
from django.http import HttpRequest
from django.template.response import TemplateResponse

from .forms import ActionForm
from .widgets import AutocompleteModelChoiceWidget, AutocompleteModelMultiChoiceWidget


def action_with_form(
    form_class: "type[ActionForm]",
    *,
    permissions: "list[str] | None" = None,
    description: "str | None" = None,
):
    """
    Decorator used to create an action with a form, alternative to the default ``@admin.action`` decorator.
    """

    def decorator(action_function: FunctionType):

        @wraps(action_function)
        def wrapper(*args):

            modeladmin: ModelAdmin
            request: HttpRequest
            queryset: QuerySet

            # Compatibility with django-no-queryset-admin-actions
            if any(isinstance(arg, QuerySet) for arg in args):
                modeladmin, request, queryset = args
            else:
                modeladmin, request = args
                queryset = modeladmin.model.objects.none()

            form = (
                form_class(request.POST)
                if "action_form" in request.POST
                else form_class()
            )
            form._remove_excluded_fields(request)
            form._replace_default_field_widgets(request)

            form_class_meta = getattr(form_class, "Meta", None)

            if form.is_valid():
                if queryset:
                    return action_function(
                        modeladmin, request, queryset, form.cleaned_data
                    )
                else:
                    return action_function(modeladmin, request, form.cleaned_data)

            app_config: AppConfig = modeladmin.opts.app_config
            model: Model = modeladmin.model

            action = request.POST.getlist("action")[int(request.POST.get("index"))]

            for field_name, field in form.fields.items():
                field: Field

                # Additional attributes required for autocomplete fields
                if isinstance(
                    field.widget,
                    (AutocompleteModelChoiceWidget, AutocompleteModelMultiChoiceWidget),
                ):
                    field.widget.attrs.update(
                        {
                            "data-admin-site": modeladmin.admin_site.name,
                            "data-app-label": model._meta.app_label,
                            "data-model-name": model._meta.model_name,
                            "data-action-name": action,
                            "data-field-name": field_name,
                        }
                    )

            context = {
                "title": modeladmin.get_actions(request).get(action)[2],
                # For default user tools to work
                "has_permission": True,
                "site_url": modeladmin.admin_site.site_url,
                # For default sidebar to work
                "is_nav_sidebar_enabled": True,
                "available_apps": modeladmin.admin_site.get_app_list(request),
                # Passing default POST values for actions
                "action": action,
                "select_across": request.POST.get("select_across"),
                "index": request.POST.get("index"),
                "selected_action": request.POST.getlist("_selected_action"),
                # For action form
                "app_label": app_config.label,
                "app_verbose_name": app_config.verbose_name,
                "model_name": model._meta.model_name,
                "model_verbose_name": model._meta.verbose_name,
                "model_verbose_name_plural": model._meta.verbose_name_plural,
                "help_text": getattr(form_class_meta, "help_text", None),
                "list_objects": getattr(form_class_meta, "list_objects", False),
                "queryset": queryset,
                "form": form,
                "fieldsets": form._get_fieldsets_for_context(request),
            }

            return TemplateResponse(
                request, "admin/django_admin_action_forms/action_form.html", context
            )

        setattr(wrapper, "form_class", form_class)

        if permissions is not None:
            setattr(wrapper, "allowed_permissions", permissions)

        if description is not None:
            setattr(wrapper, "short_description", description)

        return wrapper

    return decorator
