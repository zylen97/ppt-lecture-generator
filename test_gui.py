#!/usr/bin/env python3
"""
简单的GUI测试脚本
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_gui():
    """测试基本GUI功能"""
    root = tk.Tk()
    root.title("PPT讲稿生成器 - 测试版")
    root.geometry("800x600")
    
    # 创建基本界面
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill='both', expand=True)
    
    # 标题
    title_label = ttk.Label(
        main_frame,
        text="🎯 PPT讲稿生成器",
        font=('Arial', 16, 'bold')
    )
    title_label.pack(pady=10)
    
    # API配置区域
    config_frame = ttk.LabelFrame(main_frame, text="🔧 API配置", padding="10")
    config_frame.pack(fill='x', pady=10)
    
    # API地址
    ttk.Label(config_frame, text="API地址:").grid(row=0, column=0, sticky='w', pady=2)
    api_endpoint = ttk.Entry(config_frame, width=50)
    api_endpoint.insert(0, "https://api.chatanywhere.tech/v1")
    api_endpoint.grid(row=0, column=1, sticky='ew', padx=(5, 0), pady=2)
    
    # API密钥
    ttk.Label(config_frame, text="API密钥:").grid(row=1, column=0, sticky='w', pady=2)
    api_key = ttk.Entry(config_frame, width=50, show="*")
    api_key.insert(0, "sk-LrOwl2ZEbKhZxW4s27EyGdjwnpZ1nDwjVRJk546lSspxHymY")
    api_key.grid(row=1, column=1, sticky='ew', padx=(5, 0), pady=2)
    
    # 模型选择
    ttk.Label(config_frame, text="模型:").grid(row=2, column=0, sticky='w', pady=2)
    model_var = tk.StringVar(value="gpt-4o")
    model_combo = ttk.Combobox(
        config_frame, 
        textvariable=model_var,
        values=['gpt-4o', 'gpt-4-vision-preview', 'gpt-3.5-turbo'],
        state='readonly',
        width=47
    )
    model_combo.grid(row=2, column=1, sticky='ew', padx=(5, 0), pady=2)
    
    config_frame.columnconfigure(1, weight=1)
    
    # 文件选择区域
    file_frame = ttk.LabelFrame(main_frame, text="📁 文件选择", padding="10")
    file_frame.pack(fill='x', pady=10)
    
    selected_file = tk.StringVar(value="未选择文件")
    
    def select_file():
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="选择PPT文件",
            filetypes=[
                ("PowerPoint文件", "*.ppt *.pptx"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            selected_file.set(filename)
            status_label.config(text=f"已选择: {Path(filename).name}", foreground="green")
    
    ttk.Button(file_frame, text="选择PPT文件", command=select_file).pack(side='left')
    ttk.Label(file_frame, textvariable=selected_file).pack(side='left', padx=(10, 0))
    
    # 操作按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x', pady=20)
    
    def test_connection():
        try:
            import requests
            endpoint = api_endpoint.get()
            key = api_key.get()
            
            if not endpoint or not key:
                messagebox.showerror("错误", "请填写API地址和密钥")
                return
            
            # 简单的连接测试
            headers = {
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json'
            }
            
            # 测试模型列表接口
            response = requests.get(f"{endpoint}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                messagebox.showinfo("成功", "✅ API连接测试成功！")
                status_label.config(text="✅ API连接正常", foreground="green")
            else:
                messagebox.showerror("错误", f"API连接失败: {response.status_code}")
                status_label.config(text="❌ API连接失败", foreground="red")
                
        except Exception as e:
            messagebox.showerror("错误", f"连接测试失败: {str(e)}")
            status_label.config(text="❌ 连接测试失败", foreground="red")
    
    def start_generation():
        file_path = selected_file.get()
        if file_path == "未选择文件":
            messagebox.showerror("错误", "请先选择PPT文件")
            return
        
        endpoint = api_endpoint.get()
        key = api_key.get()
        model = model_var.get()
        
        if not endpoint or not key:
            messagebox.showerror("错误", "请配置API设置")
            return
        
        # 这里可以调用实际的生成逻辑
        messagebox.showinfo("提示", f"开始生成讲稿\\n文件: {Path(file_path).name}\\n模型: {model}")
        status_label.config(text="🔄 准备生成讲稿...", foreground="blue")
    
    ttk.Button(button_frame, text="🔗 测试连接", command=test_connection).pack(side='left', padx=(0, 10))
    ttk.Button(button_frame, text="🚀 生成讲稿", command=start_generation).pack(side='left')
    
    # 状态栏
    status_label = ttk.Label(main_frame, text="就绪", foreground="blue")
    status_label.pack(pady=10)
    
    # 关于信息
    about_text = """
🎯 PPT讲稿生成器 v1.0.0

✨ 功能特性：
• 智能PPT内容分析
• AI视觉理解和处理  
• 连贯讲稿自动生成
• 支持自定义API配置

📝 使用步骤：
1. 配置API设置并测试连接
2. 选择要处理的PPT文件
3. 点击生成讲稿开始处理

💡 提示：确保API密钥有效且模型支持视觉分析
    """
    
    about_frame = ttk.LabelFrame(main_frame, text="ℹ️ 使用说明", padding="10")
    about_frame.pack(fill='both', expand=True, pady=10)
    
    about_label = ttk.Label(about_frame, text=about_text, justify='left')
    about_label.pack(fill='both', expand=True)
    
    return root

def main():
    """主函数"""
    try:
        # 检查tkinter
        import tkinter as tk
        print("✅ Tkinter可用")
        
        # 检查其他依赖
        import requests
        print("✅ requests可用")
        
        try:
            from pptx import Presentation
            print("✅ python-pptx可用")
        except ImportError:
            print("⚠️ python-pptx不可用，但不影响GUI测试")
        
        # 创建并运行GUI
        print("🚀 启动GUI测试...")
        root = test_basic_gui()
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ 依赖检查失败: {e}")
        return 1
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())