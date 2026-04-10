from django import template
from django.contrib.sites.shortcuts import get_current_site

from allauth.socialaccount.models import SocialApp

register = template.Library()


@register.simple_tag(takes_context=True)
def google_social_login_enabled(context):
    request = context.get("request")
    if request is None:
        return False

    current_site = get_current_site(request)
    return SocialApp.objects.filter(provider="google", sites=current_site).exists()
