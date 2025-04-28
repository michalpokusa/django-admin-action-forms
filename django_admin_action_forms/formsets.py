from typing import TYPE_CHECKING, Generator, TypedDict, Any

if TYPE_CHECKING:
    from .forms import InlineActionForm

import json

from django import VERSION as DJANGO_VERSION
from django.contrib.admin.utils import flatten_fieldsets
from django.db.models import QuerySet
from django.forms import Media, Widget
from django.forms.formsets import BaseFormSet, DEFAULT_MIN_NUM, DEFAULT_MAX_NUM
from django.forms.renderers import get_default_renderer
from django.http import HttpRequest
from django.template.defaultfilters import capfirst
from django.utils.functional import cached_property
from django.utils.translation import gettext

# Django 4.0.x and above
try:
    from django.forms.utils import RenderableMixin
# Backwards compatibility for Django 3.2.x
except ImportError:
    from django.utils.safestring import mark_safe

    # Polyfill copied from django.forms.utils.RenderableMixin
    class RenderableMixin:
        def get_context(self):
            raise NotImplementedError(
                "Subclasses of RenderableMixin must provide a get_context() method."
            )

        def render(self, template_name=None, context=None, renderer=None):
            renderer = renderer or self.renderer
            template = template_name or self.template_name
            context = context or self.get_context()
            return mark_safe(renderer.render(template, context))

        __str__ = render
        __html__ = render


class InlineFieldDict(TypedDict):
    name: str
    label: str
    widget: Widget
    required: bool
    help_text: str


class InlineAdminActionFormSet(BaseFormSet, RenderableMixin):

    name: str
    form: "type[InlineActionForm]"

    template = None
    extra: int = 1
    min_num: int = DEFAULT_MIN_NUM
    max_num: int = DEFAULT_MAX_NUM
    verbose_name: "str | None" = None
    verbose_name_plural: "str | None" = None
    classes: "list[str] | None" = None
    initial: "list[dict[str, Any]] | None" = None

    empty_form: "InlineActionForm"

    def __init__(
        self,
        modeladmin,
        action: str,
        request: HttpRequest,
        queryset: QuerySet,
        is_bound: bool = False,
    ):
        if not self.name.isidentifier():
            raise ValueError(
                f"{self.__class__.__name__}.name should be a valid Python identifier: '{self.name}'"
            )

        self.modeladmin = modeladmin
        self.action = action
        self.request = request
        self.queryset = queryset

        self.extra = self.get_extra(request)
        self.min_num = self.get_min_num(request)
        self.max_num = self.get_max_num(request)

        init_kwargs = {"prefix": self.name}

        if is_bound:
            init_kwargs["data"] = request.POST
            init_kwargs["files"] = request.FILES

        if self.initial:
            init_kwargs["initial"] = self.initial

        self.renderer = get_default_renderer()
        super().__init__(**init_kwargs)

        self.absolute_max = self.max_num + DEFAULT_MAX_NUM
        self.validate_min = True
        self.validate_max = True
        self.can_order = False
        self.can_delete = False
        self.can_delete_extra = True

        if self.verbose_name is None:
            self.verbose_name = self.get_default_verbose_name()
        if self.verbose_name_plural is None:
            self.verbose_name_plural = f"{self.verbose_name}s"

        self.classes = " ".join(self.classes) if self.classes else ""

    def get_extra(self, request: HttpRequest) -> int:
        return self.extra

    def get_min_num(self, request: HttpRequest) -> int:
        return self.min_num

    def get_max_num(self, request: HttpRequest) -> int:
        return self.max_num

    @classmethod
    def get_default_verbose_name(cls) -> str:
        verbose_name = cls.name.replace("_", " ").lower()
        return verbose_name if not verbose_name.endswith("s") else verbose_name[:-1]

    def __iter__(self) -> "Generator[InlineActionForm, None, None]":
        yield from super().__iter__()
        yield self.empty_form

    def __len__(self):
        return super().__len__() + 1

    def get_form_kwargs(self, index: int) -> "dict[str, Any]":
        return {
            **super().get_form_kwargs(index),
            "formset": self,
            "modeladmin": self.modeladmin,
            "action": self.action,
            "request": self.request,
            "queryset": self.queryset,
        }

    def fields(self) -> "Generator[InlineFieldDict, None, None]":
        for field_name in flatten_fieldsets(
            self.empty_form.opts.get_fieldsets(self.request)
        ):
            form_field = self.empty_form.fields[field_name]
            yield {
                "name": field_name,
                "label": form_field.label or capfirst(field_name.replace("_", " ")),
                "widget": form_field.widget,
                "required": form_field.required,
                "help_text": form_field.help_text,
            }

    @cached_property
    def is_collapsible(self):
        return False if any(self.errors) else "collapse" in self.classes

    @property
    def media(self):
        media = super().media

        media += Media(
            js=(
                "admin/js/vendor/jquery/jquery.js",
                "admin/js/jquery.init.js",
                "admin/js/inlines.js",
            )
        )

        if self.is_collapsible and DJANGO_VERSION < (5, 1):
            media += Media(
                js=(
                    "admin/js/inlines.js",
                    "admin/js/collapse.js",
                )
            )

        return media

    @property
    def template_name(self):
        return self.template

    def get_context(self):
        return {
            "inline_action_formset": self,
            "django_version_above_5_1_x": (5, 1) <= DJANGO_VERSION,
        }

    def inline_formset_data(self):
        return json.dumps(
            {
                "name": f"#{self.prefix}",
                "options": {
                    "prefix": self.prefix,
                    "addText": gettext("Add another %(verbose_name)s")
                    % {
                        "verbose_name": capfirst(self.verbose_name),
                    },
                    "deleteText": gettext("Remove"),
                },
            }
        )

    # Polyfill for Django 3.2.x, because then BaseFormSet had it's own __str__ method
    __str__ = RenderableMixin.render
    __html__ = RenderableMixin.render


class StackedAdminActionInline(InlineAdminActionFormSet):
    template = "django_admin_action_forms/inlines/stacked.html"


class TabularAdminActionInline(InlineAdminActionFormSet):
    template = "django_admin_action_forms/inlines/tabular.html"
