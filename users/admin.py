from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Announcement

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'points', 'is_staff', 'is_superuser')
    actions = ['reset_points']
    
    def reset_points(self, request, queryset):
        queryset.update(points=0)
        self.message_user(request, f"已重置 {queryset.count()} 个用户的积分")
    reset_points.short_description = "重置所选用户的积分"
    
    # 添加 points 字段到 fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('积分信息', {'fields': ('points',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')
