from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import Widget
from django.utils.html import format_html


class RenderInsideDivMixin(Widget):
    """
    Renders the original widget inside a div element.

    Simulates `RelatedFieldWidgetWrapper`, as Select2 expects a parent div element.
    """

    def render(self, *args, **kwargs):
        rendered_widget = super().render(*args, **kwargs)

        return format_html(f"<div>{rendered_widget}</div>")


class FilterHorizontalWidget(RenderInsideDivMixin, FilteredSelectMultiple): ...


class FilterVerticalWidget(RenderInsideDivMixin, FilteredSelectMultiple): ...


