from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from .models import ContactLog
from .forms import ContactLogForm
from clients.models import Client
from tasks.models import Task
from accounts.models import User


def can_edit(user):
    return user.role in ['admin', 'manager']


@login_required
def contact_list(request):
    logs = ContactLog.objects.filter(
        deleted_at__isnull=True
    ).select_related('client', 'user').order_by('-date')

    # フィルタ
    keyword = request.GET.get('keyword', '')
    client_id = request.GET.get('client', '')
    if client_id and not keyword:
        client_obj = Client.objects.filter(id=client_id).first()
        if client_obj:
            keyword = client_obj.name

    if keyword:
        logs = logs.filter(client__name__icontains=keyword)

    if client_id:
        logs = logs.filter(client__id=client_id)

    method = request.GET.get('method', '')
    if method:
        logs = logs.filter(method=method)

    date_from = request.GET.get('date_from', '')
    if date_from:
        logs = logs.filter(date__date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        logs = logs.filter(date__date__lte=date_to)

    assigned_user_id = request.GET.get('assigned_user', '')
    if assigned_user_id:
        logs = logs.filter(user__id=assigned_user_id)

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'keyword': keyword,
        'client_id': client_id,
        'method': method,
        'date_from': date_from,
        'date_to': date_to,
        'assigned_user_id': assigned_user_id,
        'method_choices': ContactLog.METHOD_CHOICES,
        'users': User.objects.filter(is_active=True),
    }
    return render(request, 'contacts/contact_list.html', context)


@login_required
def contact_new(request):
    # 取引先詳細画面からのリンクの場合、client を初期値にセット
    initial = {}
    client_id = request.GET.get('client')
    if client_id:
        initial['client'] = client_id

    if request.method == 'POST':
        form = ContactLogForm(request.POST, request=request)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()

            # last_contact_dateを更新
            client = log.client
            latest = client.contact_logs.filter(
                deleted_at__isnull=True
            ).order_by('-date').first()
            if latest:
                client.last_contact_date = latest.date
                client.save()

            # タスク同時作成
            if form.cleaned_data.get('create_task'):
                task_title = form.cleaned_data.get('task_title')
                if task_title:
                    Task.objects.create(
                        client=log.client,
                        contact_log=log,
                        title=task_title,
                        due_date=form.cleaned_data.get('task_due_date'),
                        assigned_user=form.cleaned_data.get('task_assigned_user'),
                        status='pending',
                    )

            messages.success(request, '接触記録を登録しました。')
            return redirect('client_detail', pk=log.client.pk)
    else:
        form = ContactLogForm(initial=initial, request=request)

    return render(request, 'contacts/contact_form.html', {'form': form, 'title': '接触記録入力'})


@login_required
def contact_detail(request, pk):
    log = get_object_or_404(ContactLog, pk=pk, deleted_at__isnull=True)
    return render(request, 'contacts/contact_detail.html', {
        'log': log,
        'can_edit': can_edit(request.user),
    })


@login_required
def contact_edit(request, pk):
    if not can_edit(request.user):
        messages.error(request, '編集権限がありません。')
        return redirect('contact_detail', pk=pk)

    log = get_object_or_404(ContactLog, pk=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        form = ContactLogForm(request.POST, instance=log)
        if form.is_valid():
            log = form.save()

            # last_contact_dateを更新
            client = log.client
            latest = client.contact_logs.filter(
                deleted_at__isnull=True
            ).order_by('-date').first()
            if latest:
                client.last_contact_date = latest.date
                client.save()

            messages.success(request, '接触記録を更新しました。')
            return redirect('contact_detail', pk=pk)
    else:
        form = ContactLogForm(instance=log)

    return render(request, 'contacts/contact_form.html', {'form': form, 'title': '接触記録編集'})


@login_required
def contact_delete(request, pk):
    if not can_edit(request.user):
        messages.error(request, '削除権限がありません。')
        return redirect('contact_detail', pk=pk)

    log = get_object_or_404(ContactLog, pk=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        log.deleted_at = timezone.now()
        log.save()

        # last_contact_dateを更新
        client = log.client
        latest = client.contact_logs.filter(
            deleted_at__isnull=True
        ).order_by('-date').first()
        client.last_contact_date = latest.date if latest else None
        client.save()

        messages.success(request, '接触記録を削除しました。')
        return redirect('client_detail', pk=client.pk)

    return render(request, 'contacts/contact_confirm_delete.html', {'log': log})