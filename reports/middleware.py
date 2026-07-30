from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html
from .models import DailyReport

class ReportNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            pending_reports = DailyReport.objects.filter(
                user=request.user,
                notified=False,
            ).exclude(status='pending')
            for report in pending_reports:
                if report.status == 'ready':
                    messages.success(
                        request,
                        format_html(
                            '{}の日報の生成が完了しました。<a href="{}">編集する</a>',
                            report.report_date.strftime("%Y/%m/%d"),
                            reverse('report_edit', args=[report.pk])
                        )
                    )
                elif report.status == 'failed':
                    messages.error(
                        request,
                        f'{report.report_date.strftime("%Y/%m/%d")}の日報の生成に失敗しました。{report.error_message}'
                    )
                report.notified = True
                report.save(update_fields=['notified'])

        return self.get_response(request)