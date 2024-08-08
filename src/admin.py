from django.db import models
from django.conf import settings
from django.forms import Textarea
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group as DjangoGroup, Permission
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from src.models import (
    CustomUser,
    CustomGroup,
    SDTask,
    GSDTask,
    Server,
    ServerType,
    Restaurant,
    FranchiseOwner,
    SyncReport,
    WorkShift,
    Dispatcher,
    BotCommand,
    BreakShift,
    BotCommandCategory,
    SimpleOneTask,
    TGDeepLink,
)

admin.site.unregister(DjangoGroup)
admin.site.register(Permission)


@admin.register(CustomGroup)
class CustomGroupAdmin(GroupAdmin):
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'name',
                    'managers',
                    'permissions',
                ]
            }
        ),
    ]
    filter_horizontal = [
        'permissions',
        'managers',
    ]


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = [
        'login',
        'name',
        'tg_id',
        'tg_nickname',
        'email',
        'is_staff',
        'is_active',
        'date_joined',
    ]
    list_filter = ['is_staff', 'is_active', ]
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'login',
                    'name',
                    'email',
                    'dispatcher_name',
                    'tg_nickname',
                    'password',
                ]
            }
        ),
        (
            'Permissions',
            {
                'fields': [
                    'groups',
                    'user_permissions',
                    'is_staff',
                    'is_active',
                    'date_joined',
                ]
            }
        ),
    ]
    add_fieldsets = (
        (
            None,
            {
                'classes': ['wide', ],
                'fields': [
                    'login',
                    'name',
                    'email',
                    'tg_id',
                    'tg_nickname',
                    'dispatcher_name',
                    'password1',
                    'password2',
                    'groups',
                    'user_permissions',
                    'is_staff',
                    'is_active',
                ]
            }
        ),
    )
    readonly_fields = ['date_joined']
    search_fields = ['name', 'tg_nickname']
    ordering = ['date_joined', ]

    def response_change(self, request, obj):
        if 'next' not in request.GET:
            return super().response_change(request, obj)
        if url_has_allowed_host_and_scheme(
                request.GET['next'],
                settings.ALLOWED_HOSTS,
        ):
            return redirect(request.GET['next'])


@admin.register(SDTask)
class SDTaskAdmin(admin.ModelAdmin):
    list_display = [
        'applicant',
        'new_applicant',
        'number',
        'performer',
        'new_performer',
        'start_at',
        'finish_at',
        'support_group',
        'title',
        'status',
        'rating',
    ]
    search_fields = [
        'number',
    ]


@admin.register(SimpleOneTask)
class SimpleOneTaskAdmin(admin.ModelAdmin):
    list_display = [
        'number',
        'fact_start',
        'subject',
        'sys_id',
        'sla',
        'exp_sla',
        'request_type',
        'caller_department',
        'restaurant',
        'company',
        'assignment_group',
    ]
    search_fields = [
        'number',
    ]

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 80})},
    }


@admin.register(GSDTask)
class GSDTaskAdmin(admin.ModelAdmin):
    list_display = [
        'applicant',
        'number',
        'restaurant',
        'start_at',
        'expired_at',
        'service',
        'gsd_group',
        'title',
    ]
    search_fields = [
        'number',
    ]


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
        'employee',
        'new_employee',
        'server_type',
        'user_choice',
        'start_at',
    ]


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = [
        'employee',
        'new_employee',
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
    filter_horizontal = [
        'new_groups'
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
        'new_employee',
        'start_break_at',
        'end_break_at',
        'is_active',
    ]


@admin.register(Dispatcher)
class DispatcherAdmin(admin.ModelAdmin):
    list_display = [
        'dispatcher_number',
        'performer',
        'new_performer',
        'company',
        'restaurant',
        'itsm_number',
        'performer',
        'gsd_numbers',
    ]
    search_fields = [
        'dispatcher_number',
        'gsd_numbers',
    ]


@admin.register(TGDeepLink)
class TGDeepLinkAdmin(admin.ModelAdmin):
    list_display = [
        'deeplink_key',
        'deeplink',
        'group',
        'user',
        'creat_at',
        'is_active',
    ]
