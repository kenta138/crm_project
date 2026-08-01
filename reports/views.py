import threading
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from google import genai

from contacts.models import ContactLog
from clients.models import SystemSetting
from .forms import DailyReportForm
from .models import DailyReport


def can_view_all(user):
    return user.role in ['admin', 'manager']


def _build_prompt(user, report_date, contact_logs):
    lines = [
        f'- {log.client.name}様（{log.get_method_display()}）: {log.title}\n  {log.content}'
        for log in contact_logs
    ]
    logs_text = '\n'.join(lines)

    template = SystemSetting.get_solo().report_prompt_template
    return template.format(
        user_name=user.name,
        date=report_date.strftime('%Y年%m月%d日'),
        logs_text=logs_text,
    )

@login_required
def report_list(request):
    reports = DailyReport.objects.select_related('user')
    if not can_view_all(request.user):
        reports = reports.filter(user=request.user)
    reports = reports.order_by('-report_date')

    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/report_list.html', {'page_obj': page_obj})


def _generate_report_async(user_id, report_date, was_existing):
    contact_logs = ContactLog.objects.filter(
        user_id=user_id,
        date__date=report_date,
        deleted_at__isnull=True
    ).select_related('client').order_by('date')

    if not contact_logs.exists():
        DailyReport.objects.update_or_create(
            user_id=user_id,
            report_date=report_date,
            defaults={
                'status': 'failed',
                'error_message': f'{report_date.strftime("%Y/%m/%d")}の接触記録が見つかりません。',
                'notified': False,
            },
        )
        return

    user = contact_logs.first().user
    prompt = _build_prompt(user, report_date, contact_logs)

    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
        )
        DailyReport.objects.update_or_create(
            user_id=user_id,
            report_date=report_date,
            defaults={
                'content': response.text,
                'status': 'ready',
                'error_message': '',
                'notified': False,
                'regenerated': was_existing,
            },
        )
    except Exception as e:
        DailyReport.objects.update_or_create(
            user_id=user_id,
            report_date=report_date,
            defaults={
                'status': 'failed',
                'error_message': str(e),
                'notified': False,
            },
        )


@login_required
def report_generate(request):
    if request.method == 'POST':
        date_str = request.POST.get('report_date')
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            report_date = timezone.localdate()

        was_existing = DailyReport.objects.filter(
            user=request.user, report_date=report_date, status='ready'
        ).exists()

        DailyReport.objects.update_or_create(
            user=request.user,
            report_date=report_date,
            defaults={'status': 'pending', 'error_message': '', 'notified': True},
        )

        thread = threading.Thread(
            target=_generate_report_async,
            args=(request.user.id, report_date, was_existing),
            daemon=True,
        )
        thread.start()

        messages.success(request, f'{report_date.strftime("%Y/%m/%d")}の日報生成を開始しました。完了次第お知らせします。')
        return redirect('dashboard')

    return redirect('dashboard')

@login_required
def report_detail(request, pk):
    report = get_object_or_404(DailyReport, pk=pk)
    if report.user != request.user and not can_view_all(request.user):
        messages.error(request, 'この日報を閲覧する権限がありません。')
        return redirect('report_list')
    if report.status != 'ready':
        messages.error(request, 'この日報はまだ準備できていません。')
        return redirect('report_list')
    return render(request, 'reports/report_detail.html', {'report': report})

@login_required
def report_edit(request, pk):
    report = get_object_or_404(DailyReport, pk=pk)
    if report.user != request.user:
        messages.error(request, 'この日報を編集する権限がありません。')
        return redirect('report_detail', pk=pk)
    if report.status != 'ready':
        messages.error(request, 'この日報はまだ準備できていません。')
        return redirect('report_list')

    if request.method == 'POST':
        form = DailyReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, '日報を更新しました。')
            return redirect('report_detail', pk=pk)
    else:
        form = DailyReportForm(instance=report)

    return render(request, 'reports/report_form.html', {
        'form': form,
        'report_date': report.report_date,
        'title': '日報編集',
        'form_action': reverse('report_edit', args=[pk]),
    })