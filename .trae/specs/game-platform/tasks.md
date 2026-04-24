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
    - User (用户: id, username, is_developer)
    - Score (得分: id, game_id, user_id, score, created_at)
    - Review (评价: id, game_id, user_id, rating, comment, created_at)
    - ReviewReply (开发者回复: id, review_id, developer_id, content, created_at)
  - 创建数据库初始化脚本
- **Acceptance Criteria Addressed**: [AC-3, AC-5, AC-6]
- **Test Requirements**:
  - `programmatic` TR-2.1: 数据库可以成功初始化
  - `programmatic` TR-2.2: 所有模型都可以创建对应的表
  - `programmatic` TR-2.3: 模型之间的关联关系正确
- **Notes**: 使用 SQLite 便于开发，后续可以切换到 PostgreSQL

## [ ] Task 3: 插件化游戏架构实现
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 定义游戏插件基类 (BaseGamePlugin)
  - 实现游戏注册表 (GameRegistry)
  - 实现游戏自动发现和加载机制
  - 提供统一的游戏路由接口
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-3.1: 插件基类定义了必需的接口方法
  - `programmatic` TR-3.2: 游戏注册表可以注册和获取游戏
  - `programmatic` TR-3.3: 游戏路由可以正确访问已注册的游戏
- **Notes**: 插件需要实现: get_name(), get_slug(), get_template_name(), play()

## [ ] Task 4: 打地鼠游戏插件开发
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 创建打地鼠游戏插件类
  - 实现前端游戏页面 (Jinja2 + JavaScript)
  - 实现游戏逻辑:
    - 3x3 网格地鼠洞
    - 随机地鼠出现
    - 点击计分
    - 倒计时功能 (30秒)
  - 实现得分提交接口
- **Acceptance Criteria Addressed**: [AC-2]
- **Test Requirements**:
  - `programmatic` TR-4.1: 打地鼠插件可以成功注册
  - `programmatic` TR-4.2: 游戏页面可以正常访问
  - `programmatic` TR-4.3: 得分提交接口正常工作
  - `human-judgement` TR-4.4: 游戏界面美观，交互流畅
- **Notes**: 前端使用原生 JavaScript，无需额外框架

## [ ] Task 5: 用户系统和排名系统开发
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 实现用户简单标识 (用户名输入/选择)
  - 实现得分记录 API
  - 实现排名查询 API
  - 实现排名页面 (Jinja2 模板)
  - 支持按游戏过滤排名
  - 支持最高分和最近得分排序
- **Acceptance Criteria Addressed**: [AC-3]
- **Test Requirements**:
  - `programmatic` TR-5.1: 得分可以成功保存到数据库
  - `programmatic` TR-5.2: 排名按分数从高到低排序
  - `programmatic` TR-5.3: 排名页面正确展示数据
  - `programmatic` TR-5.4: 按游戏过滤功能正常
- **Notes**: 使用简单的用户名标识，无需密码认证

## [ ] Task 6: 评价系统开发
- **Priority**: P1
- **Depends On**: Task 5
- **Description**: 
  - 实现评价创建 API (评分 1-5, 评论)
  - 实现评价列表 API
  - 实现开发者回复 API
  - 实现评价页面 (Jinja2 模板)
  - 显示游戏平均评分
  - 支持开发者标识和回复功能
- **Acceptance Criteria Addressed**: [AC-5, AC-6]
- **Test Requirements**:
  - `programmatic` TR-6.1: 评价可以成功创建和保存
  - `programmatic` TR-6.2: 评分限制在 1-5 之间
  - `programmatic` TR-6.3: 开发者可以回复评价
  - `programmatic` TR-6.4: 评价列表正确显示评价和回复
  - `programmatic` TR-6.5: 平均评分计算正确
- **Notes**: 用户可以通过 is_developer 标识区分普通用户和开发者

## [ ] Task 7: 实时对战系统开发
- **Priority**: P1
- **Depends On**: Task 5
- **Description**: 
  - 实现 WebSocket 连接管理
  - 实现对战房间系统
  - 实现玩家匹配机制
  - 实现游戏状态实时同步
  - 实现对战结果计算
  - 实现对战页面 (Jinja2 模板)
- **Acceptance Criteria Addressed**: [AC-4]
- **Test Requirements**:
  - `programmatic` TR-7.1: WebSocket 连接可以建立和断开
  - `programmatic` TR-7.2: 房间创建和加入功能正常
  - `programmatic` TR-7.3: 游戏状态可以实时同步
  - `programmatic` TR-7.4: 对战结束后正确计算胜负
  - `human-judgement` TR-7.5: 对战界面实时更新流畅
- **Notes**: 使用 FastAPI 的 WebSocket 支持，实现简单的 2 人对战

## [ ] Task 8: 前端界面优化和整合
- **Priority**: P2
- **Depends On**: Task 6, Task 7
- **Description**: 
  - 统一全站 CSS 样式
  - 创建基础模板 (base.html)
  - 实现导航栏和页面布局
  - 优化各页面交互体验
  - 添加简单的动画效果
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-4, AC-5, AC-6]
- **Test Requirements**:
  - `human-judgement` TR-8.1: 页面样式统一美观
  - `human-judgement` TR-8.2: 导航清晰，页面跳转顺畅
  - `programmatic` TR-8.3: 所有模板正确继承基础模板
- **Notes**: 使用简单的 CSS，无需引入复杂的 CSS 框架

## [ ] Task 9: 项目配置和文档完善
- **Priority**: P2
- **Depends On**: Task 8
- **Description**: 
  - 完善 pyproject.toml 依赖配置
  - 配置环境变量和应用配置
  - 添加开发启动脚本
  - 添加数据库初始化说明
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6]
- **Test Requirements**:
  - `programmatic` TR-9.1: 通过 uv 可以安装所有依赖
  - `programmatic` TR-9.2: 启动脚本可以正常运行
  - `programmatic` TR-9.3: 数据库可以正常初始化
- **Notes**: 确保项目可以一键启动
