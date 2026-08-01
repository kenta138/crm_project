from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clients.models import Client
from tasks.models import Task

from .forms import ContactLogForm
from .models import ContactLog


def can_edit(user):
    """接触記録の編集・削除が許可されるロールかどうかを判定する。"""
    return user.role in ["admin", "manager"]


@login_required
def contact_list(request):
    """接触記録一覧。取引先詳細画面から遷移した場合はclientパラメータで絞り込み、
    その取引先名がキーワード欄に自動セットされる。"""
    logs = (
        ContactLog.objects.filter(deleted_at__isnull=True)
        .select_related("client", "user")
        .order_by("-date")
    )

    # フィルタ
    keyword = request.GET.get("keyword", "")
    client_id = request.GET.get("client", "")
    if client_id and not keyword:
        client_obj = Client.objects.filter(id=client_id).first()
        if client_obj:
            keyword = client_obj.name

    if keyword:
        logs = logs.filter(client__name__icontains=keyword)

    if client_id:
        logs = logs.filter(client__id=client_id)

    method = request.GET.get("method", "")
    if method:
        logs = logs.filter(method=method)

    date_from = request.GET.get("date_from", "")
    if date_from:
        logs = logs.filter(date__date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        logs = logs.filter(date__date__lte=date_to)

    assigned_user_id = request.GET.get("assigned_user", "")
    if assigned_user_id:
        logs = logs.filter(user__id=assigned_user_id)

    paginator = Paginator(logs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "keyword": keyword,
        "client_id": client_id,
        "method": method,
        "date_from": date_from,
        "date_to": date_to,
        "assigned_user_id": assigned_user_id,
        "method_choices": ContactLog.METHOD_CHOICES,
        "users": User.objects.filter(is_active=True),
    }
    return render(request, "contacts/contact_list.html", context)


@login_required
def contact_new(request):
    """接触記録の新規登録。「接触記録だけを保存する」「タスクも同時に保存する」の
    2つの保存ボタンがあり、request.POST['action']で処理を分岐する。"""
    # 取引先詳細画面からのリンクの場合、client を初期値にセット
    initial = {}
    client_id = request.GET.get("client")
    if client_id:
        initial["client"] = client_id

    default_next = (
        reverse("client_detail", args=[client_id]) if client_id else "/contacts/"
    )
    next_url = request.POST.get("next") or request.GET.get("next") or default_next

    if request.method == "POST":
        form = ContactLogForm(request.POST, request=request)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()

            # last_contact_dateを更新
            client = log.client
            latest = (
                client.contact_logs.filter(deleted_at__isnull=True)
                .order_by("-date")
                .first()
            )
            if latest:
                client.last_contact_date = latest.date
                client.save()

            # タスク同時作成（「タスクも同時に保存する」ボタンの場合のみ）
            if request.POST.get("action") == "save_with_task":
                task_title = form.cleaned_data.get("task_title")
                if task_title:
                    Task.objects.create(
                        client=log.client,
                        contact_log=log,
                        title=task_title,
                        due_date=form.cleaned_data.get("task_due_date"),
                        assigned_user=form.cleaned_data.get("task_assigned_user"),
                        status="pending",
                    )

            messages.success(request, "接触記録を登録しました。")
            return redirect("client_detail", pk=log.client.pk)
    else:
        form = ContactLogForm(initial=initial, request=request)

    return render(
        request,
        "contacts/contact_form.html",
        {"form": form, "title": "接触記録登録", "next_url": next_url},
    )


@login_required
def contact_detail(request, pk):
    """接触記録の詳細表示。"""
    log = get_object_or_404(ContactLog, pk=pk, deleted_at__isnull=True)
    return render(
        request,
        "contacts/contact_detail.html",
        {
            "log": log,
            "can_edit": can_edit(request.user),
        },
    )


@login_required
def contact_edit(request, pk):
    """接触記録の編集(Admin・Managerのみ)。編集時はタスク同時作成の項目自体が
    フォームから除外されるため(ContactLogForm参照)、タスク作成の分岐は無い。"""
    if not can_edit(request.user):
        messages.error(request, "編集権限がありません。")
        return redirect("contact_detail", pk=pk)

    log = get_object_or_404(ContactLog, pk=pk, deleted_at__isnull=True)
    if request.method == "POST":
        form = ContactLogForm(request.POST, instance=log)
        if form.is_valid():
            log = form.save()

            # last_contact_dateを更新
            client = log.client
            latest = (
                client.contact_logs.filter(deleted_at__isnull=True)
                .order_by("-date")
                .first()
            )
            if latest:
                client.last_contact_date = latest.date
                client.save()

            messages.success(request, "接触記録を更新しました。")
            return redirect("contact_detail", pk=pk)
    else:
        form = ContactLogForm(instance=log)

    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or reverse("contact_detail", args=[pk])
    )
    return render(
        request,
        "contacts/contact_form.html",
        {"form": form, "title": "接触記録編集", "next_url": next_url},
    )


@login_required
def contact_delete(request, pk):
    """接触記録の削除(Admin・Managerのみ)。論理削除の上、
    取引先のlast_contact_dateを残った記録の最新日時に(無ければNoneに)再計算する。"""
    if not can_edit(request.user):
        messages.error(request, "削除権限がありません。")
        return redirect("contact_detail", pk=pk)

    log = get_object_or_404(ContactLog, pk=pk, deleted_at__isnull=True)
    if request.method == "POST":
        log.deleted_at = timezone.now()
        log.save()

        # last_contact_dateを更新
        client = log.client
        latest = (
            client.contact_logs.filter(deleted_at__isnull=True)
            .order_by("-date")
            .first()
        )
        client.last_contact_date = latest.date if latest else None
        client.save()

        messages.success(request, "接触記録を削除しました。")
        return redirect("client_detail", pk=client.pk)

    return render(request, "contacts/contact_confirm_delete.html", {"log": log})
