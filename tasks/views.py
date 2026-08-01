from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .forms import TaskForm
from .models import Task


def can_delete(user):
    """タスクの削除が許可されるロールかどうかを判定する。"""
    return user.role in ["admin", "manager"]


@login_required
def task_list(request):
    """タスク一覧。ステータス・期日レンジ・担当者で絞り込み可能。
    ダッシュボードの「完了済みのタスクも見る」リンクからはstatus未指定で遷移してくる。"""
    tasks = Task.objects.filter(deleted_at__isnull=True).select_related(
        "client", "assigned_user"
    )

    # フィルタ
    status = request.GET.get("status", "")
    if status:
        tasks = tasks.filter(status=status)

    date_from = request.GET.get("date_from", "")
    if date_from:
        tasks = tasks.filter(due_date__gte=date_from)

    date_to = request.GET.get("date_to", "")
    if date_to:
        tasks = tasks.filter(due_date__lte=date_to)

    assigned_user_id = request.GET.get("assigned_user", "")
    if assigned_user_id:
        tasks = tasks.filter(assigned_user__id=assigned_user_id)

    tasks = tasks.order_by("due_date")

    paginator = Paginator(tasks, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    today = timezone.localdate()

    context = {
        "page_obj": page_obj,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "assigned_user_id": assigned_user_id,
        "status_choices": Task.STATUS_CHOICES,
        "users": User.objects.filter(is_active=True),
        "today": today,
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def task_new(request):
    """タスクの新規登録。担当者はデフォルトでログイン中のユーザー自身をセットする
    (別の担当者に変更したい場合はフォーム上で選び直せる)。"""
    initial = {}
    client_id = request.GET.get("client")
    if client_id:
        initial["client"] = client_id
    initial["assigned_user"] = request.user.id

    default_next = (
        reverse("client_detail", args=[client_id]) if client_id else "/tasks/"
    )
    next_url = request.POST.get("next") or request.GET.get("next") or default_next

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, "タスクを登録しました。")
            return redirect("task_detail", pk=task.pk)
    else:
        form = TaskForm(initial=initial)

    return render(
        request,
        "tasks/task_form.html",
        {"form": form, "title": "タスク新規登録", "next_url": next_url},
    )


@login_required
def task_detail(request, pk):
    """タスク詳細。期日超過(完了以外かつ期日が過去)の判定はここで行い、
    テンプレート側の赤字ハイライト表示に使われる。"""
    task = get_object_or_404(Task, pk=pk, deleted_at__isnull=True)
    today = timezone.localdate()
    context = {
        "task": task,
        "can_delete": can_delete(request.user),
        "today": today,
        "is_overdue": task.due_date and task.due_date < today and task.status != "done",
    }
    return render(request, "tasks/task_detail.html", context)


@login_required
def task_edit(request, pk):
    """タスクの編集。"""
    task = get_object_or_404(Task, pk=pk, deleted_at__isnull=True)
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or reverse("task_detail", args=[pk])
    )
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "タスクを更新しました。")
            return redirect("task_detail", pk=pk)
    else:
        form = TaskForm(instance=task)
    return render(
        request,
        "tasks/task_form.html",
        {"form": form, "title": "タスク編集", "next_url": next_url},
    )


@login_required
def task_delete(request, pk):
    """タスクの削除(Admin・Managerのみ)。削除後は紐づく取引先の詳細画面へ戻る。"""
    if not can_delete(request.user):
        messages.error(request, "削除権限がありません。")
        return redirect("task_detail", pk=pk)

    task = get_object_or_404(Task, pk=pk, deleted_at__isnull=True)
    client_pk = task.client.pk
    if request.method == "POST":
        task.deleted_at = timezone.now()
        task.save()
        messages.success(request, "タスクを削除しました。")
        return redirect("client_detail", pk=client_pk)
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
def task_status_update(request, pk):
    """一覧画面等からステータスだけをその場で変更するための簡易エンドポイント。
    next未指定時は"task_list"というURL名をredirect()に渡し、一覧へ戻す。"""
    task = get_object_or_404(Task, pk=pk, deleted_at__isnull=True)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            messages.success(request, "ステータスを更新しました。")
    return redirect(request.POST.get("next", "task_list"))
