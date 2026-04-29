from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .auth_helpers import (
    get_expenses_visible_to_user,
    user_can_access_expense,
    user_can_edit_expense,
    user_can_mark_paid,
    user_can_review_expense,
    user_can_submit_expense,
)
from .forms import ExpenseForm
from .models import Approval, Expense, Receipt


_django_login = LoginView.as_view(template_name='expenses/login.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('expense_list')
    return _django_login(request)


def logout_view(request):
    auth_logout(request)
    return redirect('login')


@login_required
@require_GET
def expense_list(request):
    expenses = get_expenses_visible_to_user(request.user).order_by('-created_at')
    return render(request, 'expenses/expense_list.html', {'expenses': expenses})


@login_required
@require_http_methods(['GET', 'POST'])
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.employee = request.user
            profile = getattr(request.user, 'profile', None)
            if profile and profile.department:
                expense.department = profile.department
            expense.save()
            return redirect('expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'New Expense'})


@login_required
@require_GET
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if not user_can_access_expense(request.user, expense):
        return HttpResponseForbidden('You do not have access to this expense.')
    return render(request, 'expenses/expense_detail.html', {'expense': expense})


@login_required
@require_http_methods(['GET', 'POST'])
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    profile = getattr(request.user, 'profile', None)
    manager_override = (
        profile
        and profile.is_manager
        and profile.department_id == expense.department_id
    )
    if not manager_override and not user_can_edit_expense(request.user, expense):
        return HttpResponseForbidden('You may only edit your own draft expenses.')
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'expense': expense, 'title': 'Edit Expense'})


@login_required
@require_POST
def expense_submit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if not user_can_submit_expense(request.user, expense):
        return HttpResponseForbidden('You may only submit your own draft expenses.')
    expense.status = Expense.Status.SUBMITTED
    expense.submitted_at = timezone.now()
    expense.save()
    return redirect('expense_detail', pk=expense.pk)


@login_required
@require_GET
def manage_queue(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_manager:
        return HttpResponseForbidden('Managers only.')
    expenses = Expense.objects.filter(
        department=profile.department,
        status=Expense.Status.SUBMITTED,
    ).exclude(employee=request.user).select_related('employee', 'department').order_by('submitted_at')
    return render(request, 'expenses/manage_queue.html', {'expenses': expenses})


@login_required
@require_http_methods(['GET', 'POST'])
def manage_review(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if not user_can_review_expense(request.user, expense):
        return HttpResponseForbidden('You may not review this expense.')
    if request.method == 'POST':
        decision = request.POST.get('decision')
        note = request.POST.get('note', '')
        if decision in ('APPROVED', 'DENIED'):
            with transaction.atomic():
                Approval.objects.create(
                    expense=expense,
                    reviewer=request.user,
                    decision=decision,
                    note=note,
                )
                expense.status = Expense.Status.APPROVED if decision == 'APPROVED' else Expense.Status.DENIED
                expense.reviewed_at = timezone.now()
                expense.save()
            return redirect('manage_queue')
    return render(request, 'expenses/manage_review.html', {'expense': expense})


@login_required
@require_GET
def finance_export(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_finance:
        return HttpResponseForbidden('Finance only.')
    import csv
    from io import StringIO
    expenses = Expense.objects.all().select_related('employee', 'department').order_by('department', 'created_at')
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['id', 'employee', 'department', 'amount', 'currency', 'category', 'status', 'created_at'])
    for e in expenses:
        writer.writerow([e.id, e.employee.username, e.department.code, e.amount, e.currency, e.category, e.status, e.created_at.isoformat()])
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses_export.csv"'
    return response


@login_required
@require_POST
def finance_mark_paid(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if not user_can_mark_paid(request.user, expense):
        return HttpResponseForbidden('Finance may only mark approved expenses as paid.')
    expense.status = Expense.Status.PAID
    expense.paid_at = timezone.now()
    expense.save()
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('expense_list')
    return redirect(next_url)


@login_required
@require_http_methods(['GET', 'POST'])
def receipt_upload(request, expense_pk):
    expense = get_object_or_404(Expense, pk=expense_pk)
    if not user_can_access_expense(request.user, expense):
        return HttpResponseForbidden('You do not have access to this expense.')
    if expense.employee_id != request.user.id:
        return HttpResponseForbidden('Only the expense owner may upload receipts.')
    if request.method == 'POST':
        f = request.FILES.get('receipt_file')
        if f:
            Receipt.objects.create(expense=expense, file=f, uploaded_by=request.user)
        return redirect('expense_detail', pk=expense.pk)
    return render(request, 'expenses/receipt_upload.html', {'expense': expense})


@require_GET
def receipt_download(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk)
    if not receipt.file:
        return HttpResponse('No file attached.', status=404)
    from django.http import FileResponse
    return FileResponse(receipt.file.open('rb'), as_attachment=True, filename=receipt.file.name.split('/')[-1])


@login_required
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    return redirect('expense_list')


@login_required
@require_POST
def manage_approve_quick(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if expense.status != Expense.Status.SUBMITTED:
        return HttpResponseForbidden('Expense is not submitted.')
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_manager:
        return HttpResponseForbidden('Managers only.')
    with transaction.atomic():
        Approval.objects.create(
            expense=expense,
            reviewer=request.user,
            decision=Approval.Decision.APPROVED,
            note='Quick approve',
        )
        expense.status = Expense.Status.APPROVED
        expense.reviewed_at = timezone.now()
        expense.save()
    return redirect('manage_queue')
