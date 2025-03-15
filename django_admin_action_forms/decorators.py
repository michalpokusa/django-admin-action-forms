from collections.abc import Callable
from functools import wraps

from django.apps import AppConfig
from django.contrib.admin import AdminSite, ModelAdmin
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from .forms import ActionForm


def action_with_form(
    form_class: "type[ActionForm]",
    *,
    permissions: "list[str] | None" = None,
    description: "str | None" = None,
):
    """
    Decorator used to create an action with a form, alternative to the default ``@admin.action`` decorator.
    """

    def decorator(action_function: Callable[..., None | HttpResponse]):

        @wraps(action_function)
        def wrapper(*args):

            # Compatibility with django-no-queryset-admin-actions
            modeladmin: ModelAdmin = args[0]
            request: HttpRequest = args[1]
            queryset: QuerySet = next(
                (arg for arg in args if isinstance(arg, QuerySet)),
                modeladmin.model.objects.none(),
            )
            rest = args[2:]

            form = (
                form_class(modeladmin, request, queryset)
                if "action_form" not in request.POST
                else form_class(
                    modeladmin,
                    request,
                    queryset,
                    data=request.POST,
                    files=request.FILES,
                )
            )

            if form.is_valid():
                return action_function(modeladmin, request, *rest, form.cleaned_data)

            admin_site: AdminSite = modeladmin.admin_site
            app_config: AppConfig = modeladmin.opts.app_config
            model: Model = modeladmin.model

            try:
                action_index = int(request.POST.get("index", 0))
            except ValueError:
                action_index = 0

            action = request.POST.getlist("action")[action_index]

            context = {
                **admin_site.each_context(request),
                "title": modeladmin.get_actions(request).get(action)[2],
                "subtitle": None,
                "app_label": app_config.label,
                "app_verbose_name": app_config.verbose_name,
                "model_name": model._meta.model_name,
                "model_verbose_name": model._meta.verbose_name,
                "model_verbose_name_plural": model._meta.verbose_name_plural,
                "help_text": getattr(form.Meta, "help_text", None),
                "list_objects": getattr(form.Meta, "list_objects", False),
                "queryset": queryset,
                "form": form,
                "fieldsets": form.fieldsets,
                "action": action,
                "select_across": request.POST.get("select_across"),
                "selected_action": request.POST.getlist("_selected_action"),
                "confirm_button_text": getattr(form.Meta, "confirm_button_text", None),
                "cancel_button_text": getattr(form.Meta, "cancel_button_text", None),
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
