# PPT讲稿生成器 (PPT Lecture Script Generator)

一个基于AI的PPT讲稿自动生成工具，使用视觉AI模型分析PPT内容并生成高质量的教学讲稿。

## ✨ 功能特点

- 🎯 **智能PPT分析**: 自动提取PPT中的文本、标题、要点等内容
- 🖼️ **视觉AI理解**: 将PPT转换为高质量图片，使用GPT-4等视觉模型深度分析
- 📝 **连贯讲稿生成**: 基于上下文管理生成流畅自然的教学讲稿
- ⏱️ **智能时间分配**: 根据内容复杂度自动分配每页的讲解时间
- 🎨 **双模式支持**: 提供图形界面(GUI)和命令行(CLI)两种使用方式
- 🔄 **多格式转换**: PPT → PDF → 图片的完整转换流程

## 🚀 快速开始

### 系统要求

- Python 3.8+
- LibreOffice (用于PPT转PDF)
- poppler-utils (用于PDF转图片)

### 安装依赖

1. 安装系统依赖:
```bash
# macOS
brew install --cask libreoffice
brew install poppler

# Ubuntu/Debian
sudo apt update
sudo apt install libreoffice poppler-utils

# Windows
# 请手动安装LibreOffice和poppler
```

2. 安装Python依赖:
```bash
pip install -r requirements.txt
```

### 配置API

编辑 `config/config.ini` 文件，添加你的API配置：
```ini
[api]
endpoint = https://api.openai.com/v1
api_key = your-api-key-here
model = gpt-4o
```

## 📖 使用方法

### GUI模式
```bash
python src/main.py --gui
```

### 命令行模式
```bash
# 基本使用
python src/main.py --cli --input presentation.pptx --output lecture.md

# 指定课程时长
python src/main.py --cli --input presentation.pptx --duration 120

# 使用自定义API配置
python src/main.py --cli --input presentation.pptx --api-key sk-xxx --api-base https://api.example.com
```

### 命令行参数说明
- `--input, -i`: 输入PPT文件路径
- `--output, -o`: 输出讲稿文件路径
- `--api-key, -k`: API密钥
- `--api-base, -b`: API基础URL
- `--model, -m`: 使用的AI模型
- `--duration, -d`: 课程时长（分钟，默认90）
- `--language, -l`: 语言设置（默认zh-CN）
- `--verbose, -v`: 显示详细日志

## 🏗️ 项目结构

```
ppt-lecture-generator/
├── src/                    # 源代码
│   ├── core/              # 核心功能模块
│   │   ├── ai_client.py   # AI客户端
│   │   ├── ppt_processor.py # PPT处理器
│   │   ├── script_generator.py # 讲稿生成器
│   │   └── context_manager.py # 上下文管理
│   ├── gui/               # GUI界面
│   │   ├── main_window.py # 主窗口
│   │   └── components/    # UI组件
│   ├── utils/             # 工具模块
│   │   ├── ppt_converter.py # PPT转换器
│   │   ├── image_utils.py # 图片处理
│   │   └── validators.py  # 验证器
│   └── config/            # 配置管理
├── config/                # 配置文件
├── examples/              # 示例文件
├── tests/                 # 测试代码
└── requirements.txt       # 依赖列表
```

## 🔧 高级配置

### 配置文件说明

`config/config.ini` 包含以下配置项：

```ini
[api]
endpoint = API端点URL
api_key = API密钥
model = 模型名称
timeout = 超时时间(秒)
max_retries = 最大重试次数

[ppt]
output_format = 图片格式(png/jpg)
dpi = 图片DPI(默认300)
quality = 图片质量(1-100)

[lecture]
default_duration = 默认课程时长(分钟)
language = 语言设置
style = 讲稿风格
include_interaction = 是否包含互动环节
include_examples = 是否包含示例
```

## 🐛 常见问题

### Q: PPT转换失败怎么办？
A: 请确保已安装LibreOffice，并且`soffice`命令可用。可以运行`which soffice`检查。

### Q: 图片生成失败？
A: 请确保已安装poppler-utils。在macOS上运行`brew install poppler`安装。

### Q: API调用失败？
A: 请检查API密钥是否正确，以及网络连接是否正常。

### Q: 中文显示有问题？
A: 确保系统安装了中文字体，特别是在Linux系统上。

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 感谢OpenAI提供强大的AI模型
- 感谢LibreOffice项目提供PPT转换功能
- 感谢所有贡献者的支持

---

如有问题或建议，请提交Issue或联系作者。