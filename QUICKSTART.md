# 🚀 PPT讲稿生成器 - 快速入门指南

欢迎使用PPT讲稿生成器！这个工具可以帮助你将PPT演示文稿自动转换为详细的教学讲稿。

## 📋 5分钟快速开始

### 第1步：系统要求检查 ✅

确保你的系统满足以下要求：
- **Python 3.8+** (推荐3.9+)
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 第2步：安装系统依赖 🔧

<details>
<summary><strong>macOS 用户 (点击展开)</strong></summary>

```bash
# 安装Homebrew (如果还没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装LibreOffice和Poppler
brew install --cask libreoffice
brew install poppler

# 验证安装
which soffice && echo "✅ LibreOffice安装成功"
which pdftoppm && echo "✅ Poppler安装成功"
```
</details>

<details>
<summary><strong>Ubuntu/Debian 用户 (点击展开)</strong></summary>

```bash
# 更新包管理器
sudo apt update

# 安装依赖
sudo apt install -y libreoffice poppler-utils

# 验证安装
which soffice && echo "✅ LibreOffice安装成功"
which pdftoppm && echo "✅ Poppler安装成功"
```
</details>

<details>
<summary><strong>Windows 用户 (点击展开)</strong></summary>

1. **下载并安装LibreOffice**：
   - 访问 https://www.libreoffice.org/download/
   - 下载并安装最新版本

2. **安装Poppler**：
   - 下载 poppler for Windows: https://poppler.freedesktop.org/
   - 解压到 `C:\poppler` 
   - 将 `C:\poppler\bin` 添加到系统PATH

3. **验证安装**：
   ```cmd
   soffice --version
   pdftoppm -v
   ```
</details>

### 第3步：克隆并安装项目 📦

```bash
# 克隆项目
git clone https://github.com/zylen97/ppt-lecture-generator.git
cd ppt-lecture-generator

# 安装Python依赖
pip install -r requirements.txt

# 运行环境测试
python tests/test_cli.py
```

如果测试全部通过，你会看到：
```
🎉 所有测试通过！系统可以正常使用
```

### 第4步：配置API密钥 🔑

编辑 `config/config.ini` 文件：

```ini
[api]
endpoint = https://api.chatanywhere.tech/v1
api_key = your-api-key-here
model = gpt-4o
timeout = 30
max_retries = 3
```

> 💡 **获取API密钥**：
> - OpenAI官方: https://platform.openai.com/api-keys
> - 中转服务: https://api.chatanywhere.tech/ (推荐国内用户)

### 第5步：开始使用 🎯

#### 方式1：GUI界面（推荐新手）
```bash
python src/main.py --gui
# 或者
python start.py
```

#### 方式2：命令行（推荐高级用户）
```bash
python src/main.py --cli \
  --input "你的PPT文件.pptx" \
  --output "生成的讲稿.md" \
  --duration 90
```

## 📚 常用功能示例

### 示例1：生成30分钟课程讲稿
```bash
python src/main.py --cli \
  --input "第1章-概论.pptx" \
  --output "第1章-讲稿.md" \
  --duration 30 \
  --verbose
```

### 示例2：使用自定义API
```bash
python src/main.py --cli \
  --input presentation.pptx \
  --api-key sk-your-key \
  --api-base https://api.openai.com/v1 \
  --model gpt-4-vision-preview
```

### 示例3：批量处理多个文件
```bash
# 创建批处理脚本
for file in *.pptx; do
  echo "处理文件: $file"
  python src/main.py --cli \
    --input "$file" \
    --output "${file%.pptx}-讲稿.md" \
    --duration 60
done
```

## 🔍 处理过程说明

当你运行程序时，会看到类似的输出：

```
✅ PPT转换成功 (11张幻灯片)
🔍 正在分析幻灯片内容...
📝 正在生成讲稿...
✅ 讲稿生成成功: output/lecture.md

📊 生成统计:
  处理时间: 154.5秒
  处理幻灯片: 11张
  讲稿长度: 8,771字符
```

**处理流程**：
1. **PPT → PDF**: 使用LibreOffice转换
2. **PDF → 图片**: 使用PyMuPDF转换为高质量图片
3. **AI分析**: GPT-4o分析每张幻灯片内容
4. **讲稿生成**: 基于分析结果生成连贯讲稿
5. **格式化输出**: 生成Markdown格式的讲稿文件

## 🎛️ GUI界面功能介绍

启动GUI后，你会看到：

- **📁 文件选择区域**: 选择PPT文件
- **⚙️ API配置区域**: 设置API密钥和模型
- **🎛️ 生成参数**: 调整课程时长、语言等
- **📊 进度显示**: 实时显示处理进度
- **📝 结果预览**: 查看和导出生成的讲稿

## 🐛 常见问题快速解决

### Q1: 提示"找不到soffice命令"
```bash
# 检查LibreOffice安装
which soffice

# 如果没有输出，重新安装LibreOffice
# macOS: brew reinstall --cask libreoffice
# Ubuntu: sudo apt reinstall libreoffice
```

### Q2: API调用失败
```bash
# 测试网络连接
curl -X GET "https://api.chatanywhere.tech/v1/models" \
  -H "Authorization: Bearer your-api-key"

# 检查API密钥格式
# 正确格式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Q3: 图片转换失败
```bash
# 检查依赖
python -c "import fitz; print('✅ PyMuPDF正常')"
python -c "from PIL import Image; print('✅ Pillow正常')"

# 如果报错，重新安装
pip install --upgrade pymupdf pillow
```

### Q4: 生成的讲稿质量不佳
- ✅ 确保PPT内容清晰，文字可读
- ✅ 避免过度复杂的图表和动画
- ✅ 尝试使用更强大的模型（gpt-4o）
- ✅ 调整课程时长参数

## 📁 输出文件说明

生成的讲稿文件包含：

```markdown
# 课程名称 - 课程讲稿

**生成时间**: 2025-07-15 08:33:25
**课程时长**: 30分钟
**幻灯片数量**: 11张

## 📋 课程大纲
(自动生成的章节列表)

## 📖 详细讲稿
### 第1张 - 标题
**建议时长**: X分钟
(详细的讲解内容)

## 💡 教学建议
(课前准备、课堂管理等建议)
```

## 🚀 进阶技巧

### 1. 配置文件优化
```ini
[lecture]
default_duration = 90           # 调整默认时长
include_interaction = false     # 纯讲授模式，无互动环节
include_examples = true         # 包含案例说明
no_questions = true            # 不包含提问
no_blackboard = true           # 不包含板书
time_per_slide = 2.5           # 每张幻灯片基础时间
```

### 2. 命令行别名设置
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias ppt-gen='python /path/to/ppt-lecture-generator/src/main.py'

# 使用
ppt-gen --cli --input lecture.pptx --duration 60
```

### 3. 查看详细日志
```bash
# 查看实时日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 📞 获取帮助

- 🐛 **Bug报告**: [GitHub Issues](https://github.com/zylen97/ppt-lecture-generator/issues)
- 💬 **功能建议**: [GitHub Discussions](https://github.com/zylen97/ppt-lecture-generator/discussions)
- 📖 **详细文档**: [项目Wiki](https://github.com/zylen97/ppt-lecture-generator/wiki)

---

🎉 **恭喜！** 你已经可以开始使用PPT讲稿生成器了！

**下一步建议**：
1. 尝试用一个简单的PPT文件测试
2. 根据生成结果调整配置参数
3. 探索更多高级功能

💡 **小贴士**: 第一次使用建议选择内容相对简单、幻灯片数量较少的PPT文件进行测试。