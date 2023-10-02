from django.contrib import admin

from src.models import (
    Employee,
    Task,
    Group,
    Right,
    Server,
    ServerType,
    TaskComment,
    Restaurant,
    FranchiseOwner,
    SyncReport,
    WorkShift,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(Right)
class RightAdmin(admin.ModelAdmin):
    pass


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'id',
    ]

    list_display = [
        'id',
        'name',
        'ip',
        'web_server',
        'restaurant',
        'is_sync',
        'franchise_owner',
    ]
    list_editable = [
        'is_sync',
    ]


@admin.register(ServerType)
class ServerTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    pass


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'id',
        'code',
    ]

    list_display = [
        'id',
        'name',
        'code',
        'legal_entity',
        'server_ip',
        'is_sync',
        'franchise',
    ]
    list_editable = [
        'is_sync',
    ]


@admin.register(FranchiseOwner)
class FranchiseOwner(admin.ModelAdmin):
    pass


@admin.register(SyncReport)
class SyncReportAdmin(admin.ModelAdmin):
    search_fields = [
        'employee',
    ]

    list_display = [
        'id',
        'start_at',
        'employee',
        'server_type',
        'report',
    ]


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    pass
