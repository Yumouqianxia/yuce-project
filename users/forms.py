from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProfileEditForm(UserChangeForm):
    # 移除密码字段，我们不在这个表单中处理密码
    password = None
    
    # 添加头像上传字段
    avatar = forms.ImageField(
        required=False, 
        widget=forms.FileInput,
        help_text='最大文件大小: 2MB。允许的格式: jpg, jpeg, png, gif'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'avatar']
        
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # 检查文件大小 (2MB = 2 * 1024 * 1024 bytes)
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError('图片大小不能超过2MB')
        return avatar
