from django.urls import path

from apps.accounts import views as account_views
from . import views


app_name = "dashboard"

urlpatterns = [
    path("open/", account_views.access_with_token, name="panel_access_open"),
    path("", views.home, name="home"),
    path("history/", views.history_page, name="history_page"),
    path("milk/", views.milk_page, name="milk_page"),
    path("entries/", views.entry_list, name="entry_list"),
    path("entries/create/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.milk_edit, name="milk_edit"),
    path("entries/<int:pk>/delete/", views.milk_delete, name="milk_delete"),
    path("milk-price/create/", views.milk_price_create, name="milk_price_create"),
    path("milk-payment/<int:entry_id>/receive/", views.milk_payment_receive, name="milk_payment_receive"),
    path("finance/", views.finance_page, name="finance_page"),
    path("finance/create/", views.finance_create, name="finance_create"),
    path("finance/<int:pk>/edit/", views.finance_edit, name="finance_edit"),
    path("finance/<int:pk>/delete/", views.finance_delete, name="finance_delete"),
    path("reports/export/", views.general_report_export, name="general_report_export"),
    path("workers/", views.workers_page, name="workers_page"),
    path("workers-report/", views.workers_report_page, name="workers_report_page"),
    path("workers/create/", views.worker_create, name="worker_create"),
    path("workers/<int:pk>/edit/", views.worker_edit, name="worker_edit"),
    path("workers/<int:pk>/delete/", views.worker_delete, name="worker_delete"),
    path("workers/advance/", views.worker_advance_create, name="worker_advance_create"),
    path("workers/payments/<int:pk>/edit/", views.worker_payment_edit, name="worker_payment_edit"),
    path("workers/payments/<int:pk>/delete/", views.worker_payment_delete, name="worker_payment_delete"),
    path("reports/", views.report_list, name="report_list"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
]
