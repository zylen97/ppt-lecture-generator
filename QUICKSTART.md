# 快速开始指南

本指南帮助你在5分钟内开始使用PPT讲稿生成器。

## 1. 安装准备

### macOS用户
```bash
# 安装LibreOffice和poppler
brew install --cask libreoffice
brew install poppler

# 安装Python依赖
pip install -r requirements.txt
```

### Windows用户
1. 下载并安装 [LibreOffice](https://www.libreoffice.org/download/download/)
2. 下载并安装 [poppler for Windows](http://blog.alivate.com.au/poppler-windows/)
3. 将poppler的bin目录添加到系统PATH
4. 安装Python依赖：
```bash
pip install -r requirements.txt
```

## 2. 配置API

编辑 `config/config.ini`:
```ini
[api]
endpoint = https://api.openai.com/v1
api_key = sk-你的API密钥
model = gpt-4o
```

支持的API服务：
- OpenAI API
- Azure OpenAI
- 其他兼容的API服务

## 3. 第一次使用

### 方法1：使用GUI界面
```bash
python src/main.py --gui
```
1. 点击"选择文件"选择你的PPT
2. 点击"开始生成"
3. 等待生成完成

### 方法2：使用命令行
```bash
python src/main.py --cli --input your_presentation.pptx --output lecture.md
```

## 4. 查看结果

生成的讲稿将包含：
- 课程大纲和时间安排
- 每页幻灯片的详细讲稿
- 开场语和过渡语
- 互动建议和教学提示

## 5. 常见问题解决

### 问题：提示找不到soffice命令
**解决**：确保LibreOffice已安装，运行：
```bash
which soffice
```

### 问题：PDF转图片失败
**解决**：确保poppler已安装：
```bash
# macOS
brew list | grep poppler

# Ubuntu
dpkg -l | grep poppler
```

### 问题：API调用超时
**解决**：编辑config.ini增加超时时间：
```ini
[api]
timeout = 60
```

## 6. 进阶使用

### 批量处理多个PPT
```bash
for file in *.pptx; do
    python src/main.py --cli --input "$file" --output "${file%.pptx}_讲稿.md"
done
```

### 自定义讲稿风格
编辑 `config/config.ini`:
```ini
[lecture]
style = academic  # 可选: academic, casual, formal
include_interaction = True
include_examples = True
```

## 需要帮助？

- 查看完整文档：[README.md](README.md)
- 查看示例代码：[examples/example.py](examples/example.py)
- 提交问题：创建GitHub Issue

祝你使用愉快！🎉