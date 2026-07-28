from urllib.parse import urlencode
from datetime import timedelta
from django.db.models import Q
import csv
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
from .models import Client, SystemSetting
from .forms import ClientForm
from tasks.models import Task
from labels.models import Category, Label
from contacts.models import ContactLog
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
    my_tasks = Task.objects.filter(
        assigned_user=request.user,
        due_date__lte=today,
        deleted_at__isnull=True
    ).exclude(
        status='done'
    ).select_related('client').order_by('due_date')

    my_recent_contacts = ContactLog.objects.filter(
        user=request.user,
        deleted_at__isnull=True
    ).select_related('client').order_by('-date')[:10]

    context = {
        'today': today,
        'my_tasks': my_tasks,
        'my_recent_contacts': my_recent_contacts,
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

    phase_values = request.GET.getlist('phase')
    if phase_values:
        clients = clients.filter(phase__in=phase_values)

    label_ids = request.GET.getlist('label')
    if label_ids:
        clients = clients.filter(labels__id__in=label_ids).distinct()

    assigned_user_ids = request.GET.getlist('assigned_user')
    if assigned_user_ids:
        clients = clients.filter(assigned_user__id__in=assigned_user_ids)

    contact_date_from = request.GET.get('contact_date_from', '')
    if contact_date_from:
        clients = clients.filter(last_contact_date__date__gte=contact_date_from)

    contact_date_to = request.GET.get('contact_date_to', '')
    if contact_date_to:
        clients = clients.filter(last_contact_date__date__lte=contact_date_to)

    follow_up_threshold = SystemSetting.get_solo().follow_up_threshold_days

    follow_up_only = request.GET.get('follow_up_only', '')
    if follow_up_only:
        cutoff = timezone.now() - timedelta(days=follow_up_threshold)
        clients = clients.filter(
            Q(last_contact_date__isnull=True) | Q(last_contact_date__lt=cutoff)
        )

    SORT_FIELD_MAP = {
        'id': 'id',
        'custom_id': 'custom_id',
        'name': 'name',
        'assigned_user': 'assigned_user__name',
        'phase': 'phase',
        'last_contact_date': 'last_contact_date',
    }
    sort = request.GET.get('sort', 'id')
    sort_key = sort[1:] if sort.startswith('-') else sort
    if sort_key not in SORT_FIELD_MAP:
        sort = 'id'
        sort_key = 'id'
    order_field = SORT_FIELD_MAP[sort_key]
    if sort.startswith('-'):
        order_field = '-' + order_field
    clients = clients.order_by(order_field)

    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_parts = []
    if keyword:
        query_parts.append(('keyword', keyword))
    if contact_date_from:
        query_parts.append(('contact_date_from', contact_date_from))
    if contact_date_to:
        query_parts.append(('contact_date_to', contact_date_to))
    if follow_up_only:
        query_parts.append(('follow_up_only', follow_up_only))
    for p in phase_values:
        query_parts.append(('phase', p))
    for uid in assigned_user_ids:
        query_parts.append(('assigned_user', uid))
    for lid in label_ids:
        query_parts.append(('label', lid))
    base_qs = urlencode(query_parts)

    categories = Category.objects.prefetch_related('labels').all()
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
        'page_obj': page_obj,
        'keyword': keyword,
        'phase_values': phase_values,
        'label_ids': label_ids,
        'assigned_user_ids': assigned_user_ids,
        'contact_date_from': contact_date_from,
        'contact_date_to': contact_date_to,
        'follow_up_only': follow_up_only,
        'sort': sort,
        'base_qs': base_qs,
        'categories': categories,
        'phases': phases,
        'follow_up_threshold': follow_up_threshold,
        'phase_summary': phase_summary,
        'users': User.objects.filter(is_active=True),
    }
    return render(request, 'clients/client_list.html', context)

@login_required
def client_new(request):
    categories = Category.objects.prefetch_related('labels').all()
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/client_form.html', {
        'form': form,
        'title': '取引先新規登録',
        'categories': categories,
        'selected_label_ids': [],
    })

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
    categories = Category.objects.prefetch_related('labels').all()
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/client_form.html', {
        'form': form,
        'title': '取引先編集',
        'categories': categories,
        'selected_label_ids': list(client.labels.values_list('id', flat=True)),
    })

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
    phase_values = request.GET.getlist('phase')
    label_ids = request.GET.getlist('label')

    clients = Client.objects.filter(
        deleted_at__isnull=True
    ).select_related('assigned_user').prefetch_related('labels')

    if phase_values:
        clients = clients.filter(phase__in=phase_values)
    if label_ids:
        clients = clients.filter(labels__id__in=label_ids).distinct()

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