from django.db import models
from users.models import CustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F

class Match(models.Model):
    STATUS_CHOICES = (
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('finished', '已结束'),
    )
    
    team_a = models.CharField(max_length=100, verbose_name='队伍A')
    team_b = models.CharField(max_length=100, verbose_name='队伍B')
    start_time = models.DateTimeField(verbose_name='开始时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name='状态')
    result_winner = models.CharField(max_length=100, blank=True, null=True, verbose_name='获胜队伍')
    result_score = models.CharField(max_length=20, blank=True, null=True, verbose_name='比分')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    # 新增字段
    match_series = models.CharField(max_length=50, blank=True, null=True, verbose_name='比赛局数')
    match_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='比赛性质')
    
    class Meta:
        verbose_name = '比赛'
        verbose_name_plural = '比赛列表'
        ordering = ['start_time']  # 按开始时间从早到晚排序
    
    def __str__(self):
        return f"{self.team_a} vs {self.team_b} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    def calculate_points(self):
        """计算所有用户对此比赛的预测积分并更新"""
        if self.status != 'finished' or not self.result_winner or not self.result_score:
            print(f"比赛 {self} 未结束或结果未填写，跳过积分计算")
            return
            
        print(f"开始计算比赛 {self} 的积分")
        print(f"比赛结果: {self.result_winner} ({self.result_score})")
        
        # 获取所有预测
        predictions = Prediction.objects.filter(match=self)
        print(f"找到 {predictions.count()} 条预测记录")
        
        if predictions.count() == 0:
            print("没有找到预测记录，请检查用户是否提交了预测")
            return
        
        for prediction in predictions:
            # 重置积分计算
            points = 0
            
            print(f"处理用户 {prediction.user.username} 的预测: "
                  f"{prediction.predicted_winner} ({prediction.predicted_score})")
            
            # 判断预测情况并计算积分
            if prediction.predicted_score == self.result_score:
                if prediction.predicted_winner == self.result_winner:
                    # 比分正确且队伍正确: 5分
                    points += 5
                    print(f"  比分正确且队伍正确 +5分")
                else:
                    # 比分正确但队伍错误: 1分
                    points += 1
                    print(f"  比分正确但队伍错误 +1分")
            elif prediction.predicted_winner == self.result_winner:
                # 比分错误但队伍正确: 3分
                points += 3
                print(f"  比分错误但队伍正确 +3分")
            
            # 更新用户积分 - 直接使用F表达式避免竞态条件
            CustomUser.objects.filter(pk=prediction.user.pk).update(points=F('points') + points)
            
            # 重新获取用户以获取最新积分
            updated_user = CustomUser.objects.get(pk=prediction.user.pk)
            
            # 记录积分变更
            prediction.points_earned = points
            prediction.save(update_fields=['points_earned'])
            
            print(f"  用户 {prediction.user.username} 获得 {points} 积分，总积分更新为: {updated_user.points}")

class Prediction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='用户')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name='比赛')
    predicted_winner = models.CharField(max_length=100, verbose_name='预测获胜队伍')
    predicted_score = models.CharField(max_length=20, verbose_name='预测比分')
    points_earned = models.IntegerField(default=0, verbose_name='获得积分')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '竞猜'
        verbose_name_plural = '竞猜列表'
        unique_together = ('user', 'match')  # 确保用户对每场比赛只能预测一次
    
    def __str__(self):
        return f"{self.user.username} - {self.match} - {self.predicted_winner}"

# 当比赛状态变为已结束时，自动计算积分
@receiver(post_save, sender=Match)
def update_points_on_match_finish(sender, instance, **kwargs):
    if instance.status == 'finished':
        instance.calculate_points() 