from functools import wraps
from types import FunctionType

from django.contrib.admin import ModelAdmin, site
from django.contrib.admin.helpers import Fieldset
from django.db.models import Model, QuerySet
from django.forms import Form
from django.http import HttpRequest
from django.template.response import TemplateResponse


def action_with_form(
    form_class: "type[Form]",
    *,
    permissions: "list[str] | None" = None,
    description: "str | None" = None,
):

    def decorator(action_function: FunctionType):

        @wraps(action_function)
        def wrapper(modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet):

            form = (
                form_class(request.POST)
                if "action_form" in request.POST
                else form_class()
            )
            form_class_meta = getattr(form_class, "Meta", None)

            if form.is_valid():
                return action_function(modeladmin, request, queryset)

            app_config = modeladmin.opts.app_config
            model: Model = modeladmin.model

            action = request.POST.getlist("action")[int(request.POST.get("index"))]

            context = {
                "title": modeladmin.get_action(action)[2],
                # For default user tools to work
                "has_permission": True,
                "site_url": site.site_url,
                # For default sidebar to work
                "is_nav_sidebar_enabled": True,
                "available_apps": site.get_app_list(request),
                # Passing default POST values for actions
                "action": action,
                "select_across": request.POST.get("select_across"),
                "index": request.POST.get("index"),
                "selected_action": request.POST.getlist("_selected_action"),
                # For action form
                "app_label": app_config.label,
                "app_verbose_name": app_config.verbose_name,
                "model_name": model._meta.model_name,
                "model_verbose_name_plural": model._meta.verbose_name_plural,
                "help_text": getattr(form_class_meta, "help_text", None),
                "fieldset": Fieldset(form=form, fields=tuple(form.fields.keys())),
            }

            return TemplateResponse(
                request, "admin/django_admin_action_forms/action_form.html", context
            )

        if permissions is not None:
            setattr(wrapper, "allowed_permissions", permissions)

        if description is not None:
            setattr(wrapper, "short_description", description)

        return wrapper

    return decorator
