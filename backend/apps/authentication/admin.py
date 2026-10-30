from django.contrib import admin
from .models import User, PasswordResetToken, CandidateProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'username', 'full_name')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'is_used', 'is_active', 'expires_at', 'ip_address', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token_hash', 'ip_address')
    readonly_fields = ('token_hash', 'created_at', 'expires_at', 'ip_address')


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone_number', 'target_role', 'linkedin_url', 'github_url', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'target_role', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
