from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Match, Prediction, CustomUser
from .forms import PredictionForm
from django.db import models
from django.contrib import messages
from django.http import HttpResponse
import logging
from users.models import Announcement

logger = logging.getLogger('matches')

@login_required
def match_list(request):
    try:
        now = timezone.now()
        
        # 获取今天和未来的比赛
        upcoming_matches = Match.objects.filter(
            start_time__gte=now
        ).order_by('start_time')
        
        # 获取已结束的比赛
        finished_matches = Match.objects.filter(
            status='finished'
        ).order_by('-start_time')
        
        # 获取用户已经提交的预测
        prediction_dict = {}
        if request.user.is_authenticated:
            all_matches = list(upcoming_matches) + list(finished_matches)
            predictions = Prediction.objects.filter(user=request.user, match__in=all_matches)
            # 创建字典以便快速查找
            prediction_dict = {p.match_id: p for p in predictions}
            
        # 将预测添加到匹配对象
        for match in upcoming_matches:
            match.user_prediction = prediction_dict.get(match.id)
        
        for match in finished_matches:
            match.user_prediction = prediction_dict.get(match.id)
        
        # 获取活跃的公告（添加错误处理）
        try:
            announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]
        except Exception as e:
            print(f"获取公告时出错: {e}")
            announcements = []
        
        context = {
            'upcoming_matches': upcoming_matches,
            'finished_matches': finished_matches,
            'now': now,
            'announcements': announcements,
        }
        return render(request, 'matches/match_list.html', context)
    except Exception as e:
        print(f"match_list视图出错: {e}")
        # 返回一个简单的错误页面
        return render(request, 'error.html', {'error': str(e)})

@login_required
def submit_prediction(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    logger.debug(f"提交预测: 用户={request.user.username}, 比赛={match}")
    
    # 检查比赛是否已开始
    if match.status != 'not_started':
        messages.error(request, "比赛已经开始，无法提交预测")
        return redirect('match_list')
    
    # 检查用户是否已经提交过预测
    try:
        prediction = Prediction.objects.get(user=request.user, match=match)
        print(f"找到现有预测: {prediction.id}, 用户={prediction.user.username}, 比赛={prediction.match}")
    except Prediction.DoesNotExist:
        # 创建新的预测对象，但不保存
        prediction = Prediction(user=request.user, match=match)
        print(f"创建新预测对象: 用户={request.user.username}, 比赛={match}")
    
    if request.method == 'POST':
        print(f"收到POST请求: {request.POST}")
        form = PredictionForm(request.POST, instance=prediction)
        
        if form.is_valid():
            print(f"表单验证成功: {form.cleaned_data}")
            
            # 直接保存，不使用commit=False
            prediction.predicted_winner = form.cleaned_data['predicted_winner']
            prediction.predicted_score = form.cleaned_data['predicted_score']
            prediction.save()
            
            print(f"保存预测: ID={prediction.id}, 用户={prediction.user.username}, "
                  f"比赛={prediction.match}, 预测获胜={prediction.predicted_winner}, "
                  f"预测比分={prediction.predicted_score}")
            
            # 验证保存是否成功
            try:
                verification = Prediction.objects.get(id=prediction.id)
                print(f"验证保存成功: ID={verification.id}, 用户={verification.user.username}, "
                      f"预测获胜={verification.predicted_winner}, 预测比分={verification.predicted_score}")
                messages.success(request, "预测提交成功！")
            except Prediction.DoesNotExist:
                print("警告: 无法验证保存的预测!")
                messages.error(request, "预测提交失败，请重试")
            
            return redirect('match_list')
        else:
            print(f"表单验证失败: {form.errors}")
            messages.error(request, "表单验证失败，请检查输入")
    else:
        form = PredictionForm(instance=prediction)
    
    context = {
        'form': form,
        'match': match,
    }
    return render(request, 'matches/submit_prediction.html', context)

@login_required
def admin_predictions(request):
    """管理员查看所有预测的视图"""
    if not request.user.is_superuser:
        return redirect('home')
        
    predictions = Prediction.objects.all().order_by('-created_at')
    matches = Match.objects.all().order_by('-start_time')
    
    # 按比赛分组预测
    predictions_by_match = {}
    for match in matches:
        match_predictions = predictions.filter(match=match)
        if match_predictions.exists():
            predictions_by_match[match] = match_predictions
    
    context = {
        'predictions_by_match': predictions_by_match,
    }
    return render(request, 'matches/admin_predictions.html', context)

@login_required
def check_data_consistency(request):
    """检查数据一致性的视图"""
    if not request.user.is_superuser:
        return redirect('home')
    
    # 检查所有已结束比赛是否都计算了积分
    finished_matches = Match.objects.filter(status='finished')
    matches_without_results = finished_matches.filter(
        result_winner__isnull=True, result_score__isnull=True)
    
    # 检查所有预测是否都有对应的比赛
    orphaned_predictions = Prediction.objects.filter(match__isnull=True)
    
    # 检查用户积分总和是否等于预测积分总和
    total_prediction_points = Prediction.objects.aggregate(
        total=models.Sum('points_earned'))['total'] or 0
    total_user_points = CustomUser.objects.aggregate(
        total=models.Sum('points'))['total'] or 0
    
    context = {
        'finished_matches': finished_matches,
        'matches_without_results': matches_without_results,
        'orphaned_predictions': orphaned_predictions,
        'total_prediction_points': total_prediction_points,
        'total_user_points': total_user_points,
        'points_match': total_prediction_points == total_user_points,
    }
    return render(request, 'matches/check_consistency.html', context)

@login_required
def my_predictions(request):
    """显示当前用户的所有预测"""
    predictions = Prediction.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'predictions': predictions,
    }
    return render(request, 'matches/my_predictions.html', context)

@login_required
def test_db_connection(request):
    """测试数据库连接和写入"""
    if not request.user.is_superuser:
        return redirect('home')
    
    # 尝试创建一个测试预测
    test_match = Match.objects.first()
    if not test_match:
        return HttpResponse("没有找到任何比赛，请先创建比赛")
    
    # 直接使用原始SQL插入一条记录
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO matches_prediction (user_id, match_id, predicted_winner, predicted_score, points_earned, created_at) "
            "VALUES (%s, %s, %s, %s, %s, datetime('now'))",
            [request.user.id, test_match.id, test_match.team_a, '1-0', 0]
        )
    
    # 验证插入是否成功
    test_prediction = Prediction.objects.filter(
        user=request.user, 
        match=test_match,
        predicted_winner=test_match.team_a,
        predicted_score='1-0'
    ).order_by('-created_at').first()
    
    if test_prediction:
        return HttpResponse(f"测试成功！创建了预测: {test_prediction.id}")
    else:
        return HttpResponse("测试失败：无法创建预测记录")

@login_required
def finished_matches(request):
    # 获取已结束的比赛
    finished_matches = Match.objects.filter(
        status='finished'
    ).order_by('-start_time')
    
    # 获取用户已经提交的预测
    prediction_dict = {}
    if request.user.is_authenticated:
        predictions = Prediction.objects.filter(user=request.user, match__in=finished_matches)
        # 创建字典以便快速查找
        prediction_dict = {p.match_id: p for p in predictions}
        
    # 将预测添加到匹配对象
    for match in finished_matches:
        match.user_prediction = prediction_dict.get(match.id)
    
    context = {
        'finished_matches': finished_matches,
    }
    return render(request, 'matches/finished_matches.html', context) 