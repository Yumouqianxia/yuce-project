from django.shortcuts import render, redirect
from .forms import RegisterForm, ProfileEditForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import CustomUser
from matches.models import Prediction
from django.db import models
from django.contrib import messages

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
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {
        'form': form
    })
