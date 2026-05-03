# 📚 电子阅读器 (E-Reader)

一个基于 Web 的电子阅读器应用，支持上传和阅读 EPUB 和 TXT 格式的电子书。

## ✨ 功能特性

### 📖 核心功能
- **文件上传**: 支持拖拽上传或点击选择 EPUB 和 TXT 格式的电子书
- **书籍解析**: 自动解析书籍章节结构，提取元数据（标题、作者）
- **章节导航**: 目录侧边栏，快速跳转到任意章节
- **阅读体验**:
  - 字体大小调节 (12px - 28px)
  - 行间距调节 (1.2 - 3.0)
  - 三种阅读主题: 浅色、深色、护眼( sepia )
  - 阅读进度条
  - 点击页面隐藏/显示控制栏

### 🔖 书签功能
- 按 `B` 键快速添加书签
- 支持添加书签备注
- 书签列表显示，可跳转到对应章节
- 支持删除书签

### 🎮 键盘快捷键
| 按键 | 功能 |
|------|------|
| `←` / `PageUp` | 上一章 |
| `→` / `PageDown` | 下一章 |
| `B` | 添加书签 |
| `Esc` | 关闭侧边栏/对话框 |

## 🛠️ 技术栈

### 后端
- **Python 3.8+**
- **FastAPI**: 高性能 Web 框架
- **Uvicorn**: ASGI 服务器
- **SQLAlchemy**: ORM 框架
- **SQLite**: 轻量级数据库
- **ebooklib**: EPUB 文件解析
- **BeautifulSoup4**: HTML 解析
- **Jinja2**: 模板引擎

### 前端
- **原生 JavaScript**: 无需额外框架
- **CSS3**: 响应式设计，CSS 变量主题系统
- **SVG 图标**: 轻量级矢量图标

## 📁 项目结构

```
soloCoder-E/
├── app/                      # 应用核心代码
│   ├── __init__.py          # 应用初始化
│   ├── main.py              # FastAPI 主应用和路由
│   ├── database.py          # 数据库配置
│   ├── models.py            # 数据模型定义
│   └── parser.py            # 电子书解析器
├── static/                   # 静态资源
│   ├── css/
│   │   ├── style.css        # 首页样式
│   │   └── reader.css       # 阅读器样式
│   └── js/
│       ├── app.js           # 首页交互逻辑
│       └── reader.js        # 阅读器交互逻辑
├── templates/                # 模板文件
│   ├── index.html           # 首页（上传/书架）
│   └── reader.html          # 阅读器页面
├── uploads/                  # 上传文件存储目录
├── start.sh                  # 启动脚本
├── stop.sh                   # 停止脚本
├── restart.sh                # 重启脚本
├── run.py                    # 主入口文件
├── pyproject.toml            # 项目配置和依赖
├── .gitignore                # Git 忽略文件
└── README.md                 # 本文档
```

## 🚀 快速开始

### 环境要求
- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆或进入项目目录**
   ```bash
   cd /path/to/soloCoder-E
   ```

2. **（推荐）创建虚拟环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # 或 Windows:
   # .venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -e .
   ```

### 启动服务

#### 方式一：使用脚本（推荐）

```bash
# 启动服务（后台运行）
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh
```

启动成功后会显示：
```
✅ 电子阅读器启动成功！
📍 PID: 12345
🌐 访问地址: http://0.0.0.0:5555
```

#### 方式二：直接运行

```bash
# 前台运行（用于开发调试）
python run.py

# 带自动重载（开发模式）
python run.py --reload

# 指定地址和端口
python run.py --host 127.0.0.1 --port 8080
```

### 访问应用

启动后，在浏览器中访问：
- 本地访问: `http://localhost:5555`
- 局域网访问: `http://<服务器IP>:5555`

## 📖 使用指南

### 1. 上传书籍
1. 打开首页
2. 点击上传区域或拖拽电子书文件到上传区域
3. 支持格式: `.epub`, `.txt`
4. 上传后系统会自动解析书籍和章节

### 2. 阅读书籍
1. 在"我的书架"中点击任意书籍卡片
2. 进入阅读器界面
3. 阅读控制：
   - 点击页面空白区域：隐藏/显示控制栏
   - 点击目录图标：查看书籍目录
   - 点击书签图标：管理书签
   - 点击设置图标：调整阅读设置

