from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import CustomUser
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    nickname = forms.CharField(
        max_length=50, 
        required=False,
        help_text='显示在个人资料和排行榜上的名称，可以使用中文'
    )

    class Meta:
        model = CustomUser
        fields = ["username", "nickname", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nickname = self.cleaned_data['nickname'] or self.cleaned_data['username']
        if commit:
            user.save()
        return user

class ProfileEditForm(UserChangeForm):
    # 移除密码字段，我们不在这个表单中处理密码
    password = None
    
    # 添加昵称字段
    nickname = forms.CharField(
        max_length=50, 
        required=False,
        help_text='显示在个人资料和排行榜上的名称，可以使用中文'
    )
    
    # 移除头像字段，我们将使用专门的表单处理头像上传
    
    # 添加用户名字段，但添加验证
    username = forms.CharField(
        max_length=150,
        help_text='用于登录的用户名，只能包含英文字母和数字',
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9]+$',
                message='用户名只能包含英文字母和数字',
                code='invalid_username'
            ),
        ],
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'nickname', 'email']

# 添加一个专门用于修改用户名的表单
class UsernameChangeForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        help_text='用于登录的用户名，只能包含英文字母和数字',
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9]+$',
                message='用户名只能包含英文字母和数字',
                code='invalid_username'
            ),
        ],
    )
    
    class Meta:
        model = CustomUser
        fields = ['username']

class LimitedPasswordChangeForm(PasswordChangeForm):
    """限制每天只能修改一次密码的表单"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加更友好的字段标签和帮助文本
        self.fields['old_password'].label = '当前密码'
        self.fields['new_password1'].label = '新密码'
        self.fields['new_password1'].help_text = '密码必须包含至少8个字符，不能是纯数字，不能与用户名太相似。'
        self.fields['new_password2'].label = '确认新密码'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 检查用户是否可以修改密码
        if not self.user.can_change_password():
            import datetime
            from django.utils import timezone
            
            # 计算还需等待多长时间
            next_change_time = self.user.last_password_change + datetime.timedelta(days=1)
            time_left = next_change_time - timezone.now()
            
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            raise ValidationError(
                f"您今天已经修改过密码，请等待 {hours} 小时 {minutes} 分钟后再试。"
            )
            
        return cleaned_data
