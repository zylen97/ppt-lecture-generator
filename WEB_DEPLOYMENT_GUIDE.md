# PPT讲稿生成器 Web版开发指南

## 🎯 项目概述

PPT讲稿生成器已成功完成Web化改造，采用了现代化的技术架构：

### 技术栈
- **Backend**: FastAPI + SQLite + LangChain适配
- **Frontend**: React 18 + TypeScript + Ant Design 5
- **Communication**: RESTful API + WebSocket（实时进度推送）
- **Development**: 本地开发环境

## 🏗️ 项目架构

```
ppt-lecture-generator/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── main.py            # 应用入口
│   │   ├── database.py        # 数据库配置
│   │   ├── models/            # SQLAlchemy模型
│   │   ├── schemas/           # Pydantic数据验证
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心业务逻辑（迁移自原项目）
│   │   └── services/          # 服务层
│   ├── requirements.txt       # Python依赖
│   └── run.py               # 启动脚本
│
├── frontend/                   # React前端
│   ├── src/
│   │   ├── components/        # 通用组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API服务层
│   │   ├── types/            # TypeScript类型
│   │   └── utils/            # 工具函数
│   ├── package.json          # 前端依赖
│   └── vite.config.ts        # Vite配置
│
└── README.md                 # 项目说明
```

## 🚀 本地开发环境部署

### 前置要求

- **Node.js**: 18.0+ 
- **Python**: 3.8+
- **NPM**: 8.0+ 或 Yarn
- **Git**: 最新版本

### 步骤一：克隆项目

```bash
git clone <repository-url>
cd ppt-lecture-generator
```

### 步骤二：后端设置

```bash
# 进入后端目录
cd backend

# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建数据目录
mkdir -p data uploads logs temp

# 启动后端服务
python run.py
```

后端服务将在 http://localhost:8000 启动

### 步骤三：前端设置

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用 yarn
yarn install

# 启动开发服务器
npm run dev
# 或使用 yarn
yarn dev
```

前端服务将在 http://localhost:3000 启动

### 步骤四：验证安装

1. **后端验证**:
   - 访问 http://localhost:8000/docs 查看API文档
   - 访问 http://localhost:8000/health 检查健康状态

2. **前端验证**:
   - 访问 http://localhost:3000 查看应用界面
   - 检查浏览器控制台是否有错误

## 📋 核心功能

### ✅ 已完成功能

1. **完整的Web应用架构**
   - 现代化的前后端分离架构
   - 响应式设计，支持多设备访问
   - 本地开发环境，快速启动

2. **数据持久化**
   - SQLite数据库存储
   - 用户文件管理
   - 任务状态跟踪
   - 讲稿版本管理
   - API配置管理

3. **核心业务逻辑迁移**
   - AI客户端（支持多种模型）
   - PPT处理器（LibreOffice集成）
   - 讲稿生成器（完整工作流）

4. **完整的API接口**
   - 文件上传和管理
   - 任务创建和监控
   - 讲稿生成和编辑
   - 配置管理

5. **现代化前端界面**
   - 仪表盘（系统概览）
   - 文件上传（拖拽支持、批量上传）
   - 任务管理（实时状态更新）
   - 讲稿管理（在线编辑、预览、导出）
   - 系统设置（API配置管理）

6. **高级功能**
   - WebSocket实时推送
   - 批量文件处理
   - 任务队列管理
   - 性能监控

## 🔧 开发配置

### 环境变量配置

创建 `backend/.env` 文件：

```env
# 数据库配置
DATABASE_URL=sqlite:///./data/ppt_generator.db

# 加密密钥（请修改为安全的密钥）
ENCRYPTION_KEY=your-secure-encryption-key-here

# 开发模式
DEBUG=true

# API配置
DEFAULT_API_ENDPOINT=https://api.openai.com/v1
```

创建 `frontend/.env` 文件：

```env
# API配置
VITE_API_BASE_URL=http://localhost:8000

