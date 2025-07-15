# PPT讲稿生成器 (PPT Lecture Script Generator)

🎯 **一个基于AI的PPT讲稿自动生成工具，使用视觉AI模型分析PPT内容并生成高质量的教学讲稿。**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ 功能特点

- 🎯 **智能PPT分析**: 自动提取PPT中的文本、图表、要点等内容
- 🖼️ **视觉AI理解**: 将PPT转换为高质量图片，使用GPT-4o等视觉模型深度分析
- 📝 **连贯讲稿生成**: 基于上下文管理生成流畅自然的教学讲稿
- ⏱️ **智能时间分配**: 根据内容复杂度和课程时长自动分配讲解时间
- 🎨 **双模式支持**: 提供图形界面(GUI)和命令行(CLI)两种使用方式
- 🔄 **完整转换流程**: PPT → PDF → 图片 → AI分析 → 讲稿生成
- 🌐 **多模型支持**: 支持OpenAI GPT-4o、Claude等多种AI模型
- 📊 **详细日志**: 完整的处理日志和错误追踪

## 🚀 快速开始

### 系统要求

- **Python**: 3.8+ 
- **LibreOffice**: 用于PPT转PDF转换
- **系统依赖**: 图片处理库

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/zylen97/ppt-lecture-generator.git
cd ppt-lecture-generator
```

2. **安装系统依赖**
```bash
# macOS
brew install --cask libreoffice
brew install poppler

# Ubuntu/Debian
sudo apt update
sudo apt install libreoffice poppler-utils

# Windows (手动安装)
# 下载并安装 LibreOffice: https://www.libreoffice.org/download/
# 下载并安装 poppler: https://poppler.freedesktop.org/
```

3. **安装Python依赖**
```bash
pip install -r requirements.txt
```

4. **配置API密钥**

编辑 `config/config.ini` 文件：
```ini
[api]
endpoint = https://api.chatanywhere.tech/v1
api_key = your-api-key-here
model = gpt-4o
timeout = 30
max_retries = 3
```

### 快速测试

运行基础功能测试：
```bash
# 测试系统环境和依赖
python tests/test_cli.py

# 测试GUI界面（可选）
python tests/test_gui.py
```

## 📖 使用方法

### 🖥️ GUI模式（推荐）

```bash
python src/main.py --gui
# 或者
python start.py
```

GUI界面功能：
- 📁 文件选择和预览
- ⚙️ API配置管理
- 🎛️ 生成参数设置
- 📊 实时进度显示
- 📝 结果预览和导出

### 💻 命令行模式

```bash
# 基本使用
python src/main.py --cli --input presentation.pptx --output lecture.md

# 完整参数示例
python src/main.py --cli \
  --input presentation.pptx \
  --output lecture.md \
  --api-key sk-your-key \
  --api-base https://api.openai.com/v1 \
  --model gpt-4o \
  --duration 90 \
  --language zh-CN \
  --verbose
```

### 📋 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--gui` | - | 启动图形界面 | - |
| `--cli` | - | 使用命令行模式 | - |
| `--input` | `-i` | 输入PPT文件路径 | - |
| `--output` | `-o` | 输出讲稿文件路径 | - |
| `--api-key` | `-k` | API密钥 | 配置文件 |
| `--api-base` | `-b` | API基础URL | 配置文件 |
| `--model` | `-m` | AI模型名称 | gpt-4o |
| `--duration` | `-d` | 课程时长（分钟） | 90 |
| `--language` | `-l` | 语言设置 | zh-CN |
| `--verbose` | `-v` | 显示详细日志 | False |
| `--quiet` | `-q` | 静默模式 | False |

## 🏗️ 项目结构

```
ppt-lecture-generator/
├── 📁 src/                     # 源代码
│   ├── 🎯 main.py              # 主程序入口
│   ├── 📁 core/                # 核心功能模块
│   │   ├── ai_client.py        # AI客户端封装
│   │   ├── ppt_processor.py    # PPT处理和转换
│   │   ├── script_generator.py # 讲稿生成逻辑
│   │   └── context_manager.py  # 上下文管理
│   ├── 📁 gui/                 # GUI界面
│   │   ├── main_window.py      # 主窗口
│   │   └── 📁 components/      # UI组件
│   ├── 📁 utils/               # 工具模块
│   │   ├── ppt_converter.py    # PPT转换器
│   │   ├── image_utils.py      # 图片处理
│   │   ├── file_utils.py       # 文件操作
│   │   ├── validators.py       # 输入验证
│   │   └── logger.py           # 日志管理
│   └── 📁 config/              # 配置管理
│       ├── settings.py         # 设置管理
│       ├── constants.py        # 常量定义
│       └── default_config.json # 默认配置
├── 📁 tests/                   # 测试代码
│   ├── test_cli.py             # CLI功能测试
│   ├── test_gui.py             # GUI测试
│   └── test_validators.py      # 验证器测试
├── 📁 config/                  # 配置文件
│   └── config.ini              # 用户配置
├── 📁 examples/                # 示例文件
│   └── example.py              # 使用示例
├── 📁 scripts/                 # 构建脚本
│   ├── build.py                # 构建脚本
│   └── install.py              # 安装脚本
├── 📁 output/                  # 输出目录
├── 📁 logs/                    # 日志文件
├── 📁 temp/                    # 临时文件
├── 📄 requirements.txt         # Python依赖
├── 📄 setup.py                 # 安装脚本
├── 📄 start.py                 # 快速启动脚本
└── 📄 QUICKSTART.md            # 快速入门指南
```

