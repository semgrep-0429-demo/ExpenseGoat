"""
Seed demo data: departments, users (alice, bob, cathy, dave, frank), expenses, receipts.
Passwords are documented in README.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from django.contrib.auth import get_user_model
from expenses.models import Department, EmployeeProfile, Expense, Receipt

User = get_user_model()

DEMO_PASSWORD = 'demo1234'


class Command(BaseCommand):
    help = 'Create demo departments, users, expenses, and receipts.'

    def handle(self, *args, **options):
        dept_eng = Department.objects.get_or_create(
            code='ENG',
            defaults={'name': 'Engineering', 'code': 'ENG'},
        )[0]
        dept_sales = Department.objects.get_or_create(
            code='SAL',
            defaults={'name': 'Sales', 'code': 'SAL'},
        )[0]
        dept_hr = Department.objects.get_or_create(
            code='HR',
            defaults={'name': 'HR', 'code': 'HR'},
        )[0]

        def get_or_create_user(username, department, role, **kwargs):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com', **kwargs},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile, _ = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={'department': department, 'role': role},
            )
            if profile.department != department or profile.role != role:
                profile.department = department
                profile.role = role
                profile.save()
            return user

        alice = get_or_create_user('alice', dept_eng, EmployeeProfile.Role.EMPLOYEE)
        bob = get_or_create_user('bob', dept_eng, EmployeeProfile.Role.MANAGER)
        cathy = get_or_create_user('cathy', dept_sales, EmployeeProfile.Role.EMPLOYEE)
        dave = get_or_create_user('dave', dept_sales, EmployeeProfile.Role.MANAGER)
        frank = get_or_create_user('frank', dept_hr, EmployeeProfile.Role.FINANCE)
        frank.profile.department = dept_eng
        frank.profile.save()

        def expense(employee, amount, category, description, status=Expense.Status.DRAFT, **kwargs):
            profile = getattr(employee, 'profile', None)
            dept = profile.department if profile else dept_eng
            e, _ = Expense.objects.get_or_create(
                employee=employee,
                amount=Decimal(str(amount)),
                description=(description or '')[:200],
                defaults={
                    'department': dept,
                    'category': category,
                    'status': status,
                    'currency': 'USD',
                    **kwargs,
                },
            )
            if e.status != status or e.category != category:
                e.department = dept
                e.amount = Decimal(str(amount))
                e.category = category
                e.status = status
                for k, v in kwargs.items():
                    setattr(e, k, v)
                e.save()
            return e

        now = timezone.now()
        e1 = expense(alice, 50, Expense.Category.MEALS, 'Team lunch', Expense.Status.SUBMITTED, submitted_at=now)
        e2 = expense(alice, 120, Expense.Category.TRAVEL, 'Train ticket', Expense.Status.DRAFT)
        e3 = expense(bob, 30, Expense.Category.SUPPLIES, 'Office supplies', Expense.Status.APPROVED, submitted_at=now, reviewed_at=now)
        e4 = expense(cathy, 200, Expense.Category.TRAVEL, 'Conference travel', Expense.Status.SUBMITTED, submitted_at=now)
        e5 = expense(cathy, 15, Expense.Category.MEALS, 'Coffee', Expense.Status.DRAFT)
        e6 = expense(dave, 75, Expense.Category.OTHER, 'Client dinner', Expense.Status.PAID, submitted_at=now, reviewed_at=now, paid_at=now)
        e7 = expense(alice, 25, Expense.Category.MEALS, 'Lunch', Expense.Status.DENIED, submitted_at=now, reviewed_at=now)
        e8 = expense(cathy, 100, Expense.Category.SUPPLIES, 'Software license', Expense.Status.SUBMITTED, submitted_at=now)
        e9 = expense(bob, 45, Expense.Category.TRAVEL, 'Parking', Expense.Status.DRAFT)
        e10 = expense(alice, 80, Expense.Category.OTHER, 'Misc', Expense.Status.APPROVED, submitted_at=now, reviewed_at=now)

        for e in [e1, e3, e6]:
            if not e.receipts.exists():
                r = Receipt.objects.create(expense=e, uploaded_by=e.employee)
                if r.file:
                    pass
                else:
                    pass

        self.stdout.write(self.style.SUCCESS(
            f'Demo data created. Users: alice, bob, cathy, dave, frank. Password: {DEMO_PASSWORD}'
        ))
