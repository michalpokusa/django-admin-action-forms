
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

3. Include `'django_admin_action_forms.urls'` in your `urls.py` file. This is needed only if you want to use autocomplete.

    If you are want to include them under same path as admin site, make sure to place them **before** the admin urls.

    ```python
    from django.contrib import admin
    from django.urls import path, include


    urlpatterns = [
        path("admin/action-forms/", include("django_admin_action_forms.urls")),
        path("admin/", admin.site.urls),
        ...
    ]
    ```
    ...or include them under any other path.

    ```python
    from django.contrib import admin
    from django.urls import path, include


    urlpatterns = [
        path("admin/", admin.site.urls),
        ...
        path("any/other/path/", include("django_admin_action_forms.urls")),
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

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/actions/#the-action-decorator">
    <code>@admin.action</code>
</a>

Decorator that can be used instead of `@admin.action` to create action with custom form.
Functions decorated with `@action_with_form` should accept additional argument `data` that will contain cleaned data from the form, `permissions` and `description` work the same.

```python
@action_with_form(
    CustomActionForm,
    description="Description of the action",
)
def custom_action(self, request, queryset, data):
    ...
```

### ActionForm

Base class for creating action forms responsible for all under the hood logic. Nearly always you will want to subclass `AdminActionForm` instead of `ActionForm`, as it provides additional features.

### AdminActionForm

In addition to `ActionForm`, it replaces default text inputs for `DateField`, `TimeField`, `SplitDateTimeField` with respective admin widgets.

Most of the time this is a class you want to subclass when creating custom action forms.

```python
class CustomActionForm(AdminActionForm):

    field1 = forms.ChoiceField(
        label="Field 1",
        choices=[(1, "Option 1"), (2, "Option 2"), (3, "Option 3")],
    )
    field2 = forms.CharField(
        label="Field 2",
        required=False,
        widget=forms.TextInput
    )
    field3 = forms.DateField(label="Field 3", initial="2024-07-15")

    ...
```


### ActionForm.Meta

> Works similar to some <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#modeladmin-options">
    <code>ModelAdmin</code> options
</a>

Additional configuration for action forms. It can be use to customize the layout of the form, add help text or display a list of objects that will be affected by the action.

```python
class CustomActionForm(AdminActionForm):

    ...

    class Meta:
        list_objects = True
        help_text = "This is a help text"
        ...
```

Below you can find all available options:

#### list_objects

Default: `False`

If `True`, the intermediate page will display a list of objects that will be affected by the action similarly
to the intermediate page for built-in `delete_selected` action.

```python
list_objects = True
```

#### help_text

Default: `None`

Text displayed between the form and the list of objects or form in the intermediate page.

```python
help_text = "This text will be displayed between the form and the list of objects"
```

#### fields

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fields">
    <code>ModelAdmin.fields</code>
</a>

Specifies the fields that should be displayed in the form. If `fieldsets` is provided, `fields` will be ignored.


```python
fields = ["field1", ("field2", "field3")]
```

#### get_fields(request)

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_fields">
    <code>ModelAdmin.get_fields()</code>
</a>

Method that can be used to dynamically determine fields that should be displayed in the form. Can be used to reorder, group or exclude fields based on the `request`. Should return a list of fields, as described above in the [`fields`](#fields).

```python
def get_fields(self, request):
    if request.user.is_superuser:
        return ["field1", "field2", "field3"]
    else:
        return ["field1", "field2"]
```


#### fieldsets

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets">
    <code>ModelAdmin.fieldsets</code>
</a>

If both `fields` and `fieldsets` are provided, `fieldsets` will be used.

```python
fieldsets = [
    (
        None,
        {
            "fields": ["field1", "field2", ("field3", "field4")],
        },
    ),
    (
        "Fieldset 2",
        {
            "classes": ["collapse"],
            "fields": ["field5", ("field6", "field7")],
            "description": "This is a description for fieldset 2",
        },
    ),
]
```

#### get_fieldsets(request)

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_fieldsets">
    <code>ModelAdmin.get_fieldsets()</code>
</a>

Method that can be used to dynamically determine fieldsets that should be displayed in the form. Can be used to reorder, group or exclude fields based on the `request`. Should return a list of fieldsets, as described above in the [`fieldsets`](#fieldsets).

```python
def get_fieldsets(self, request):
    if request.user.is_superuser:
        return [
            (
                None,
                {
                    "fields": ["field1", "field2", ("field3", "field4")],
                },
            ),
            (
                "Fieldset 2",
                {
                    "classes": ["collapse"],
                    "fields": ["field5", ("field6", "field7")],
                    "description": "This is a description for fieldset 2",
                },
            ),
        ]
    else:
        return [
            (
                None,
                {
                    "fields": ["field1", "field2", ("field3", "field4")],
                },
            ),
        ]
```

#### filter_horizontal

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_horizontal">
    <code>ModelAdmin.filter_horizontal</code>
</a>

Default: `None`

Sets fields that should use horizontal filter widget. It should be a list of field names.

```python
filter_horizontal = ["field1", "field2"]
```

#### filter_vertical

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_vertical">
    <code>ModelAdmin.filter_vertical</code>
</a>

Default: `None`

Sets fields that should use vertical filter widget. It should be a list of field names.

```python
filter_vertical = ["field1", "field2"]
```

#### autocomplete_fields

> Works similar to <a href="https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.autocomplete_fields">
    <code>ModelAdmin.autocomplete_fields</code>
</a>

Default: `None`


Sets fields that should use autocomplete widget. It should be a list of field names.

```python
autocomplete_fields = ["field1", "field2"]
```