## ⚙️ 配置说明

### API配置
```ini
[api]
endpoint = https://api.chatanywhere.tech/v1  # API端点
api_key = your-api-key-here                  # API密钥
model = gpt-4o                               # 模型名称
timeout = 30                                 # 超时时间(秒)
max_retries = 3                              # 最大重试次数
```

### PPT处理配置
```ini
[ppt]
output_format = png              # 输出图片格式
dpi = 300                       # 图片DPI
enable_libreoffice = true       # 启用LibreOffice转换
conversion_timeout = 60         # 转换超时时间
```

### 讲稿生成配置
```ini
[lecture]
default_duration = 90           # 默认课程时长(分钟)
language = zh-CN               # 语言设置
include_interaction = true     # 包含互动环节
include_examples = true        # 包含示例说明
time_per_slide = 2.0          # 每张幻灯片基础时间(分钟)
```

## 🔍 使用示例

### 示例1：基础使用
```bash
# 生成90分钟的课程讲稿
python src/main.py --cli \
  --input "第1章 概论.pptx" \
  --output "第1章讲稿.md" \
  --duration 90
```

### 示例2：自定义API
```bash
# 使用自定义API配置
python src/main.py --cli \
  --input presentation.pptx \
  --api-key sk-your-custom-key \
  --api-base https://your-api-endpoint.com/v1 \
  --model gpt-4-vision-preview
```

### 示例3：批量处理
```bash
# 处理多个文件（需要编写简单脚本）
for file in *.pptx; do
  python src/main.py --cli --input "$file" --output "${file%.pptx}.md"
done
```

## 🛠️ 开发指南

### 本地开发设置
```bash
# 克隆项目
git clone https://github.com/zylen97/ppt-lecture-generator.git
cd ppt-lecture-generator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
```

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python tests/test_cli.py
```

### 代码格式化
```bash
# 使用black格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/
```

## 🐛 故障排除

### 常见问题

**Q: PPT转换失败，提示找不到LibreOffice？**
```bash
# 检查LibreOffice安装
which soffice || which libreoffice

# macOS重新安装
brew reinstall --cask libreoffice

# 手动指定路径（如果需要）
export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"
```

**Q: 图片转换失败？**
```bash
# 检查依赖
python -c "import fitz; print('PyMuPDF OK')"
python -c "from PIL import Image; print('Pillow OK')"

# 重新安装依赖
pip install --upgrade pymupdf pillow
```

**Q: API调用超时或失败？**
- 检查网络连接和API密钥
- 确认API端点是否正确
- 查看 `logs/error.log` 了解详细错误信息

**Q: 生成的讲稿内容质量不佳？**
- 确保PPT内容清晰，避免过于复杂的图表
- 尝试调整课程时长参数
- 使用更强大的AI模型（如GPT-4o）

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. 🍴 Fork本项目
2. 🌟 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 💝 提交修改 (`git commit -m 'Add some AmazingFeature'`)
4. 📤 推送到分支 (`git push origin feature/AmazingFeature`)
5. 🔄 创建Pull Request

### 贡献类型
- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🎨 界面优化
- 🧪 测试用例
- 🌐 国际化支持

## 📋 开发路线图

- [ ] 🎯 支持更多PPT格式（.ppt, .odp等）
- [ ] 🌐 多语言界面支持
- [ ] 🔌 插件系统架构
- [ ] 📊 批量处理功能
- [ ] 🎨 自定义讲稿模板
- [ ] 📱 Web版本开发
- [ ] 🔊 语音合成集成
- [ ] 📈 使用统计和分析

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) - 查看LICENSE文件了解详情。

## 🙏 致谢

- 🤖 [OpenAI](https://openai.com) - 提供强大的GPT视觉模型
- 📄 [LibreOffice](https://www.libreoffice.org/) - PPT转换功能支持
- 🖼️ [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理库
- 🎨 [Pillow](https://pillow.readthedocs.io/) - 图像处理库
- 💻 所有贡献者和用户的支持

## 📞 联系方式

- 📧 **问题反馈**: [提交Issue](https://github.com/zylen97/ppt-lecture-generator/issues)
- 💬 **功能建议**: [讨论区](https://github.com/zylen97/ppt-lecture-generator/discussions)
- 📖 **文档**: [Wiki](https://github.com/zylen97/ppt-lecture-generator/wiki)

---

⭐ 如果这个项目对你有帮助，请给它一个Star！

🚀 **立即开始**: `python src/main.py --gui`