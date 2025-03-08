import os
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator, MaxValueValidator

def user_avatar_path(instance, filename):
    # 获取文件扩展名
    ext = filename.split('.')[-1]
    # 使用UUID生成唯一文件名，避免中文文件名问题
    filename = f"{uuid.uuid4()}.{ext}"
    # 文件将上传到 MEDIA_ROOT/user_avatars/user_<id>/<filename>
    return f'user_avatars/user_{instance.id}/{filename}'

class CustomUser(AbstractUser):
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

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户列表'

    def __str__(self):
        return self.username

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
