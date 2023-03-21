"""
@created at 2023.03.21
@author OKS in Aimdat Team
"""
from django.contrib.admin import ModelAdmin

class AccessAttemptAdmin(ModelAdmin):
    list_display = ('id', 'user_agent', 'ip_address', 'username', 'failures_since_start',)
    search_fields = ('ip_address', 'username', 'user_agent',)
    list_filter = ('user_agent',)
    ordering = ('-attempt_time',)
    readonly_fields = ('attempt_time',)

class AccessFailureAdmin(ModelAdmin):
    list_display = ('id', 'user_agent', 'ip_address', 'username', 'locked_out',)
    search_fields = ('ip_address', 'username', 'user_agent',)
    list_filter = ('user_agent',)
    ordering = ('-attempt_time',)
    readonly_fields = ('attempt_time',)

class AccessSuccessAdmin(ModelAdmin):
    list_display = ('id', 'user_agent', 'ip_address', 'username')
    search_fields = ('ip_address', 'username', 'user_agent',)
    list_filter = ('user_agent',)
    ordering = ('-attempt_time',)
    readonly_fields = ('attempt_time',)