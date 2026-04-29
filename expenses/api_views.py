"""
JSON API endpoints: mix of secure and intentionally vulnerable patterns.
"""
import csv
import json
from decimal import Decimal
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .auth_helpers import user_can_review_expense
from .models import Approval, Expense


def _expense_to_dict(expense):
    return {
        'id': expense.id,
        'employee': expense.employee.username,
        'department': expense.department.code,
        'amount': str(expense.amount),
        'currency': expense.currency,
        'category': expense.category,
        'description': expense.description,
        'status': expense.status,
        'created_at': expense.created_at.isoformat(),
    }


@login_required
@require_GET
def api_me_expenses(request):
    qs = Expense.objects.filter(employee=request.user).order_by('-created_at')
    return JsonResponse({'expenses': [_expense_to_dict(e) for e in qs]})


def _parse_json_body(request):
    if request.content_type == 'application/json' and request.body:
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            pass
    return {}


@login_required
@require_POST
def api_expenses_create(request):
    data = request.POST.dict() if request.POST else _parse_json_body(request)
    amount = data.get('amount') or '0'
    try:
        amount = Decimal(amount)
    except Exception:
        amount = Decimal('0')
    category = data.get('category', Expense.Category.OTHER)
    if category not in dict(Expense.Category.choices):
        category = Expense.Category.OTHER
    description = data.get('description', '')
    profile = getattr(request.user, 'profile', None)
    department = profile.department if profile else None
    if not department:
        return JsonResponse({'error': 'No department assigned'}, status=400)
    expense = Expense.objects.create(
        employee=request.user,
        department=department,
        amount=amount,
        currency=data.get('currency', 'USD'),
        category=category,
        description=description,
        status=Expense.Status.DRAFT,
    )
    return JsonResponse(_expense_to_dict(expense), status=201)


@login_required
@require_GET
def api_expense_by_id(request, pk):
    expense = Expense.objects.filter(pk=pk).select_related('employee', 'department').first()
    if not expense:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse(_expense_to_dict(expense))


@login_required
@require_POST
def api_expense_update_amount(request, pk):
    expense = Expense.objects.filter(pk=pk).first()
    if not expense:
        return JsonResponse({'error': 'Not found'}, status=404)
    # Authorization: only the owner can update their own expense
    if expense.employee != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    # Only DRAFT expenses can be modified
    if expense.status != Expense.Status.DRAFT:
        return JsonResponse({'error': 'Only draft expenses can be modified'}, status=400)
    data = _parse_json_body(request) or request.POST.dict()
    amount = data.get('amount')
    if amount is not None:
        try:
            expense.amount = Decimal(str(amount))
        except Exception:
            pass
    if 'description' in data:
        expense.description = str(data['description'])[:2000]
    expense.save()
    return JsonResponse(_expense_to_dict(expense))


@login_required
@require_GET
def api_manage_department_expenses(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_manager:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    qs = Expense.objects.filter(department=profile.department).order_by('-created_at')
    return JsonResponse({'expenses': [_expense_to_dict(e) for e in qs]})


@login_required
@require_POST
def api_manage_decision(request, pk):
    expense = Expense.objects.filter(pk=pk).select_related('department').first()
    if not expense:
        return JsonResponse({'error': 'Not found'}, status=404)
    if not user_can_review_expense(request.user, expense):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if expense.status != Expense.Status.SUBMITTED:
        return JsonResponse({'error': 'Expense not submitted'}, status=400)
    data = _parse_json_body(request) or request.POST.dict()
    decision = data.get('decision')
    note = data.get('note', '')
    if decision not in (Approval.Decision.APPROVED, Approval.Decision.DENIED):
        return JsonResponse({'error': 'Invalid decision'}, status=400)
    Approval.objects.create(
        expense=expense,
        reviewer=request.user,
        decision=decision,
        note=note,
    )
    expense.status = Expense.Status.APPROVED if decision == Approval.Decision.APPROVED else Expense.Status.DENIED
    expense.reviewed_at = timezone.now()
    expense.save()
    return JsonResponse(_expense_to_dict(expense))


@login_required
@require_GET
def api_finance_export(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_finance:
        return JsonResponse({'error': 'Forbidden'}, status=403)
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
def api_profile_update_department(request):
    from .models import EmployeeProfile, Department
    data = _parse_json_body(request) or request.POST.dict()
    department_id = data.get('department_id')
    if department_id is None:
        return JsonResponse({'error': 'department_id required'}, status=400)
    dept = Department.objects.filter(pk=department_id).first()
    if not dept:
        return JsonResponse({'error': 'Department not found'}, status=404)
    profile, _ = EmployeeProfile.objects.get_or_create(
        user=request.user,
        defaults={"role": EmployeeProfile.Role.EMPLOYEE},
    )
    profile.department = dept
    profile.save()
    return JsonResponse({'ok': True, 'department': dept.code})
