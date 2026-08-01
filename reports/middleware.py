from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html

from .models import DailyReport


# 日報生成はバックグラウンドスレッドで行われ、生成完了/失敗のタイミングでは
# ユーザーに直接レスポンスを返せない(reports/views.py._generate_report_async参照)。
# そのため「notified=Falseの日報が無いか」を毎リクエストのタイミングでチェックし、
# 次にユーザーが何らかのページを開いた際にDjango messagesで結果を知らせる、という形をとる。
# settings.MIDDLEWAREでは、requestにmessagesを追加できるようMessageMiddlewareより後段に置く必要がある。
class ReportNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # status='pending'(生成中)はまだ結果が出ていないので通知対象から除外する
            pending_reports = DailyReport.objects.filter(
                user=request.user,
                notified=False,
            ).exclude(status="pending")
            for report in pending_reports:
                if report.status == "ready":
                    if report.regenerated:
                        text = f'{report.report_date.strftime("%Y/%m/%d")}の日報を再生成しました（既存の内容を上書きしました）。'
                    else:
                        text = f'{report.report_date.strftime("%Y/%m/%d")}の日報の生成が完了しました。'
                    messages.success(
                        request,
                        format_html(
                            '{} <a href="{}">編集する</a>',
                            text,
                            reverse("report_edit", args=[report.pk]),
                        ),
                    )
                elif report.status == "failed":
                    messages.error(
                        request,
                        f'{report.report_date.strftime("%Y/%m/%d")}の日報の生成に失敗しました。{report.error_message}',
                    )
                # 一度通知したら次回以降は表示しないようフラグを立てる(二重通知防止)
                report.notified = True
                report.save(update_fields=["notified"])

        return self.get_response(request)
