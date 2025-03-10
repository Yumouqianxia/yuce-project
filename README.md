# 预测系统

一个基于Django的比赛预测系统，允许用户对比赛结果进行预测并获得积分。

## 功能特点

- 用户注册和登录
- 比赛列表和详情查看
- 比赛结果预测
- 用户积分系统
- 排行榜
- 公告系统
- 用户上传头像
- 用户修改密码

## 技术栈

- Django 5.1.7
- SQLite数据库
- Bootstrap 4.5.2
- Pillow (用于图像处理)

## 安装步骤

1. 克隆仓库
   ```
   git clone https://github.com/yourusername/yuce-project.git
   cd yuce-project
   ```

2. 创建并激活虚拟环境
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. 安装依赖
   ```
   pip install -r requirements.txt
   ```

4. 运行数据库迁移
   ```
   python manage.py migrate
   ```

5. 创建超级用户
   ```
   python manage.py createsuperuser
   ```

6. 启动开发服务器
   ```
   python manage.py runserver
   ```

## 使用说明

1. 访问 http://127.0.0.1:8000/ 进入系统
2. 注册新用户或使用已有账户登录
3. 浏览比赛列表并进行预测
4. 查看排行榜了解自己的排名

## 许可证

[MIT License](LICENSE) 
