# 小游戏平台 - Verification Checklist

## 项目基础架构
- [ ] Checkpoint 1: 项目可以通过 `uv run uvicorn app.main:app --reload` 成功启动
- [ ] Checkpoint 2: 访问 http://localhost:8000/ 返回 200 状态码和首页内容
- [ ] Checkpoint 3: 目录结构符合预期 (app/, app/models/, app/plugins/, app/templates/, app/static/)

## 数据库模型
- [ ] Checkpoint 4: 数据库可以成功初始化并创建所有表
- [ ] Checkpoint 5: User 模型可以正确创建用户 (id, username, is_developer)
- [ ] Checkpoint 6: Game 模型可以正确创建游戏 (id, name, slug, description, developer)
- [ ] Checkpoint 7: Score 模型可以正确记录得分并关联游戏和用户
- [ ] Checkpoint 8: Review 模型可以正确保存评价 (评分 1-5)
- [ ] Checkpoint 9: ReviewReply 模型可以正确保存开发者回复并关联评价

## 插件化架构
- [ ] Checkpoint 10: BaseGamePlugin 基类定义了必要的接口方法
- [ ] Checkpoint 11: GameRegistry 可以注册游戏插件
- [ ] Checkpoint 12: GameRegistry 可以通过 slug 获取已注册的游戏
- [ ] Checkpoint 13: 游戏路由可以正确访问已注册的游戏页面

## 打地鼠游戏
- [ ] Checkpoint 14: 打地鼠游戏插件可以成功注册到注册表
- [ ] Checkpoint 15: 访问 /games/whack-a-mole 显示游戏页面
- [ ] Checkpoint 16: 游戏有 3x3 网格布局的地鼠洞
- [ ] Checkpoint 17: 点击开始按钮后，地鼠会随机出现
- [ ] Checkpoint 18: 点击地鼠可以得分 (每只 +10 分)
- [ ] Checkpoint 19: 游戏有倒计时功能 (30秒)
- [ ] Checkpoint 20: 游戏结束后显示最终得分
- [ ] Checkpoint 21: 得分可以成功提交到后端保存

## 排名系统
- [ ] Checkpoint 22: 用户可以输入用户名开始游戏
- [ ] Checkpoint 23: 多个用户的得分可以正确保存
- [ ] Checkpoint 24: 排名页面按分数从高到低排序显示
- [ ] Checkpoint 25: 排名显示包含用户名、分数、游戏时间
- [ ] Checkpoint 26: 支持按游戏过滤排名 (仅显示打地鼠游戏排名)

## 评价系统
- [ ] Checkpoint 27: 用户可以对游戏提交评分 (1-5 星)
- [ ] Checkpoint 28: 用户可以撰写文字评论
- [ ] Checkpoint 29: 提交的评价成功保存到数据库
- [ ] Checkpoint 30: 游戏详情页显示平均评分
- [ ] Checkpoint 31: 游戏详情页显示评价列表
- [ ] Checkpoint 32: 开发者可以回复用户评价
- [ ] Checkpoint 33: 开发者回复显示在原评价下方

## 实时对战
- [ ] Checkpoint 34: WebSocket 连接可以成功建立
- [ ] Checkpoint 35: 可以创建对战房间
- [ ] Checkpoint 36: 第二个玩家可以加入已创建的房间
- [ ] Checkpoint 37: 对战开始后，双方可以看到对方的游戏状态
- [ ] Checkpoint 38: 一方得分时，另一方实时看到更新
- [ ] Checkpoint 39: 游戏结束后显示对战结果 (胜负)
- [ ] Checkpoint 40: WebSocket 连接可以正常断开

## 前端界面
- [ ] Checkpoint 41: 所有页面使用统一的基础模板 (base.html)
- [ ] Checkpoint 42: 导航栏可以正确跳转到各页面 (首页、游戏、排名、评价)
- [ ] Checkpoint 43: 页面样式统一美观
- [ ] Checkpoint 44: 游戏界面交互流畅

## 项目配置
- [ ] Checkpoint 45: pyproject.toml 包含所有必要依赖
- [ ] Checkpoint 46: 通过 `uv sync` 可以安装所有依赖
- [ ] Checkpoint 47: 数据库初始化脚本可以正常运行
- [ ] Checkpoint 48: 项目可以一键启动 (无需额外配置)
