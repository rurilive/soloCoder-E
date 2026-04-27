# 会议系统设计文档

> 包管理工具: uv
> 绑定地址: 0.0.0.0:5555

---

## 1. 项目概述

### 1.1 目标
开发一个功能完整的实时会议系统，支持多人视频通话、屏幕共享、实时聊天和会议录制。

### 1.2 技术栈
- **后端框架**: FastAPI (与现有项目保持一致)
- **实时通信**: WebSocket (信令) + WebRTC (媒体传输)
- **前端**: HTML5 + JavaScript + CSS3
- **录制**: MediaRecorder API + 后端存储
- **部署**: Uvicorn + 绑定 `0.0.0.0:5555`

### 1.3 包管理
使用 `uv` 作为包管理工具：
- 安装依赖: `uv sync`
- 添加依赖: `uv add <package>`
- 运行服务: `uv run uvicorn app.main:app --host 0.0.0.0 --port 5555`

---

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                        客户端 (浏览器)                        │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  视频通话    │  屏幕共享    │  实时聊天    │  录制功能     │
│  (WebRTC)   │  (WebRTC)    │  (WebSocket) │ (MediaRecorder)│
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬───────┘
       │              │              │               │
       └──────────────┴──────┬───────┴───────────────┘
                             │
                    ┌────────▼────────┐
                    │  信令服务器     │
                    │  (WebSocket)    │
                    │  - 房间管理     │
                    │  - 信令交换     │
                    │  - 聊天消息     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  存储层         │
                    │  - SQLite       │
                    │  - 文件系统     │
                    │  (录制文件)     │
                    └─────────────────┘
```

### 2.2 核心模块

| 模块名称 | 功能描述 | 技术实现 |
|---------|---------|---------|
| **房间管理** | 创建、加入、销毁会议房间 | FastAPI + SQLite |
| **信令服务** | WebRTC 连接建立所需的信令交换 | WebSocket |
| **媒体传输** | 视频/音频/屏幕共享数据传输 | WebRTC PeerConnection |
| **实时聊天** | 房间内实时消息传递 | WebSocket |
| **录制服务** | 会议内容录制与存储 | MediaRecorder API + 后端存储 |

---

## 3. 详细设计

### 3.1 后端设计

#### 3.1.1 目录结构
```
app/
├── routers/
│   ├── conference.py       # 会议相关 API
│   └── recording.py        # 录制相关 API
├── models/
│   └── conference.py       # 会议数据模型
├── services/
│   ├── conference_manager.py    # 会议管理器
│   ├── signaling_service.py     # 信令服务
│   └── recording_service.py     # 录制服务
└── templates/
    └── conference/
        ├── lobby.html       # 会议大厅
        └── room.html        # 会议室
```

#### 3.1.2 数据模型

```python
# 会议房间
class ConferenceRoom(Base):
    __tablename__ = "conference_rooms"
    
    id = Column(Integer, primary_key=True)
    room_code = Column(String(8), unique=True, index=True)
    name = Column(String(100))
    host_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    max_participants = Column(Integer, default=10)
    status = Column(String(20), default="waiting")  # waiting/active/ended
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    recording_enabled = Column(Boolean, default=False)

# 会议参与者
class ConferenceParticipant(Base):
    __tablename__ = "conference_participants"
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("conference_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    join_time = Column(DateTime, default=datetime.utcnow)
    leave_time = Column(DateTime, nullable=True)
    is_host = Column(Boolean, default=False)

# 录制记录
class Recording(Base):
    __tablename__ = "recordings"
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("conference_rooms.id"))
    filename = Column(String(255))
    file_path = Column(String(500))
    duration = Column(Integer)  # 秒
    size = Column(Integer)      # 字节
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### 3.1.3 API 设计

| 端点 | 方法 | 描述 |
|-----|------|-----|
| `/conference/` | GET | 会议大厅页面 |
| `/conference/create` | POST | 创建会议房间 |
| `/conference/join/{room_code}` | POST | 加入会议 |
| `/conference/room/{room_code}` | GET | 会议室页面 |
| `/conference/ws/{room_code}` | WebSocket | 信令和聊天连接 |
| `/recording/upload` | POST | 上传录制文件 |
| `/recording/list` | GET | 获取录制列表 |
| `/recording/download/{recording_id}` | GET | 下载录制文件 |

#### 3.1.4 WebSocket 信令协议

信令消息格式：
```json
{
  "type": "message_type",
  "payload": {},
  "sender_id": "user_id"
}
```

消息类型：
| 类型 | 方向 | 描述 |
|-----|------|-----|
| `join_room` | Client → Server | 加入房间请求 |
| `room_joined` | Server → Client | 加入成功确认 |
| `participant_joined` | Server → Broadcast | 新参与者加入通知 |
| `participant_left` | Server → Broadcast | 参与者离开通知 |
| `offer` | Client → Client | WebRTC SDP Offer |
| `answer` | Client → Client | WebRTC SDP Answer |
| `ice_candidate` | Client → Client | WebRTC ICE Candidate |
| `chat_message` | Client → Broadcast | 聊天消息 |
| `start_recording` | Client → Server | 开始录制请求 |
| `stop_recording` | Client → Server | 停止录制请求 |
| `mute_audio` | Client → Broadcast | 静音通知 |
| `mute_video` | Client → Broadcast | 关闭视频通知 |
| `screen_share_start` | Client → Broadcast | 开始屏幕共享 |
| `screen_share_stop` | Client → Broadcast | 停止屏幕共享 |

