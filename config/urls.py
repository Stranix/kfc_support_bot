from django.urls import path
from django.urls import include

from django.contrib import admin

from src import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.index, name='home'),
    path('employees/', views.show_employee, name='emp'),
    path('support_tasks/', views.show_support_tasks, name='support_tasks'),
    path('work_shifts/', views.show_shifts, name='shifts'),
    path('shift_report/', views.show_shift_report, name='shift_report'),
    path('sync_report/', views.show_sync_report_prev, name='sync_report_prev'),
    path('sync_report/<int:pk>', views.show_sync_report, name='sync_report'),
]
