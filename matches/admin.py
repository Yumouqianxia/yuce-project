from django.contrib import admin
from .models import Match, Prediction
from django.urls import path
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from users.models import CustomUser

class MatchAdmin(admin.ModelAdmin):
    list_display = ('team_a', 'team_b', 'match_series', 'match_type', 'start_time', 'status', 'result_winner', 'result_score')
    list_filter = ('status', 'start_time', 'match_type')
    search_fields = ('team_a', 'team_b', 'match_type')
    fieldsets = (
        ('基本信息', {
            'fields': ('team_a', 'team_b', 'start_time', 'status')
        }),
        ('比赛详情', {
            'fields': ('match_series', 'match_type')
        }),
        ('比赛结果', {
            'fields': ('result_winner', 'result_score'),
            'classes': ('collapse',),
        }),
    )
    actions = ['calculate_points', 'recalculate_all_points']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('view_predictions/', self.admin_site.admin_view(self.view_predictions), 
                 name='view_predictions'),
            path('user_predictions/<int:user_id>/', self.admin_site.admin_view(self.user_predictions), 
                 name='user_predictions'),
        ]
        return custom_urls + urls
    
    def view_predictions(self, request):
        return redirect('admin_predictions')
    
    def user_predictions(self, request, user_id):
        user = CustomUser.objects.get(id=user_id)
        predictions = Prediction.objects.filter(user=user).order_by('-created_at')
        
        context = {
            'user': user,
            'predictions': predictions,
            'title': f"{user.username} 的预测",
        }
        return render(request, 'admin/matches/user_predictions.html', context)
    
    def calculate_points(self, request, queryset):
        for match in queryset:
            if match.status == 'finished':
                match.calculate_points()
        self.message_user(request, f"已为{queryset.count()}场比赛计算积分")
    calculate_points.short_description = "为选中的已结束比赛计算积分"
    
    def recalculate_all_points(self, request, queryset):
        # 重置所有用户积分
        CustomUser.objects.all().update(points=0)
        
        # 重置所有预测的获得积分
        Prediction.objects.all().update(points_earned=0)
        
        # 重新计算所有已结束比赛的积分
        finished_matches = Match.objects.filter(status='finished')
        for match in finished_matches:
            match.calculate_points()
            
        self.message_user(request, f"已重置所有用户积分并重新计算 {finished_matches.count()} 场比赛的积分")
    recalculate_all_points.short_description = "重置所有积分并重新计算"

admin.site.register(Match, MatchAdmin)

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'match', 'predicted_winner', 'predicted_score', 'points_earned', 'created_at')
    list_filter = ('match', 'predicted_winner', 'points_earned')
    search_fields = ('user__username', 'match__team_a', 'match__team_b') 