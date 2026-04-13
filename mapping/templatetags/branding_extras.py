from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@register.simple_tag
def static_asset_exists(asset_path: str) -> bool:
    """Return True when the given static asset can be found by staticfiles finders."""
    return finders.find(asset_path) is not None
