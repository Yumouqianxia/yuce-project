import os
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator, MaxValueValidator, RegexValidator

def user_avatar_path(instance, filename):
    """
    生成用户头像的存储路径
    使用UUID替换原始文件名，避免中文文件名问题
    """
    # 获取文件扩展名
    ext = filename.split('.')[-1]
    # 使用UUID生成唯一文件名
    new_filename = f"{uuid.uuid4()}.{ext}"
    # 返回存储路径
    return f'user_avatars/user_{instance.id}/{new_filename}'

class CustomUser(AbstractUser):
    # 添加用户名验证器，只允许英文字母和数字
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9]+$',
                message='用户名只能包含英文字母和数字',
                code='invalid_username'
            ),
        ],
        help_text='用于登录的用户名，只能包含英文字母和数字',
        error_messages={
            'unique': "该用户名已被使用",
        },
    )
    
    # 添加昵称字段
    nickname = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='昵称',
        help_text='显示在个人资料和排行榜上的名称，可以使用中文'
    )
    
    points = models.IntegerField(default=0, verbose_name='积分')  # 用户积分字段
    avatar = models.ImageField(
        upload_to=user_avatar_path, 
        null=True, 
        blank=True, 
        verbose_name='头像',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif']),
        ]
    )
    
    # 添加上次修改密码的时间字段
    last_password_change = models.DateTimeField(null=True, blank=True, verbose_name='上次修改密码时间')
    
    # 保留现有的模型字段，但可以移除自动裁剪标志
    # avatar_is_cropped = models.BooleanField(default=False, verbose_name='头像已裁剪')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户列表'

    def __str__(self):
        return self.nickname or self.username
        
    def save(self, *args, **kwargs):
        # 如果没有设置昵称，默认使用用户名
        if not self.nickname:
            self.nickname = self.username
        super().save(*args, **kwargs)

    def can_change_password(self):
        """检查用户是否可以修改密码（每天限制一次）"""
        if not self.last_password_change:
            return True
            
        import datetime
        from django.utils import timezone
        
        # 计算上次修改密码到现在的时间差
        time_since_last_change = timezone.now() - self.last_password_change
        
        # 如果超过24小时，允许修改
        return time_since_last_change.days >= 1

class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '公告'
        verbose_name_plural = '公告列表'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
