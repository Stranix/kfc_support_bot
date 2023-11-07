from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

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
    BotCommand,
    BreakShift,
    BotCommandCategory,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
    ]

    filter_horizontal = [
        'groups',
        'managers',
    ]

    readonly_fields = [
        'registered_at',
        'tg_nickname',
        'tg_id',
    ]

    def response_change(self, request, obj):
        if 'next' not in request.GET:
            return super().response_change(request, obj)
        if url_has_allowed_host_and_scheme(
                request.GET['next'],
                settings.ALLOWED_HOSTS,
        ):
            return redirect(request.GET['next'])


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
    list_display = [
        'employee',
        'shift_start_at',
        'shift_end_at',
        'is_works',
    ]


@admin.register(BotCommand)
class BotCommandAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'description',
        'view_priority',
    ]

    list_editable = [
        'category',
    ]


@admin.register(BotCommandCategory)
class BotCommandCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(BreakShift)
class BreakShiftAdmin(admin.ModelAdmin):
    readonly_fields = [
        'start_break_at',
        'end_break_at',
    ]
    list_display = [
        'employee',
        'start_break_at',
        'end_break_at',
        'is_active',
    ]
