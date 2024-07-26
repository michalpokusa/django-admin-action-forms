from django.urls import path

from .views import ActionFormAutocompleteJsonView


app_name = "django_admin_action_forms"

urlpatterns = [
    path(
        "autocomplete/", ActionFormAutocompleteJsonView.as_view(), name="autocomplete"
    ),
]
