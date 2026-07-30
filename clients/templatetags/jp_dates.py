from django import template
from django.utils import timezone

register = template.Library()

WEEKDAY_KANJI = ['月', '火', '水', '木', '金', '土', '日']


@register.filter
def jpdate(value):
    if not value:
        return ''
    weekday = WEEKDAY_KANJI[value.weekday()]
    return f"{value.strftime('%Y/%m/%d')}({weekday})"


@register.filter
def jpdatetime(value):
    if not value:
        return ''
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    weekday = WEEKDAY_KANJI[value.weekday()]
    return f"{value.strftime('%Y/%m/%d')}({weekday}) {value.strftime('%H:%M')}"