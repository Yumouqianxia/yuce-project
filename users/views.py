from django.shortcuts import render, redirect
from .forms import RegisterForm, ProfileEditForm, UsernameChangeForm, LimitedPasswordChangeForm
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import CustomUser
from matches.models import Prediction
from django.db import models
from django.contrib import messages
import os
from django.conf import settings
from PIL import Image
from django.urls import reverse
from django.http import HttpResponseRedirect
import uuid
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print(f"用户 {username} 登录成功")
                # 尝试获取next参数，如果没有则默认重定向到profile
                next_url = request.GET.get('next', 'profile')
                return redirect(next_url)
            else:
                print(f"用户 {username} 登录失败")
                return render(request, 'users/login.html', {'error': '用户名或密码错误'})
        return render(request, 'users/login.html')
    except Exception as e:
        print(f"登录视图出错: {e}")
        return render(request, 'error.html', {'error': str(e)})

@login_required
def profile(request):
    # 获取用户的所有预测
    predictions = Prediction.objects.filter(user=request.user).order_by('-created_at')
    
    # 计算正确预测数量
    correct_predictions = Prediction.objects.filter(
        user=request.user,
        match__status='finished',
        predicted_winner=models.F('match__result_winner')
    ).count()
    
    # 获取最近的预测（限制为5条）
    recent_predictions = predictions[:5]
    
    context = {
        'user': request.user,
        'predictions': recent_predictions,
        'predictions_count': predictions.count(),
        'correct_predictions': correct_predictions,
    }
    return render(request, 'users/profile.html', context)

def user_logout(request):
    logout(request)
    return redirect('login')

def home(request):
    """用户首页视图"""
    if request.user.is_authenticated:
        return redirect('match_list')
    return render(request, 'users/home.html')

def leaderboard(request):
    """用户排行榜视图"""
    # 排除超级管理员和工作人员
    users = CustomUser.objects.filter(is_superuser=False, is_staff=False).order_by('-points')[:50]
    return render(request, 'users/leaderboard.html', {'users': users})

@login_required
def points_detail(request):
    """显示用户积分详情"""
    user = request.user
    predictions = Prediction.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'user': user,
        'predictions': predictions,
        'total_points': user.points,
    }
    return render(request, 'users/points_detail.html', context)

def debug_points(request):
    """调试视图：显示所有用户积分"""
    if not request.user.is_superuser:
        return redirect('home')
        
    users = CustomUser.objects.all().order_by('-points')
    predictions = Prediction.objects.all().order_by('-created_at')
    
    context = {
        'users': users,
        'predictions': predictions,
    }
    return render(request, 'users/debug_points.html', context)

@login_required
def edit_profile(request):
    """编辑个人资料视图"""
    if request.method == 'POST':
        # 创建表单时排除avatar字段
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {
        'form': form
    })

@login_required
def crop_avatar(request):
    """显示头像裁剪界面"""
    if not request.user.avatar:
        messages.error(request, "没有上传头像")
        return redirect('edit_profile')
    
    # 打印调试信息
    avatar_path = request.user.avatar.name
    full_path = os.path.join(settings.MEDIA_ROOT, avatar_path)
    print(f"Avatar path: {avatar_path}")
    print(f"Full path: {full_path}")
    print(f"File exists: {os.path.exists(full_path)}")
    
    # 如果文件不存在，显示错误
    if not os.path.exists(full_path):
        messages.error(request, f"头像文件不存在: {avatar_path}")
        return redirect('edit_profile')
    
    context = {
        'avatar_url': request.user.avatar.url,
        'avatar_path': avatar_path,
    }
    return render(request, 'users/crop_avatar.html', context)

