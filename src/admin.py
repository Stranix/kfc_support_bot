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
    FranchiseOwner
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
        'restaurant',
        'is_sync',
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
    ]

    list_display = [
        'id',
        'name',
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
