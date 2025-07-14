# PPT讲稿生成器

一个基于AI的PPT讲稿自动生成工具，支持图片内容分析和连贯讲稿生成。

## 🌟 项目特色

- 📊 **智能PPT分析** - 提取文本内容并转换为高质量图片
- 🤖 **AI视觉理解** - 使用GPT-4 Vision等模型分析图片内容
- 📝 **连贯讲稿生成** - 基于上下文管理生成流畅的教学讲稿
- 🎨 **GUI友好界面** - 简单易用的图形界面
- ⚙️ **灵活配置** - 支持自定义API端点和参数
- 🔧 **模块化设计** - 工程化的代码结构，易于扩展

## 🏗️ 项目架构

```
ppt-lecture-generator/
├── src/                    # 源代码
│   ├── config/            # 配置管理
│   ├── core/              # 核心业务逻辑
│   ├── gui/               # GUI界面
│   └── utils/             # 工具函数
├── tests/                 # 单元测试
├── docs/                  # 文档
└── resources/             # 资源文件
```

## 🚀 已实现功能

### ✅ 核心模块

1. **配置管理模块** (`src/config/`)
   - 设置文件读写和验证
   - 支持多种配置格式
   - 自动备份和恢复

2. **PPT处理模块** (`src/core/ppt_processor.py`)
   - 支持PPTX文件读取和解析
   - 文本内容提取
   - 图片转换（Spire.Presentation + pdf2image）
   - 多媒体元素统计

3. **AI API调用模块** (`src/core/ai_client.py`)
   - 支持OpenAI API和自定义端点
   - 图片编码和视觉分析
   - 错误处理和重试机制
   - 异步调用支持

4. **上下文管理模块** (`src/core/context_manager.py`)
   - 跟踪讲稿生成上下文
   - 概念关系管理
   - 教学进度控制
   - 互动点和示例点计算

5. **讲稿生成模块** (`src/core/script_generator.py`)
   - 整合所有模块功能
   - 批量处理和进度报告
   - 结构化讲稿输出
   - 统计信息收集

6. **工具函数模块** (`src/utils/`)
   - 日志系统（多级别、文件轮转）
   - 文件操作工具
   - 输入验证器
   - 图片处理工具

## 📋 待实现功能

- [ ] GUI界面模块
- [ ] 主程序入口
- [ ] 单元测试
- [ ] 部署脚本

## 🔧 技术栈

- **核心语言**: Python 3.8+
- **GUI框架**: Tkinter
- **AI API**: OpenAI GPT-4 Vision
- **PPT处理**: python-pptx, spire.presentation
- **图片处理**: Pillow, pdf2image
- **HTTP客户端**: requests, aiohttp
- **日志系统**: logging, loguru
- **测试框架**: pytest

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 使用示例

```python
from src.core.script_generator import ScriptGenerator

# 初始化生成器
generator = ScriptGenerator(
    api_key="your-api-key",
    api_base="https://api.chatanywhere.tech",
    model="gpt-4-vision-preview"
)

# 生成讲稿
success, result = generator.generate_from_ppt("presentation.pptx")
if success:
    print(f"讲稿已生成: {result}")
else:
    print(f"生成失败: {result}")
```

## 📊 功能特性

### 智能分析
- 自动识别幻灯片类型（标题页、章节页、内容页、总结页）
- 提取文本内容和多媒体元素统计
- AI视觉分析图片、图表和复杂布局

### 连贯生成
- 基于上下文的前向引用
- 概念关系追踪
- 教学进度管理
- 自动时间分配

### 专业输出
- 结构化的Markdown格式
- 教学建议和互动设计
- 课程大纲和时间安排
- 完整的统计信息

### 灵活配置
- 支持多种API端点
- 可自定义生成参数
- 配置文件管理
- 错误处理和重试

## 🎯 设计原则

1. **模块化设计** - 每个模块职责单一，接口清晰
2. **可扩展性** - 支持新的PPT处理库和AI模型
3. **健壮性** - 完善的错误处理和日志记录
4. **易用性** - 简单的API和友好的用户界面
5. **性能优化** - 异步处理和批量操作

## 🔍 代码质量

- 类型注解和文档字符串
- 统一的错误处理机制
- 完善的日志记录
- 配置验证和安全检查
- 资源管理和清理

## 📈 性能特性

- 支持大型PPT文件处理
- 批量幻灯片分析
- 智能重试和错误恢复
- 内存优化和缓存机制
- 异步API调用

## 🛡️ 安全考虑

- API密钥安全存储
- 输入验证和过滤
- 文件路径安全检查
- 临时文件清理
- 错误信息脱敏

## 📝 开发状态

当前版本：**v1.0.0-alpha**

核心功能已完成，可以进行基本的PPT讲稿生成。GUI界面和完整的用户体验正在开发中。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**开发团队**: PPT Lecture Generator Team  
**技术支持**: support@ppt-lecture-generator.com  
**项目地址**: https://github.com/your-username/ppt-lecture-generator