@login_required
def save_cropped_avatar(request):
    """处理头像裁剪请求"""
    if request.method == 'POST':
        try:
            x = int(float(request.POST.get('x', 0)))
            y = int(float(request.POST.get('y', 0)))
            width = int(float(request.POST.get('width', 100)))
            height = int(float(request.POST.get('height', 100)))
            avatar_path = request.POST.get('avatar_path', '')
            
            if not avatar_path:
                raise ValueError("头像路径不能为空")
                
            # 获取完整的文件路径
            full_path = os.path.join(settings.MEDIA_ROOT, avatar_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"找不到文件: {full_path}")
            
            # 打开图片并裁剪
            img = Image.open(full_path)
            cropped_img = img.crop((x, y, x + width, y + height))
            
            # 调整大小为标准尺寸
            cropped_img = cropped_img.resize((300, 300), Image.LANCZOS)
            
            # 保存裁剪后的图片
            cropped_img.save(full_path, quality=90)
            
            # 清除可能的缓存
            from django.core.files.storage import default_storage
            if hasattr(default_storage, 'delete_thumbnail'):
                default_storage.delete_thumbnail(avatar_path)
            
            messages.success(request, '头像裁剪成功！')
        except FileNotFoundError as e:
            messages.error(request, f'找不到头像文件: {str(e)}')
            return redirect('edit_profile')
        except Exception as e:
            messages.error(request, f'裁剪头像时出错: {str(e)}')
            return redirect('edit_profile')
            
        return redirect('profile')
    
    return redirect('edit_profile')

@login_required
def change_username(request):
    if request.method == 'POST':
        form = UsernameChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '用户名修改成功！请使用新用户名登录。')
            return redirect('profile')
    else:
        form = UsernameChangeForm(instance=request.user)
    
    return render(request, 'users/change_username.html', {
        'form': form
    })

@login_required
def upload_avatar(request):
    """专门处理头像上传的视图"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            # 获取上传的文件
            avatar_file = request.FILES['avatar']
            
            # 检查文件大小
            if avatar_file.size > 2 * 1024 * 1024:  # 2MB
                messages.error(request, '图片大小不能超过2MB')
                return redirect('edit_profile')
                
            # 检查文件类型
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = avatar_file.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                messages.error(request, '只支持jpg、jpeg、png和gif格式的图片')
                return redirect('edit_profile')
            
            # 生成唯一文件名
            new_filename = f"{uuid.uuid4()}.{ext}"
            
            # 确保用户目录存在
            user_dir = os.path.join(settings.MEDIA_ROOT, f'user_avatars/user_{request.user.id}')
            os.makedirs(user_dir, exist_ok=True)
            
            # 构建完整的文件路径
            file_path = os.path.join(user_dir, new_filename)
            
            # 保存文件
            with open(file_path, 'wb+') as destination:
                for chunk in avatar_file.chunks():
                    destination.write(chunk)
            
            # 更新用户头像字段
            relative_path = f'user_avatars/user_{request.user.id}/{new_filename}'
            request.user.avatar = relative_path
            request.user.save()
            
            # 重定向到裁剪页面
            return redirect('crop_avatar')
            
        except Exception as e:
            messages.error(request, f'上传头像时出错: {str(e)}')
            return redirect('edit_profile')
    
    return redirect('edit_profile')

@login_required
def change_password(request):
    """修改密码视图"""
    # 检查用户是否可以修改密码
    if not request.user.can_change_password():
        import datetime
        
        # 计算还需等待多长时间
        next_change_time = request.user.last_password_change + datetime.timedelta(days=1)
        time_left = next_change_time - timezone.now()
        
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        
        messages.error(
            request, 
            f"您今天已经修改过密码，请等待 {hours} 小时 {minutes} 分钟后再试。"
        )
        return redirect('profile')
    
    if request.method == 'POST':
        form = LimitedPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # 更新上次修改密码时间
            user.last_password_change = timezone.now()
            user.save()
            
            # 更新会话，避免用户被登出
            update_session_auth_hash(request, user)
            
            messages.success(request, '密码修改成功！')
            return redirect('profile')
    else:
        form = LimitedPasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {
        'form': form
    })
