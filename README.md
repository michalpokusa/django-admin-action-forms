
# django-admin-action-forms

<p float="left">
    <a href="https://pypi.org/project/django-admin-action-forms/">
        <img src="https://img.shields.io/pypi/v/django-admin-action-forms?color=0073b7"/>
    </a>
    <a href="https://www.djangoproject.com/">
        <img src="https://img.shields.io/badge/3.2.x, 4.x.x, 5.x.x-a?style=flat&logo=django&label=django&labelColor=0c4b33&color=616161">
    </a>
</p>

Extension for the Django admin panel that allows passing additional parameters to actions by creating intermediate pages with forms.


- [🚀 Overview](#-overview)
- [🎉 Features](#-features)
- [🔌 Instalation](#-instalation)
- [✏️ Example](#️-example)
- [📄 Documentation](#-documentation)

##  🚀 Overview

Do you need confirmation pages for your actions in Django admin?<br>
Does creating multiple actions in Django admin that only differ in arguments sound familiar?<br>
Have you ever added a somewhat hacky way to pass additional parameters to an action?

**If so, this package is for you!**

This is how it looks in action:

<img src="https://raw.githubusercontent.com/michalpokusa/django-admin-action-forms/main/resources/overview.gif" width="100%" alt="GIF showing usage of django-admin-action-forms"></img>

By adding a few lines of code, you can create actions with custom forms that will be displayed in an intermediate page before the action is executed. Data from the form will be passed to the action as an additional argument.

Simple and powerful!


### 🎉 Features

- Requires minimal configuration, easy to use
- Supports all modern Django versions (3.2.x, 4.x.x, 5.x.x)
- Built on top of Django's templates and forms, matches the Django admin style
- Supports `fields`/`fieldsets`, `filter_horizontal`/`filter_vertical` and `autocomplete_fields`
- Works with custom widgets

## 🔌 Instalation

1. Install using ``pip``:

```bash
$ pip3 install django-admin-action-forms
```


2. Add `'django_admin_action_forms'` to your `INSTALLED_APPS` setting.
```python
INSTALLED_APPS = [
    ...
    'django_admin_action_forms',
]
```

1. Include `'django_admin_action_forms.urls'` in your `urls.py` file.

    **Required** if you want to use `autocomplete_fields` in your actions' forms.


```python
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin-action-forms/", include("django_admin_action_forms.urls")),
    path("admin/", admin.site.urls),
    ...
]
```

## ✏️ Example

Below you can see an example of how to create an action with a custom form.

If needed, you can:
- display list of objects that will be affected by using `list_objects`,
- add short description with `help_text`,
- use custom widgets by specifying them for each field,
- reorder or group fields with `fields` and `fieldsets`,
- use autocomplete for `Model`s or simple choices by using `autocomplete_fields`.

```python
# admin.py

from django.http import HttpRequest
from django import forms
from django.contrib import admin
from django.db.models import QuerySet

from django_admin_action_forms import action_with_form
from django_admin_action_forms.forms import AdminActionForm

from .models import Order


class GenerateReportActionForm(AdminActionForm):
    output_format = forms.ChoiceField(
        label="Output format", choices=[(1, ".csv"), (2, ".pdf"), (3, ".json")]
    )
    from_date = forms.DateField(label="From date", initial="2024-07-15")
    to_date = forms.DateField(label="To date", initial="2024-07-22")
    max_orders_per_page = forms.IntegerField(
        label="Max orders per page",
        help_text="Only used when output format is PDF",
        required=False,
    )
    comment = forms.CharField(label="Comment", required=False)

    class Meta:
        help_text = "This action will generate a sales report for selected orders and download it in the selected format."

        fieldsets = [
            (
                None,
                {"fields": ["output_format"]}
            ),
            (
                "Date range",
                {"fields": ["from_date", "to_date"]}
            ),
            (
                "Other",
                {"fields": ["max_orders_per_page", "comment"], "classes": ["collapse"]}
            ),
        ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    @action_with_form(
        GenerateReportActionForm,
        description="Generate sales report for selected orders",
    )
    def generate_report(self, request: HttpRequest, queryset: QuerySet, data: dict):
        output_format = data["output_format"]
        ...

    actions = [
        generate_report,
        ...
    ]
```

## 📄 Documentation

#### <code>@action_with_form(<i>form_class, *, permissions=None, description=None</i>)</code>

Decorator that can be used instead of `@admin.action` to create action with custom form.
Functions decorated with `@action_with_form` should accept additional argument `data` that will contain cleaned data from the form.

### ActionForm

Base class for creating action forms, it replaces field widgets

Nearly always you will want to subclass `AdminActionForm` instead of `ActionForm`, as it provides additional features.

### AdminActionForm

In addition to `ActionForm`, it replaces default text inputs for `DateField`, `TimeField`, `SplitDateTimeField` with respective admin widgets.

Most of the this is a class you want to subclass when creating action forms.

### ActionForm.Meta

Additional configuration for action forms. It works similarly to some `ModelAdmin` options.

#### list_objects

Default: `False`

If `True`, the intermediate page will display a list of objects that will be affected by the action similarly
to the intermediate page for built-in `delete_selected` action.

#### help_text

Default: `None`

Text displayed between the form and the list of objects or form in the intermediate page.

#### fields

Works similar to
<a href="https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fields">
    <code>ModelAdmin.fields</code>
</a>.

Specifies the fields that should be displayed in the form. If `fieldsets` is provided, `fields` will be ignored.

#### fieldsets

Works similar to
<a href="https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets">
    <code>ModelAdmin.fieldsets</code>
</a>
If both `fields` and `fieldsets` are provided, `fieldsets` will be used.

#### filter_horizontal

Default: `None`

Similar to
<a href="https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_horizontal">
    <code>ModelAdmin.filter_horizontal</code>
</a>.
Sets fields that should use horizontal filter widget. It should be a list of field names.

#### filter_vertical

Default: `None`

Similar to
<a href="https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_vertical">
    <code>ModelAdmin.filter_vertical</code>
</a>.
Sets fields that should use vertical filter widget. It should be a list of field names.

#### autocomplete_fields

> In order for autocomplete to you have to include `'django_admin_action_forms.urls'` in your `urls.py` file.

Default: `None`

Similar to
<a href="https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.autocomplete_fields">
    <code>ModelAdmin.autocomplete_fields</code>
</a>.
Sets fields that should use autocomplete widget. It should be a list of field names.
