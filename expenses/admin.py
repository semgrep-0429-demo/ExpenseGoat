from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import Department, EmployeeProfile, Expense, Receipt, Approval

User = get_user_model()


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'role', 'title')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'department', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'department', 'category')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense', 'uploaded_by', 'created_at')


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('id', 'expense', 'reviewer', 'decision', 'created_at')
