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

    return f"""以下は{user.name}さんの{report_date.strftime('%Y年%m月%d日')}の接触記録です。
これをもとに、簡潔な日本語のビジネス日報を作成してください。

# 接触記録
{logs_text}

# 出力フォーマット
- 本日の活動概要
- 対応した取引先一覧
- 所感・課題
"""


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


@login_required
def report_generate(request):
    if request.method == 'POST':
        date_str = request.POST.get('report_date')
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            report_date = timezone.localdate()

        contact_logs = ContactLog.objects.filter(
            user=request.user,
            date__date=report_date,
            deleted_at__isnull=True
        ).select_related('client').order_by('date')

        if not contact_logs.exists():
            messages.error(request, f'{report_date.strftime("%Y/%m/%d")}の接触記録が見つかりません。')
            return render(request, 'reports/report_generate.html', {'today': timezone.localdate()})

        prompt = _build_prompt(request.user, report_date, contact_logs)

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
        )
        generated_content = response.text

        form = DailyReportForm(initial={'content': generated_content})
        already_exists = DailyReport.objects.filter(user=request.user, report_date=report_date).exists()

        return render(request, 'reports/report_form.html', {
            'form': form,
            'report_date': report_date,
            'title': '日報プレビュー・編集',
            'form_action': reverse('report_save'),
            'already_exists': already_exists,
        })
    
    return render(request, 'reports/report_generate.html', {'today': timezone.localdate()})


@login_required
def report_save(request):
    if request.method != 'POST':
        return redirect('report_generate')

    report_date = datetime.strptime(request.POST.get('report_date'), '%Y-%m-%d').date()
    form = DailyReportForm(request.POST)
    if form.is_valid():
        report, _ = DailyReport.objects.update_or_create(
            user=request.user,
            report_date=report_date,
            defaults={'content': form.cleaned_data['content']},
        )
        messages.success(request, '日報を保存しました。')
        return redirect('report_detail', pk=report.pk)

    return render(request, 'reports/report_form.html', {
        'form': form,
        'report_date': report_date,
        'title': '日報プレビュー・編集',
        'form_action': reverse('report_save'),
    })


@login_required
def report_detail(request, pk):
    report = get_object_or_404(DailyReport, pk=pk)
    if report.user != request.user and not can_view_all(request.user):
        messages.error(request, 'この日報を閲覧する権限がありません。')
        return redirect('report_list')
    return render(request, 'reports/report_detail.html', {'report': report})


@login_required
def report_edit(request, pk):
    report = get_object_or_404(DailyReport, pk=pk)
    if report.user != request.user:
        messages.error(request, 'この日報を編集する権限がありません。')
        return redirect('report_detail', pk=pk)

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