from django.contrib import admin

from ussd.models import USSDSession, USSDRequestLog, USSDVoterPin


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ('msisdn', 'provider_session_id', 'current_step', 'status', 'updated_at')
    list_filter = ('status', 'current_step')
    search_fields = ('msisdn', 'provider_session_id')


@admin.register(USSDRequestLog)
class USSDRequestLogAdmin(admin.ModelAdmin):
    list_display = ('session', 'outcome', 'timestamp')
    list_filter = ('outcome',)
    search_fields = ('session__msisdn',)


@admin.register(USSDVoterPin)
class USSDVoterPinAdmin(admin.ModelAdmin):
    list_display = ('user', 'election', 'is_active', 'failed_attempts', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('user__email', 'user__index_number', 'user__phone_number')
