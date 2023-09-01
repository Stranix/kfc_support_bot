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
    pass


@admin.register(ServerType)
class ServerTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    pass


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    pass


@admin.register(FranchiseOwner)
class FranchiseOwner(admin.ModelAdmin):
    pass
