# 小游戏平台 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 1: 项目初始化和基础架构搭建
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 使用 uv 初始化 Python 项目
  - 创建项目目录结构
  - 配置 FastAPI 应用入口
  - 配置 Jinja2 模板引擎
  - 配置静态文件目录
  - 创建 .gitignore 文件
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-1.1: 项目可以通过 `uv run uvicorn` 启动
  - `programmatic` TR-1.2: 访问根路径返回 200 状态码
  - `human-judgement` TR-1.3: 目录结构清晰，符合 Python 项目规范
- **Notes**: 项目结构建议: app/, app/models/, app/plugins/, app/templates/, app/static/

## [ ] Task 2: 数据库模型设计
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 配置 SQLAlchemy 连接 SQLite 数据库
  - 创建数据库模型:
    - Game (游戏: id, name, slug, description, developer)
    - User (用户: id, username, hashed_password, is_developer, created_at)
    - Score (得分: id, game_id, user_id, score, created_at)
    - Review (评价: id, game_id, user_id, rating, comment, created_at)
    - ReviewReply (开发者回复: id, review_id, developer_id, content, created_at)
    - GameRoom (对战房间: id, game_id, host_id, invite_code, is_public, status, created_at)
  - 创建数据库初始化脚本
- **Acceptance Criteria Addressed**: [AC-2, AC-5, AC-6, AC-7]
- **Test Requirements**:
  - `programmatic` TR-2.1: 数据库可以成功初始化
  - `programmatic` TR-2.2: 所有模型都可以创建对应的表
  - `programmatic` TR-2.3: 模型之间的关联关系正确
- **Notes**: 使用 SQLite 便于开发，后续可以切换到 PostgreSQL

## [ ] Task 3: 用户系统开发（持久化）
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现用户注册 API (用户名、密码)
  - 实现密码加密存储 (bcrypt)
  - 实现用户登录 API (会话 Cookie)
  - 实现用户登出 API
  - 实现注册页面模板
  - 实现登录页面模板
  - 实现登录状态装饰器
- **Acceptance Criteria Addressed**: [AC-2, AC-3]
- **Test Requirements**:
  - `programmatic` TR-3.1: 用户可以成功注册账号
  - `programmatic` TR-3.2: 密码加密存储，不存储明文
  - `programmatic` TR-3.3: 用户可以成功登录
  - `programmatic` TR-3.4: 登录状态可以保持
  - `programmatic` TR-3.5: 用户可以成功登出
- **Notes**: 使用 FastAPI 的 Request 和 Response 处理 Cookie

## [ ] Task 4: 插件化游戏架构实现
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 定义游戏插件基类 (BaseGamePlugin)
  - 实现游戏注册表 (GameRegistry)
  - 实现游戏自动发现和加载机制
  - 提供统一的游戏路由接口
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-4.1: 插件基类定义了必需的接口方法
  - `programmatic` TR-4.2: 游戏注册表可以注册和获取游戏
  - `programmatic` TR-4.3: 游戏路由可以正确访问已注册的游戏
- **Notes**: 插件需要实现: get_name(), get_slug(), get_template_name(), play()

## [ ] Task 5: 打地鼠游戏插件开发
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 创建打地鼠游戏插件类
  - 实现前端游戏页面 (Jinja2 + JavaScript)
  - 实现游戏逻辑:
    - 3x3 网格地鼠洞
    - 随机地鼠出现
    - 点击计分
    - 倒计时功能 (30秒)
  - 实现得分提交接口
- **Acceptance Criteria Addressed**: [AC-4]
- **Test Requirements**:
  - `programmatic` TR-5.1: 打地鼠插件可以成功注册
  - `programmatic` TR-5.2: 游戏页面可以正常访问
  - `programmatic` TR-5.3: 得分提交接口正常工作
  - `human-judgement` TR-5.4: 游戏界面美观，交互流畅
- **Notes**: 前端使用原生 JavaScript，无需额外框架

## [ ] Task 6: 排名系统开发
- **Priority**: P0
- **Depends On**: Task 5
- **Description**: 
  - 实现得分记录 API
  - 实现排名查询 API
  - 实现排名页面 (Jinja2 模板)
  - 支持按游戏过滤排名
  - 支持最高分和最近得分排序
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `programmatic` TR-6.1: 得分可以成功保存到数据库
  - `programmatic` TR-6.2: 排名按分数从高到低排序
  - `programmatic` TR-6.3: 排名页面正确展示数据
  - `programmatic` TR-6.4: 按游戏过滤功能正常
