from collections.abc import Callable
from functools import wraps

from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

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

    def decorator(action_function: "Callable[..., None | HttpResponse]"):

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
                if request.POST.get("submitted_from_changelist_view", "0") == "1"
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

            return form.action_form_view(request)

        setattr(wrapper, "form_class", form_class)

        if permissions is not None:
            setattr(wrapper, "allowed_permissions", permissions)

        if description is not None:
            setattr(wrapper, "short_description", description)

        return wrapper

    return decorator