# 应用配置
VITE_APP_TITLE=PPT讲稿生成器
VITE_APP_VERSION=1.0.0

# 开发配置
VITE_DEV_MODE=true
```

### API配置

首次使用需要在设置页面配置：

1. **API端点**: https://api.openai.com/v1 或中转服务
2. **API密钥**: 您的OpenAI API密钥
3. **模型选择**: gpt-4-vision-preview（推荐）

## 📊 开发要求

### 系统要求

- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 5GB以上可用空间
- **系统**: Windows/macOS/Linux

### 开发工具

- **代码编辑器**: VS Code（推荐）
- **API测试**: Postman 或类似工具
- **数据库查看**: DB Browser for SQLite

## 🔍 使用说明

### 基本工作流程

1. **上传PPT文件**
   - 支持 .ppt 和 .pptx 格式
   - 最大文件大小 100MB
   - 支持拖拽上传或批量上传

2. **创建处理任务**
   - 选择已上传的文件
   - 配置生成参数（时长、语言、风格等）
   - 启动处理任务

3. **监控任务进度**
   - WebSocket实时查看处理状态
   - 查看详细处理日志
   - 任务完成通知

4. **管理生成的讲稿**
   - 在线预览和编辑（Markdown格式）
   - 导出多种格式（Markdown、HTML、TXT）
   - 版本管理和历史记录

### 高级功能

- **API配置管理**: 支持多个API配置切换
- **批量处理**: 同时处理多个PPT文件
- **实时监控**: WebSocket实时任务状态更新

## 🛠️ 开发调试

### 后端调试

```bash
# 查看后端日志
tail -f logs/app.log

# 数据库操作
sqlite3 data/ppt_generator.db

# 运行测试
python -m pytest tests/
```

### 前端调试

```bash
# 类型检查
npm run type-check

# 代码检查
npm run lint

# 构建检查
npm run build
```

### 常见问题解决

1. **端口占用**
   ```bash
   # 检查端口使用
   lsof -i :8000  # 后端端口
   lsof -i :3000  # 前端端口
   ```

2. **依赖安装失败**
   ```bash
   # 清理缓存
   pip cache purge
   npm cache clean --force
   ```

3. **数据库连接问题**
   - 检查 `data` 目录权限
   - 确认 SQLite 文件路径正确

## 🚨 注意事项

1. **API密钥安全**
   - 密钥在数据库中加密存储
   - 开发环境中妥善保管 .env 文件
   - 不要将密钥提交到版本控制

2. **文件存储**
   - 上传文件存储在 `uploads/` 目录
   - 定期清理临时文件
   - 监控磁盘空间使用

3. **开发性能**
   - PPT转换需要较多CPU资源
   - AI分析需要稳定网络连接
   - 建议监控系统资源使用

## 📞 开发支持

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用
   - 确认依赖是否正确安装
   - 查看错误日志定位问题

2. **API连接失败**
   - 检查API密钥是否正确
   - 验证网络连接
   - 确认API端点可访问

3. **文件上传失败**
   - 检查文件格式和大小
   - 确认存储空间充足
   - 查看后端错误日志

### 开发调试技巧

```bash
# 后端开发模式（自动重载）
python run.py --reload

# 前端开发模式（热更新）
npm run dev

# 同时启动前后端
# 可以使用 concurrently 工具
npm install -g concurrently
concurrently "cd backend && python run.py" "cd frontend && npm run dev"
```

## 🎉 开发完成

恭喜！您的PPT讲稿生成器Web版本地开发环境已成功搭建。

**访问地址**: http://localhost:3000  
**API文档**: http://localhost:8000/docs  
**健康检查**: http://localhost:8000/health

开始享受现代化的PPT讲稿生成体验吧！

## 📚 相关文档

- **API文档**: 访问后端 `/docs` 路径查看完整API文档
- **组件文档**: 前端组件使用 TypeScript 和详细注释
- **数据库模型**: 查看 `backend/app/models/` 目录下的模型定义