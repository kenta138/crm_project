from django import template
from django.utils import timezone

register = template.Library()

# datetime.weekday()は月曜=0始まりなので、そのままインデックスとして使える
WEEKDAY_KANJI = ["月", "火", "水", "木", "金", "土", "日"]


@register.filter
def jpdate(value):
    """日付のみを「YYYY/MM/DD(曜)」形式で表示する(例: 2026/08/01(土))。
    date/datetimeどちらの値にも使えるが、時刻は含めない。"""
    if not value:
        return ""
    weekday = WEEKDAY_KANJI[value.weekday()]
    return f"{value.strftime('%Y/%m/%d')}({weekday})"


@register.filter
def jpdatetime(value):
    """日時を「YYYY/MM/DD(曜) HH:MM」形式で表示する。
    settings.USE_TZ=Trueのため、DBにはUTCで保存されている値をそのままstrftimeすると
    日本時間からずれてしまう。そのためtimezone.localtime()でAsia/Tokyoへ変換してから整形する。"""
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    weekday = WEEKDAY_KANJI[value.weekday()]
    return f"{value.strftime('%Y/%m/%d')}({weekday}) {value.strftime('%H:%M')}"
