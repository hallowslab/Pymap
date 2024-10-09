from django import template
from django.contrib.auth.models import User, AnonymousUser

register = template.Library()


@register.simple_tag
def get_username(user: (User | AnonymousUser)) -> str:
    if user.is_authenticated:
        return user.username[:10]
    return "Guest"
