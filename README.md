
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

3. (Optional) Include `'django_admin_action_forms.urls'` in your `urls.py` file.
They are **only required if you want to use** `autocomplete_fields` in your actions' forms.


```python
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin-action-forms/", include("django_admin_action_forms.urls")),
    path("admin/", admin.site.urls),
    ...
]
```