### 3.2 前端设计

#### 3.2.1 页面结构

1. **会议大厅 (`lobby.html`)**
   - 创建会议按钮
   - 输入房间码加入
   - 公共会议列表

2. **会议室 (`room.html`)**
   - 视频网格布局
   - 屏幕共享区域
   - 控制栏（静音、视频、共享、录制、离开）
   - 聊天侧边栏
   - 参与者列表

#### 3.2.2 核心 JavaScript 模块

```javascript
// conference.js - 会议核心逻辑
class ConferenceManager {
  constructor(roomCode, userId) {
    this.roomCode = roomCode;
    this.userId = userId;
    this.ws = null;
    this.localStream = null;
    this.screenStream = null;
    this.peerConnections = new Map();  // userId -> RTCPeerConnection
    this.remoteStreams = new Map();     // userId -> MediaStream
    this.recorder = null;
  }
  
  // 连接 WebSocket 信令
  async connectSignaling() {}
  
  // 创建 WebRTC 连接
  async createPeerConnection(targetUserId) {}
  
  // 发送 Offer
  async sendOffer(targetUserId) {}
  
  // 处理 Answer
  async handleAnswer(offer) {}
  
  // 处理 ICE Candidate
  async handleICECandidate(candidate) {}
  
  // 开启屏幕共享
  async startScreenShare() {}
  
  // 停止屏幕共享
  async stopScreenShare() {}
  
  // 开始录制
  async startRecording() {}
  
  // 停止录制
  async stopRecording() {}
  
  // 发送聊天消息
  sendChatMessage(message) {}
}
```

### 3.3 录制功能设计

#### 3.3.1 方案选择

**客户端 MediaRecorder 方案**（初期简单实现）

| 优点 | 缺点 |
|-----|------|
| 实现简单，无需服务器转码 | 依赖客户端性能，可能丢帧 |
| 服务器压力小 | 视频质量受客户端影响 |

#### 3.3.2 录制流程

```
1. 用户点击"开始录制"
        ↓
2. 前端获取本地流 + 远端流组合
        ↓
3. 创建 MediaRecorder 实例
        ↓
4. 录制过程中定期保存数据块
        ↓
5. 用户点击"停止录制"
        ↓
6. 合并数据块为 Blob
        ↓
7. 分片上传到服务器
        ↓
8. 服务器保存并记录到数据库
```

### 3.4 WebRTC 连接流程

```
用户A                                    信令服务器                              用户B
  │                                          │                                    │
  │─────── 1. join_room ──────────────────>│                                    │
  │                                          │─────── room_joined ─────────────>│
  │                                          │                                    │
  │─────── 2. createOffer ────────────────>│                                    │
  │                                          │─────── forward offer ───────────>│
  │                                          │                                    │
  │                                          │<────── createAnswer ──────────────│
  │<─────── forward answer ─────────────────│                                    │
  │                                          │                                    │
  │─────── 3. ice_candidate ──────────────>│                                    │
  │                                          │─────── forward candidate ────────>│
  │                                          │                                    │
  │<─────── ice_candidate ──────────────────│<────── ice_candidate ─────────────│
  │                                          │                                    │
  │◄═══════════════════════════════════════════════════════════════════════════►│
  │                              WebRTC P2P 连接建立                              │
  │                              视频/音频数据直接传输                              │
  │◄═══════════════════════════════════════════════════════════════════════════►│
```

---

## 4. 依赖配置

需要添加的 Python 依赖（使用 uv 添加）：
```bash
uv add python-multipart aiofiles
```

pyproject.toml 依赖：
```toml
dependencies = [
    # ... 现有依赖
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "jinja2>=3.1.2",
    "sqlalchemy>=2.0.25",
    "python-multipart>=0.0.6",
    "websockets>=12.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "aiofiles>=23.2.1",
    "pydantic-settings>=2.0.0",
]
```

---

## 5. 安全考虑

1. **身份认证**: 复用现有用户系统，WebSocket 连接需验证 token
2. **房间权限**: 只有房主可以控制录制、踢出参与者等
3. **录制权限**: 需获得所有参与者同意才能录制（可配置）
4. **文件安全**: 录制文件需权限校验，防止未授权访问

---

## 6. 实施计划

| 阶段 | 任务 |
|-----|------|
| **Phase 1** | 后端房间管理 API + 基础 WebSocket 信令 |
| **Phase 2** | 前端会议室 UI + 基础 WebRTC 1v1 视频 |
| **Phase 3** | 多人视频支持 + 屏幕共享 |
| **Phase 4** | 实时聊天功能 |
| **Phase 5** | 录制功能（客户端方案） |
| **Phase 6** | 测试与优化 |

---

## 7. 与现有项目集成

- 复用现有的用户认证系统 (`app/auth.py`)
- 复用现有的 WebSocket 连接管理模式 (`app/routers/battle.py` 中的 `ConnectionManager`)
- 复用现有的模板系统和静态文件管理
- 绑定端口: `run.py` 已支持 `--port` 参数，默认已设为 `5555`，且强制绑定 `0.0.0.0`

---

## 8. 配置

- **绑定地址**: 0.0.0.0
- **端口**: 5555
- **启动命令**: `python run.py` 或 `uv run uvicorn app.main:app --host 0.0.0.0 --port 5555`
