from django.urls import path

from . import api_views, views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/<int:pk>/submit/', views.expense_submit, name='expense_submit'),
    path('expenses/<int:expense_pk>/receipts/upload/', views.receipt_upload, name='receipt_upload'),
    path('manage/queue/', views.manage_queue, name='manage_queue'),
    path('manage/expenses/<int:pk>/review/', views.manage_review, name='manage_review'),
    path('manage/expenses/<int:pk>/approve_quick/', views.manage_approve_quick, name='manage_approve_quick'),
    path('finance/export/', views.finance_export, name='finance_export'),
    path('finance/expenses/<int:pk>/mark_paid/', views.finance_mark_paid, name='finance_mark_paid'),
    path('receipts/<int:pk>/download/', views.receipt_download, name='receipt_download'),
    path('api/me/expenses/', api_views.api_me_expenses),
    path('api/expenses/', api_views.api_expenses_create),
    path('api/expenses/<int:pk>/', api_views.api_expense_by_id),
    path('api/expenses/<int:pk>/update_amount/', api_views.api_expense_update_amount),
    path('api/manage/department_expenses/', api_views.api_manage_department_expenses),
    path('api/manage/expenses/<int:pk>/decision/', api_views.api_manage_decision),
    path('api/finance/export/', api_views.api_finance_export),
    path('api/profile/update_department/', api_views.api_profile_update_department),
]
