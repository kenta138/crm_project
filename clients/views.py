import csv
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
from .models import Client
from .forms import ClientForm
from tasks.models import Task
from labels.models import Label
from accounts.models import User


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'この操作はAdminのみ可能です。')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['admin', 'manager']:
            messages.error(request, 'この操作はAdmin・Managerのみ可能です。')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def dashboard(request):
    today = timezone.localdate()
    today_tasks = Task.objects.filter(
        due_date=today,
        deleted_at__isnull=True
    ).exclude(
        status='done'
    ).select_related('client', 'assigned_user')

    phases = Client.PHASE_CHOICES
    phase_summary = []
    for phase_value, phase_label in phases:
        count = Client.objects.filter(
            phase=phase_value,
            deleted_at__isnull=True
        ).count()
        phase_summary.append({
            'value': phase_value,
            'label': phase_label,
            'count': count,
        })

    context = {
        'today_tasks': today_tasks,
        'phase_summary': phase_summary,
    }
    return render(request, 'clients/dashboard.html', context)


@login_required
def client_list(request):
    clients = Client.objects.filter(
        deleted_at__isnull=True
    ).select_related('assigned_user').prefetch_related('labels')

    keyword = request.GET.get('keyword', '')
    if keyword:
        clients = clients.filter(name__icontains=keyword)

    phase = request.GET.get('phase', '')
    if phase:
        clients = clients.filter(phase=phase)

    label_id = request.GET.get('label', '')
    if label_id:
        clients = clients.filter(labels__id=label_id)

    clients = clients.order_by('-last_contact_date')

    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    labels = Label.objects.filter(is_active=True)
    phases = Client.PHASE_CHOICES

    context = {
        'page_obj': page_obj,
        'keyword': keyword,
        'phase': phase,
        'label_id': label_id,
        'labels': labels,
        'phases': phases,
    }
    return render(request, 'clients/client_list.html', context)


@login_required
def client_new(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/client_form.html', {'form': form, 'title': '取引先新規登録'})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk, deleted_at__isnull=True)

    contact_logs = client.contact_logs.filter(
        deleted_at__isnull=True
    ).select_related('user').order_by('-date')[:10]

    tasks = client.tasks.filter(
        deleted_at__isnull=True
    ).select_related('assigned_user')

    task_status = request.GET.get('task_status', '')
    if task_status:
        tasks = tasks.filter(status=task_status)

    tasks = tasks.order_by('due_date')

    context = {
        'client': client,
        'contact_logs': contact_logs,
        'tasks': tasks,
        'task_status': task_status,
        'task_status_choices': Task.STATUS_CHOICES,
        'can_edit': request.user.role in ['admin', 'manager'],
        'can_delete': request.user.role == 'admin',
    }
    return render(request, 'clients/client_detail.html', context)


@login_required
@manager_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/client_form.html', {'form': form, 'title': '取引先編集'})


@login_required
@admin_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        client.deleted_at = timezone.now()
        client.save()
        return redirect('client_list')
    return render(request, 'clients/client_confirm_delete.html', {'client': client})


@login_required
@admin_required
def client_import(request):
    errors = []
    success_count = 0

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))

        valid_phases = dict(Client.PHASE_CHOICES)
        phase_map = {v: k for k, v in valid_phases.items()}

        clients_to_create = []
        for row_num, row in enumerate(reader, start=2):
            row_errors = []

            name = row.get('会社名', '').strip()
            if not name:
                row_errors.append('会社名は必須です')

            phase_label = row.get('フェーズ', '').strip()
            phase = phase_map.get(phase_label, 'new')

            email = row.get('メールアドレス', '').strip()
            phone = row.get('電話番号', '').strip()
            memo = row.get('メモ', '').strip()

            assigned_user = None
            user_email = row.get('担当者メールアドレス', '').strip()
            if user_email:
                try:
                    assigned_user = User.objects.get(email=user_email)
                except User.DoesNotExist:
                    row_errors.append(f'担当者メールアドレス「{user_email}」のユーザーが見つかりません')

            if row_errors:
                for err in row_errors:
                    errors.append(f'{row_num}行目：{err}')
                continue

            if Client.objects.filter(name=name, deleted_at__isnull=True).exists():
                errors.append(f'{row_num}行目：「{name}」はすでに登録されています（スキップ）')
                continue

            clients_to_create.append(Client(
                name=name,
                phase=phase,
                phone=phone,
                email=email,
                memo=memo,
                assigned_user=assigned_user,
            ))

        if clients_to_create:
            Client.objects.bulk_create(clients_to_create)
            success_count = len(clients_to_create)

    context = {
        'errors': errors,
        'success_count': success_count,
    }
    return render(request, 'clients/client_import.html', context)


@login_required
@admin_required
def client_export(request):
    phase = request.GET.get('phase', '')
    label_id = request.GET.get('label', '')

    clients = Client.objects.filter(
        deleted_at__isnull=True
    ).select_related('assigned_user').prefetch_related('labels')

    if phase:
        clients = clients.filter(phase=phase)
    if label_id:
        clients = clients.filter(labels__id=label_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="clients.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['会社名', 'フェーズ', '担当者メールアドレス', '電話番号', 'メールアドレス', 'メモ', '最終接触日'])

    for client in clients:
        writer.writerow([
            client.name,
            client.get_phase_display(),
            client.assigned_user.email if client.assigned_user else '',
            client.phone,
            client.email,
            client.memo,
            client.last_contact_date.strftime('%Y/%m/%d %H:%M') if client.last_contact_date else '',
        ])

    return response


@login_required
@admin_required
def client_import_template(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="clients_template.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['会社名', 'フェーズ', '担当者メールアドレス', '電話番号', 'メールアドレス', 'メモ'])
    writer.writerow(['株式会社サンプル', '新規', 'user@example.com', '03-0000-0000', 'info@sample.com', 'サンプルメモ'])

    return response