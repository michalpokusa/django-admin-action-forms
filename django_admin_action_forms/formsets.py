from django.forms.formsets import BaseFormSet


class InlineAdminActionFormSet(BaseFormSet): ...


class StackedAdminActionInline(InlineAdminActionFormSet):
    template = "django_admin_action_forms/inlines/stacked.html"


class TabularAdminActionInline(InlineAdminActionFormSet):
    template = "django_admin_action_forms/inlines/tabular.html"
