"""
Authorization helpers for expense access control.
"""
from .models import Expense


def user_can_access_expense(user, expense):
    """
    Returns True if user may view this expense (owner, same department manager, or finance).
    """
    if not user or not user.is_authenticated:
        return False
    if expense.employee_id == user.id:
        return True
    profile = getattr(user, 'profile', None)
    if not profile:
        return False
    if profile.is_finance:
        return True
    if profile.is_manager and profile.department_id == expense.department_id:
        return True
    return False


def user_can_edit_expense(user, expense):
    """User may edit only their own draft expense."""
    if not user or not user.is_authenticated:
        return False
    return expense.employee_id == user.id and expense.status == Expense.Status.DRAFT


def user_can_submit_expense(user, expense):
    """User may submit only their own draft expense."""
    if not user or not user.is_authenticated:
        return False
    return expense.employee_id == user.id and expense.status == Expense.Status.DRAFT


def user_can_review_expense(user, expense):
    """Manager may review submitted expenses in their department (not their own)."""
    if not user or not user.is_authenticated:
        return False
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_manager or profile.is_finance:
        return False
    if expense.employee_id == user.id:
        return False
    if expense.department_id != profile.department_id:
        return False
    return expense.status == Expense.Status.SUBMITTED


def user_can_mark_paid(user, expense):
    """Finance may mark approved expenses as paid."""
    if not user or not user.is_authenticated:
        return False
    profile = getattr(user, 'profile', None)
    if not profile or not profile.is_finance:
        return False
    return expense.status == Expense.Status.APPROVED


def get_expenses_visible_to_user(user):
    """Queryset of expenses the user is allowed to see."""
    from django.db.models import Q

    if not user or not user.is_authenticated:
        return Expense.objects.none()
    profile = getattr(user, 'profile', None)
    if profile and profile.is_finance:
        return Expense.objects.all().select_related('employee', 'department')
    if profile and profile.is_manager:
        return Expense.objects.filter(
            Q(employee=user) | Q(department=profile.department)
        ).select_related('employee', 'department')
    return Expense.objects.filter(employee=user).select_related('employee', 'department')
