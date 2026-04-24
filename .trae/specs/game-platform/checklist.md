# 小游戏平台 - Verification Checklist

## 项目基础架构
- [ ] Checkpoint 1: 项目可以通过 `uv run uvicorn app.main:app --reload` 成功启动
- [ ] Checkpoint 2: 访问 http://localhost:8000/ 返回 200 状态码和首页内容
- [ ] Checkpoint 3: 目录结构符合预期 (app/, app/models/, app/plugins/, app/templates/, app/static/)
- [ ] Checkpoint 4: .gitignore 文件已创建，包含必要的忽略规则

## 用户系统（持久化）
- [ ] Checkpoint 5: 注册页面可以正常访问
- [ ] Checkpoint 6: 用户可以成功注册账号
- [ ] Checkpoint 7: 密码加密存储（数据库中无明文密码）
- [ ] Checkpoint 8: 登录页面可以正常访问
- [ ] Checkpoint 9: 用户可以使用正确的用户名和密码登录
- [ ] Checkpoint 10: 登录状态通过 Cookie 保持
- [ ] Checkpoint 11: 用户可以成功登出
- [ ] Checkpoint 12: 未登录用户访问需要登录的页面会被重定向到登录页

## 数据库模型
- [ ] Checkpoint 13: 数据库可以成功初始化并创建所有表
- [ ] Checkpoint 14: User 模型可以正确创建用户 (id, username, hashed_password, is_developer, created_at)
- [ ] Checkpoint 15: Game 模型可以正确创建游戏 (id, name, slug, description, developer)
- [ ] Checkpoint 16: Score 模型可以正确记录得分并关联游戏和用户
- [ ] Checkpoint 17: Review 模型可以正确保存评价 (评分 1-5)
- [ ] Checkpoint 18: ReviewReply 模型可以正确保存开发者回复并关联评价
- [ ] Checkpoint 19: GameRoom 模型可以正确创建对战房间 (id, game_id, host_id, invite_code, is_public, status)

## 插件化架构
- [ ] Checkpoint 20: BaseGamePlugin 基类定义了必要的接口方法
- [ ] Checkpoint 21: GameRegistry 可以注册游戏插件
- [ ] Checkpoint 22: GameRegistry 可以通过 slug 获取已注册的游戏
- [ ] Checkpoint 23: 游戏路由可以正确访问已注册的游戏页面

## 打地鼠游戏
- [ ] Checkpoint 24: 打地鼠游戏插件可以成功注册到注册表
- [ ] Checkpoint 25: 访问 /games/whack-a-mole 显示游戏页面
- [ ] Checkpoint 26: 游戏有 3x3 网格布局的地鼠洞
- [ ] Checkpoint 27: 点击开始按钮后，地鼠会随机出现
- [ ] Checkpoint 28: 点击地鼠可以得分 (每只 +10 分)
- [ ] Checkpoint 29: 游戏有倒计时功能 (30秒)
- [ ] Checkpoint 30: 游戏结束后显示最终得分
- [ ] Checkpoint 31: 得分可以成功提交到后端保存

## 排名系统
- [ ] Checkpoint 32: 多个用户的得分可以正确保存
- [ ] Checkpoint 33: 排名页面按分数从高到低排序显示
- [ ] Checkpoint 34: 排名显示包含用户名、分数、游戏时间
- [ ] Checkpoint 35: 支持按游戏过滤排名 (仅显示打地鼠游戏排名)

## 实时对战 - 房间管理
- [ ] Checkpoint 36: 已登录用户可以创建对战房间
- [ ] Checkpoint 37: 房间创建后生成唯一的邀请码
- [ ] Checkpoint 38: 房主可以选择房间是否公开
- [ ] Checkpoint 39: 公开房间显示在对战大厅
- [ ] Checkpoint 40: 玩家可以通过邀请链接加入房间
- [ ] Checkpoint 41: 玩家可以通过对战大厅加入公开房间
- [ ] Checkpoint 42: 房间满员（2人）后无法再加入

## 实时对战 - WebSocket 实时通讯
- [ ] Checkpoint 43: WebSocket 连接可以成功建立
- [ ] Checkpoint 44: 房间内两名玩家都可以连接到 WebSocket
- [ ] Checkpoint 45: 对战开始后，双方可以看到对方的游戏状态
- [ ] Checkpoint 46: 一方得分时，另一方实时看到更新
- [ ] Checkpoint 47: 游戏结束后显示对战结果 (胜负)
- [ ] Checkpoint 48: WebSocket 连接可以正常断开

## 评价系统
- [ ] Checkpoint 49: 用户可以对游戏提交评分 (1-5 星)
- [ ] Checkpoint 50: 用户可以撰写文字评论
- [ ] Checkpoint 51: 提交的评价成功保存到数据库
- [ ] Checkpoint 52: 游戏详情页显示平均评分
- [ ] Checkpoint 53: 游戏详情页显示评价列表
- [ ] Checkpoint 54: 开发者可以回复用户评价
- [ ] Checkpoint 55: 开发者回复显示在原评价下方

## 前端界面
- [ ] Checkpoint 56: 所有页面使用统一的基础模板 (base.html)
- [ ] Checkpoint 57: 导航栏显示正确（包含登录/注册按钮或用户信息）
- [ ] Checkpoint 58: 已登录用户在导航栏显示用户名和登出按钮
- [ ] Checkpoint 59: 页面样式统一美观
- [ ] Checkpoint 60: 游戏界面交互流畅

## 项目配置
- [ ] Checkpoint 61: pyproject.toml 包含所有必要依赖
- [ ] Checkpoint 62: 通过 `uv sync` 可以安装所有依赖
- [ ] Checkpoint 63: 数据库初始化脚本可以正常运行
- [ ] Checkpoint 64: 项目可以一键启动 (无需额外配置)
