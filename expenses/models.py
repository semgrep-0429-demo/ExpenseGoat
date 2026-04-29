from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.code})"


class EmployeeProfile(models.Model):
    class Role(models.TextChoices):
        EMPLOYEE = 'EMPLOYEE', 'Employee'
        MANAGER = 'MANAGER', 'Manager'
        FINANCE = 'FINANCE', 'Finance'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees',
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )
    title = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_manager(self):
        return self.role in (self.Role.MANAGER, self.Role.FINANCE)

    @property
    def is_finance(self):
        return self.role == self.Role.FINANCE


class Expense(models.Model):
    class Category(models.TextChoices):
        TRAVEL = 'TRAVEL', 'Travel'
        MEALS = 'MEALS', 'Meals'
        SUPPLIES = 'SUPPLIES', 'Supplies'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        APPROVED = 'APPROVED', 'Approved'
        DENIED = 'DENIED', 'Denied'
        PAID = 'PAID', 'Paid'

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='expenses',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Expense #{self.id} {self.amount} {self.currency} ({self.status})"


def receipt_upload_path(instance, filename):
    return f"receipts/expense_{instance.expense_id}/{instance.id}_{filename}"


class Receipt(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='receipts',
    )
    file = models.FileField(upload_to=receipt_upload_path, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_receipts',
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Receipt #{self.id} for Expense #{self.expense_id}"


class Approval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved'
        DENIED = 'DENIED', 'Denied'

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='approvals',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approvals_given',
    )
    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.decision} by {self.reviewer} on Expense #{self.expense_id}"