- **Notes**: 排名与用户系统关联

## [ ] Task 7: 实时对战系统 - 房间管理
- **Priority**: P1
- **Depends On**: Task 6
- **Description**: 
  - 实现创建对战房间 API
  - 生成房间邀请码/邀请链接
  - 实现房间公开/私有设置
  - 实现对战大厅页面（展示公开房间）
  - 实现通过邀请链接加入房间
  - 实现通过对战大厅加入房间
- **Acceptance Criteria Addressed**: [AC-6, AC-7]
- **Test Requirements**:
  - `programmatic` TR-7.1: 房主可以成功创建房间
  - `programmatic` TR-7.2: 房间邀请链接可以生成
  - `programmatic` TR-7.3: 公开房间显示在对战大厅
  - `programmatic` TR-7.4: 玩家可以通过邀请链接加入房间
  - `programmatic` TR-7.5: 玩家可以通过对战大厅加入公开房间
- **Notes**: 房间状态: waiting, playing, finished

## [ ] Task 8: 实时对战系统 - WebSocket 实时通讯
- **Priority**: P1
- **Depends On**: Task 7
- **Description**: 
  - 实现 WebSocket 连接管理
  - 实现房间内玩家连接管理
  - 实现游戏状态实时同步
  - 实现玩家得分实时同步
  - 实现对战开始/结束消息
  - 实现对战结果计算
  - 实现对战页面 (Jinja2 模板)
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-8.1: WebSocket 连接可以建立和断开
  - `programmatic` TR-8.2: 房间内两名玩家都可以连接
  - `programmatic` TR-8.3: 游戏状态可以实时同步
  - `programmatic` TR-8.4: 得分可以实时同步给对方
  - `programmatic` TR-8.5: 对战结束后正确计算胜负
  - `human-judgement` TR-8.6: 对战界面实时更新流畅
- **Notes**: 使用 FastAPI 的 WebSocket 支持

## [ ] Task 9: 评价系统开发
- **Priority**: P1
- **Depends On**: Task 6
- **Description**: 
  - 实现评价创建 API (评分 1-5, 评论)
  - 实现评价列表 API
  - 实现开发者回复 API
  - 实现评价页面 (Jinja2 模板)
  - 显示游戏平均评分
  - 支持开发者标识和回复功能
- **Acceptance Criteria Addressed**: [AC-9, AC-10]
- **Test Requirements**:
  - `programmatic` TR-9.1: 评价可以成功创建和保存
  - `programmatic` TR-9.2: 评分限制在 1-5 之间
  - `programmatic` TR-9.3: 开发者可以回复评价
  - `programmatic` TR-9.4: 评价列表正确显示评价和回复
  - `programmatic` TR-9.5: 平均评分计算正确
- **Notes**: 用户可以通过 is_developer 标识区分普通用户和开发者

## [ ] Task 10: 前端界面优化和整合
- **Priority**: P2
- **Depends On**: Task 8, Task 9
- **Description**: 
  - 统一全站 CSS 样式
  - 创建基础模板 (base.html)
  - 实现导航栏（包含登录/注册/用户信息）
  - 实现页面布局
  - 优化各页面交互体验
  - 添加简单的动画效果
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10]
- **Test Requirements**:
  - `human-judgement` TR-10.1: 页面样式统一美观
  - `human-judgement` TR-10.2: 导航清晰，页面跳转顺畅
  - `programmatic` TR-10.3: 所有模板正确继承基础模板
- **Notes**: 使用简单的 CSS，无需引入复杂的 CSS 框架

## [ ] Task 11: 项目配置和文档完善
- **Priority**: P2
- **Depends On**: Task 10
- **Description**: 
  - 完善 pyproject.toml 依赖配置
  - 配置环境变量和应用配置
  - 添加开发启动脚本
  - 添加数据库初始化说明
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10]
- **Test Requirements**:
  - `programmatic` TR-11.1: 通过 uv 可以安装所有依赖
  - `programmatic` TR-11.2: 启动脚本可以正常运行
  - `programmatic` TR-11.3: 数据库可以正常初始化
- **Notes**: 确保项目可以一键启动
