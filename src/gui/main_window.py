"""
主窗口模块

应用程序的主界面，整合所有GUI组件。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import Settings
from src.core.script_generator import ScriptGenerator
from src.core.ai_client import AIClient
from src.utils.logger import get_logger
from src.gui.components.config_panel import ConfigPanel
from src.gui.components.file_panel import FilePanel
from src.gui.components.control_panel import ControlPanel
from src.gui.components.preview_panel import PreviewPanel


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.logger = get_logger()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("PPT讲稿生成器 v1.0.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # 设置窗口图标（如果有的话）
        try:
            # 这里可以设置应用程序图标
            pass
        except:
            pass
        
        # 初始化组件
        self.settings = Settings()
        self.script_generator: Optional[ScriptGenerator] = None
        self.current_file: Optional[str] = None
        
        # 创建GUI组件
        self._create_widgets()
        
        # 设置回调
        self._setup_callbacks()
        
        # 加载配置
        self._load_initial_config()
        
        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.logger.info("主窗口初始化完成")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建主要内容区域
        self._create_main_content()
        
        # 创建状态栏
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开PPT...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="保存讲稿", command=self._save_script, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为...", command=self._save_script_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing, accelerator="Ctrl+Q")
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="复制", command=self._copy_content, accelerator="Ctrl+C")
        edit_menu.add_command(label="全选", command=self._select_all, accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self._find_text, accelerator="Ctrl+F")
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="测试API连接", command=self._test_api_connection)
        tools_menu.add_command(label="清理临时文件", command=self._clean_temp_files)
        tools_menu.add_separator()
        tools_menu.add_command(label="设置", command=self._open_settings)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="快捷键", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="关于", command=self._show_about)
        
        # 绑定快捷键
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-s>', lambda e: self._save_script())
        self.root.bind('<Control-Shift-S>', lambda e: self._save_script_as())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<Control-c>', lambda e: self._copy_content())
        self.root.bind('<Control-a>', lambda e: self._select_all())
        self.root.bind('<Control-f>', lambda e: self._find_text())
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side='top', fill='x', padx=5, pady=5)
        
        # 文件操作按钮
        ttk.Button(
            toolbar,
            text="📁 打开",
            command=self._open_file
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            toolbar,
            text="💾 保存",
            command=self._save_script
        ).pack(side='left', padx=(0, 5))
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
        
        # 处理按钮
        ttk.Button(
            toolbar,
            text="🔄 生成讲稿",
            command=self._start_generation
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            toolbar,
            text="⏹️ 停止",
            command=self._stop_generation
        ).pack(side='left', padx=(0, 5))
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
        
        # 设置按钮
        ttk.Button(
            toolbar,
            text="⚙️ 设置",
            command=self._open_settings
        ).pack(side='left', padx=(0, 5))
        
        # 帮助按钮
        ttk.Button(
            toolbar,
            text="❓ 帮助",
            command=self._show_help
        ).pack(side='right')
    
    def _create_main_content(self):
        """创建主要内容区域"""
        # 创建主要容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建左侧面板
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        
        # 配置面板
        self.config_panel = ConfigPanel(left_panel, self.settings)
        self.config_panel.pack(fill='x', pady=(0, 10))
        
        # 文件面板
        self.file_panel = FilePanel(left_panel)
        self.file_panel.pack(fill='x', pady=(0, 10))
        
        # 控制面板
        self.control_panel = ControlPanel(left_panel)
        self.control_panel.pack(fill='both', expand=True)
        
        # 创建右侧面板（预览区域）
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # 预览面板
        self.preview_panel = PreviewPanel(right_panel)
        self.preview_panel.pack(fill='both', expand=True)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x')
        
        # 状态标签
        self.status_label = ttk.Label(
            self.status_bar,
            text="就绪",
            relief='sunken',
            anchor='w'
        )
        self.status_label.pack(side='left', fill='x', expand=True, padx=2, pady=2)
        
        # 进度信息
        self.progress_info = ttk.Label(
            self.status_bar,
            text="",
            relief='sunken',
            anchor='e'
        )
        self.progress_info.pack(side='right', padx=2, pady=2)
    
    def _setup_callbacks(self):
        """设置回调函数"""
        # 配置面板回调
        self.config_panel.set_config_change_callback(self._on_config_change)
        self.config_panel.set_test_connection_callback(self._test_api_connection)
        
        # 文件面板回调
        self.file_panel.set_file_selected_callback(self._on_file_selected)
        self.file_panel.set_file_preview_callback(self._on_file_preview)
        
        # 控制面板回调
        self.control_panel.set_start_processing_callback(self._on_start_processing)
        self.control_panel.set_stop_processing_callback(self._on_stop_processing)
        self.control_panel.set_step_processing_callback(self._on_step_processing)
        
        # 预览面板回调
        self.preview_panel.set_content_change_callback(self._on_content_change)
        self.preview_panel.set_save_content_callback(self._on_save_content)
    
    def _load_initial_config(self):
        """加载初始配置"""
        try:
            # 从设置中加载配置
            config = {
                'api': self.settings.get_section('api'),
                'lecture': self.settings.get_section('lecture')
            }
            
            self.config_panel.set_config(config)
            self._update_ui_state()
            
            self.logger.info("初始配置加载完成")
        except Exception as e:
            self.logger.error(f"加载初始配置失败: {e}")
            self.status_label.config(text="配置加载失败")
    
    def _on_config_change(self, config: Dict[str, Any]):
        """配置变化回调"""
        self._update_ui_state()
        self.logger.debug("配置已更新")
    
    def _test_api_connection(self, config: Dict[str, Any] = None) -> tuple[bool, str]:
        """测试API连接"""
        if config is None:
            config = self.config_panel.get_config()
        
        try:
            api_config = config.get('api', {})
            
            # 创建临时AI客户端
            client = AIClient(
                api_key=api_config.get('api_key', ''),
                api_base=api_config.get('endpoint', ''),
                model=api_config.get('model', '')
            )
            
            # 测试连接
            success, message = client.test_connection()
            client.close()
            
            if success:
                self.status_label.config(text="✅ API连接成功")
            else:
                self.status_label.config(text=f"❌ API连接失败: {message}")
            
            return success, message
            
        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.status_label.config(text=f"❌ {error_msg}")
            return False, error_msg
    
    def _on_file_selected(self, filename: str, file_info: dict):
        """文件选择回调"""
        self.current_file = filename
        
        if filename:
            self.status_label.config(text=f"已选择文件: {Path(filename).name}")
            
            # 尝试获取幻灯片数量
            try:
                # 这里可以添加快速获取幻灯片数量的逻辑
                self.file_panel.update_slides_count(0)  # 占位符
            except Exception as e:
                self.logger.error(f"获取幻灯片数量失败: {e}")
        else:
            self.status_label.config(text="就绪")
            self.preview_panel.clear_content()
        
        self._update_ui_state()
    
    def _on_file_preview(self, filename: str):
        """文件预览回调"""
        # 使用系统默认程序打开文件
        self.logger.info(f"预览文件: {filename}")
    
    def _on_start_processing(self) -> bool:
        """开始处理回调"""
        try:
            if not self.current_file:
                messagebox.showerror("错误", "请先选择PPT文件")
                return False
            
            # 获取配置
            config = self.config_panel.get_config()
            
            # 创建脚本生成器
            api_config = config.get('api', {})
            self.script_generator = ScriptGenerator(
                api_key=api_config.get('api_key', ''),
                api_base=api_config.get('endpoint', ''),
                model=api_config.get('model', '')
            )
            
            # 设置生成配置
            lecture_config = config.get('lecture', {})
            self.script_generator.set_generation_config(lecture_config)
            
            # 设置进度回调
            self.script_generator.set_progress_callback(self._on_progress_update)
            
            # 开始生成
            self.status_label.config(text="正在生成讲稿...")
            
            def generate_thread():
                try:
                    success, result = self.script_generator.generate_from_ppt(self.current_file)
                    
                    # 更新UI（在主线程中）
                    self.root.after(0, self._on_generation_complete, success, result)
                    
                except Exception as e:
                    self.root.after(0, self._on_generation_error, str(e))
            
            # 启动生成线程
            threading.Thread(target=generate_thread, daemon=True).start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"开始处理失败: {e}")
            messagebox.showerror("错误", f"开始处理失败: {e}")
            return False
    
    def _on_stop_processing(self):
        """停止处理回调"""
        if self.script_generator:
            # 这里可以添加停止生成的逻辑
            self.logger.info("用户请求停止处理")
            self.status_label.config(text="处理已停止")
    
    def _on_step_processing(self, step: str) -> bool:
        """分步处理回调"""
        # 这里可以添加分步处理的逻辑
        self.logger.info(f"执行步骤: {step}")
        return True
    
    def _on_progress_update(self, current: int, total: int, message: str):
        """进度更新回调"""
        self.control_panel.set_progress(current, total, message)
        self.progress_info.config(text=f"{current}/{total}")
        
        # 更新状态统计
        if self.script_generator:
            stats = self.script_generator.get_generation_stats()
            self.control_panel.update_stats(stats)
    
    def _on_generation_complete(self, success: bool, result: str):
        """生成完成回调"""
        if success:
            self.status_label.config(text="✅ 讲稿生成完成")
            
            # 读取生成的讲稿
            try:
                from src.utils.file_utils import FileUtils
                content = FileUtils.read_text_file(result)
                
                # 显示在预览面板
                filename = Path(result).name
                self.preview_panel.set_content(content, filename)
                self.preview_panel.set_output_file(result)
                
                # 更新统计信息
                if self.script_generator:
                    stats = self.script_generator.get_generation_stats()
                    self.control_panel.update_stats(stats)
                
                messagebox.showinfo("成功", f"讲稿已生成并保存到:\\n{result}")
                
            except Exception as e:
                self.logger.error(f"读取生成的讲稿失败: {e}")
                messagebox.showerror("错误", f"读取生成的讲稿失败: {e}")
        else:
            self.status_label.config(text="❌ 讲稿生成失败")
            messagebox.showerror("错误", f"讲稿生成失败:\\n{result}")
    
    def _on_generation_error(self, error: str):
        """生成错误回调"""
        self.status_label.config(text="❌ 生成过程中发生错误")
        messagebox.showerror("错误", f"生成过程中发生错误:\\n{error}")
    
    def _on_content_change(self, content: str):
        """内容变化回调"""
        # 这里可以添加内容变化的处理逻辑
        pass
    
    def _on_save_content(self, filename: str, content: str):
        """保存内容回调"""
        self.status_label.config(text=f"✅ 已保存: {Path(filename).name}")
        self.logger.info(f"内容已保存: {filename}")
    
    def _update_ui_state(self):
        """更新UI状态"""
        # 检查是否可以开始处理
        config = self.config_panel.get_config()
        api_config = config.get('api', {})
        
        has_file = self.current_file is not None
        has_config = (
            api_config.get('endpoint') and 
            api_config.get('api_key') and 
            api_config.get('model')
        )
        
        can_process = has_file and has_config
        
        # 更新控制面板状态
        self.control_panel.enable_processing(can_process)
        
        if not has_file:
            self.control_panel.set_status("请选择PPT文件")
        elif not has_config:
            self.control_panel.set_status("请配置API设置")
        else:
            self.control_panel.set_status("准备就绪")
    
    # 菜单事件处理
    def _open_file(self):
        """打开文件"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="选择PPT文件",
            filetypes=[
                ("PowerPoint文件", "*.ppt;*.pptx"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            self.file_panel._load_file(filename)
    
    def _save_script(self):
        """保存讲稿"""
        self.preview_panel._save_content()
    
    def _save_script_as(self):
        """另存为讲稿"""
        self.preview_panel._save_as_content()
    
    def _copy_content(self):
        """复制内容"""
        self.preview_panel._copy_content()
    
    def _select_all(self):
        """全选"""
        self.preview_panel._select_all()
    
    def _find_text(self):
        """查找文本"""
        self.preview_panel._find_text()
    
    def _start_generation(self):
        """开始生成"""
        self.control_panel._start_full_processing()
    
    def _stop_generation(self):
        """停止生成"""
        self.control_panel._stop_processing()
    
    def _clean_temp_files(self):
        """清理临时文件"""
        try:
            # 这里可以添加清理临时文件的逻辑
            messagebox.showinfo("提示", "临时文件清理功能待实现")
        except Exception as e:
            messagebox.showerror("错误", f"清理临时文件失败: {e}")
    
    def _open_settings(self):
        """打开设置"""
        # 这里可以添加设置对话框
        messagebox.showinfo("提示", "设置对话框待实现")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """PPT讲稿生成器使用说明：

1. 配置API设置：
   - 输入API地址和密钥
   - 选择合适的模型
   - 测试连接是否正常

2. 选择PPT文件：
   - 点击"选择PPT文件"按钮
   - 支持.ppt和.pptx格式

3. 生成讲稿：
   - 点击"一键生成讲稿"按钮
   - 等待处理完成

4. 编辑和保存：
   - 在预览面板中编辑讲稿
   - 保存到指定位置

快捷键：
- Ctrl+O: 打开文件
- Ctrl+S: 保存讲稿
- Ctrl+C: 复制内容
- Ctrl+A: 全选
- Ctrl+F: 查找文本
"""
        messagebox.showinfo("使用说明", help_text)
    
    def _show_shortcuts(self):
        """显示快捷键"""
        shortcuts_text = """快捷键列表：

文件操作：
- Ctrl+O: 打开PPT文件
- Ctrl+S: 保存讲稿
- Ctrl+Shift+S: 另存为
- Ctrl+Q: 退出程序

编辑操作：
- Ctrl+C: 复制内容
- Ctrl+A: 全选
- Ctrl+F: 查找文本

其他：
- F1: 显示帮助
- F5: 开始生成讲稿
- Esc: 停止当前操作
"""
        messagebox.showinfo("快捷键", shortcuts_text)
    
    def _show_about(self):
        """显示关于信息"""
        about_text = """PPT讲稿生成器 v1.0.0

一个基于AI的PPT讲稿自动生成工具

特性：
• 智能PPT内容分析
• AI视觉理解和处理
• 连贯讲稿自动生成
• 用户友好的界面

技术支持：
• Python + Tkinter界面
• OpenAI GPT-4 Vision API
• 模块化工程架构

开发者：PPT Lecture Generator Team
许可证：MIT License

© 2024 All rights reserved.
"""
        messagebox.showinfo("关于", about_text)
    
    def _on_closing(self):
        """关闭窗口事件"""
        # 检查是否有未保存的内容
        if self.preview_panel.is_content_modified():
            if messagebox.askyesno("确认", "有未保存的内容，是否要退出？"):
                self._cleanup_and_exit()
        else:
            self._cleanup_and_exit()
    
    def _cleanup_and_exit(self):
        """清理资源并退出"""
        try:
            # 保存配置
            self.settings.save_config()
            
            # 清理脚本生成器
            if self.script_generator:
                self.script_generator.cleanup()
            
            self.logger.info("应用程序正常退出")
            
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
        
        finally:
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("用户中断程序")
            self._cleanup_and_exit()
        except Exception as e:
            self.logger.error(f"应用程序运行错误: {e}")
            messagebox.showerror("错误", f"应用程序发生错误: {e}")


if __name__ == "__main__":
    app = MainWindow()
    app.run()