### 3. 管理设置
- **字体大小**: 12px - 28px，每次增减 2px
- **行间距**: 1.2 - 3.0，每次增减 0.2
- **主题**:
  - 浅色主题（默认）
  - 深色主题（适合夜间阅读）
  - 护眼主题（sepia，减少眼睛疲劳）

设置会自动保存到浏览器 localStorage，下次打开自动应用。

## 🗄️ 数据库模型

### 书籍 (Book)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(255) | 书名 |
| author | String(255) | 作者 |
| file_path | String(500) | 文件路径 |
| file_type | String(10) | 文件类型 (epub/txt) |
| created_at | DateTime | 创建时间 |
| last_read_at | DateTime | 最后阅读时间 |

### 章节 (Chapter)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| book_id | Integer | 外键，关联书籍 |
| title | String(255) | 章节标题 |
| order | Integer | 章节顺序 |
| content | Text | 章节内容 |

### 书签 (Bookmark)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| book_id | Integer | 外键，关联书籍 |
| chapter_id | Integer | 外键，关联章节 |
| position | Integer | 滚动位置 |
| note | Text | 书签备注 |
| created_at | DateTime | 创建时间 |

## 🔌 API 接口

### 书籍管理
- `GET /books/` - 获取所有书籍列表
- `GET /books/{book_id}` - 获取单本书籍详情（含章节列表）
- `DELETE /books/{book_id}` - 删除书籍
- `POST /upload/` - 上传电子书（multipart/form-data）

### 章节管理
- `GET /chapters/{chapter_id}` - 获取章节内容

### 书签管理
- `GET /bookmarks/{book_id}` - 获取书籍的所有书签
- `POST /bookmarks/` - 创建新书签
- `DELETE /bookmarks/{bookmark_id}` - 删除书签

## 🔧 配置说明

### 服务器配置
在 `run.py` 中可以修改默认配置：
- `--host`: 绑定地址，默认 `0.0.0.0`
- `--port`: 端口号，默认 `5555`
- `--reload`: 开发模式，自动重载

### 数据库
- 默认使用 SQLite 数据库，文件名为 `ereader.db`
- 数据库配置在 `app/database.py` 中

### 上传目录
- 上传的文件存储在 `uploads/` 目录
- 如需修改，编辑 `app/main.py` 中的 `UPLOAD_DIR` 变量

## 📋 开发指南

### 本地开发

1. 安装开发依赖：
   ```bash
   pip install -e ".[dev]"
   ```

2. 以开发模式运行：
   ```bash
   python run.py --reload
   ```

3. 访问 API 文档：
   - Swagger UI: `http://localhost:5555/docs`
   - ReDoc: `http://localhost:5555/redoc`

### 添加新功能

1. **后端路由**: 在 `app/main.py` 中添加新的路由函数
2. **数据模型**: 在 `app/models.py` 中定义新的数据模型
3. **解析器**: 在 `app/parser.py` 中扩展文件解析功能
4. **前端**: 在 `static/js/` 中添加 JavaScript 逻辑
5. **模板**: 在 `templates/` 中添加或修改 HTML 模板

## 🐛 常见问题

### Q1: 上传文件后无法解析？
**A**: 请确保：
- 文件扩展名是 `.epub` 或 `.txt`
- EPUB 文件是有效的（不是改了扩展名的其他文件）
- TXT 文件编码为 UTF-8 或 GBK（会自动尝试两种编码）

### Q2: 服务启动失败？
**A**: 检查：
- Python 版本 >= 3.8
- 所有依赖已正确安装（`pip install -e .`）
- 端口 5555 未被占用
- 查看日志文件 `ereader.log` 获取详细错误信息

### Q3: 如何修改端口？
**A**: 方式有两种：
1. 命令行参数：`python run.py --port 8080`
2. 修改 `start.sh` 中的 `PORT` 变量

### Q4: 数据存储在哪里？
**A**: 
- SQLite 数据库：`ereader.db`
- 上传的文件：`uploads/` 目录
- 日志文件：`ereader.log`

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**享受阅读！** 📖✨
