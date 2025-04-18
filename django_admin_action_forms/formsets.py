from django.forms.formsets import BaseFormSet


class AdminActionInlineFormSet(BaseFormSet): ...


class StackedAdminActionInline(AdminActionInlineFormSet):
    template = "django_admin_action_forms/inlines/stacked.html"


class TabularAdminActionInline(AdminActionInlineFormSet):
    template = "django_admin_action_forms/inlines/tabular.html"
