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
]
