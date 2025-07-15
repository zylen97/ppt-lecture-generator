"""
文件面板组件

提供文件上传、预览和管理功能。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
import os
from pathlib import Path

from ...utils.file_utils import FileUtils
from ...utils.validators import Validators
from ...utils.logger import get_logger


class FilePanel:
    """文件面板类"""
    
    def __init__(self, parent: tk.Widget):
        """
        初始化文件面板
        
        Args:
            parent: 父组件
        """
        self.parent = parent
        self.logger = get_logger()
        
        # 创建主框架
        self.frame = ttk.LabelFrame(parent, text="📁 文件上传", padding="10")
        
        # 文件状态
        self.current_file: Optional[str] = None
        self.file_info: dict = {}
        
        # 回调函数
        self.on_file_selected: Optional[Callable] = None
        self.on_file_preview: Optional[Callable] = None
        
        # 创建界面
        self._create_widgets()
        
        self.logger.debug("文件面板初始化完成")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 文件选择区域
        select_frame = ttk.Frame(self.frame)
        select_frame.pack(fill='x', pady=5)
        
        self.btn_select = ttk.Button(
            select_frame,
            text="选择PPT文件...",
            command=self._select_file,
            width=20
        )
        self.btn_select.pack(side='left')
        
        # 拖拽提示
        drag_label = ttk.Label(
            select_frame,
            text="或拖拽文件到此处",
            foreground="gray"
        )
        drag_label.pack(side='left', padx=(10, 0))
        
        # 文件信息显示
        info_frame = ttk.LabelFrame(self.frame, text="文件信息")
        info_frame.pack(fill='both', expand=True, pady=10)
        
        # 文件名显示
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(fill='x', pady=2)
        
        ttk.Label(name_frame, text="文件名:").pack(side='left')
        self.name_label = ttk.Label(
            name_frame,
            text="未选择文件",
            foreground="gray"
        )
        self.name_label.pack(side='left', padx=(5, 0))
        
        # 文件大小显示
        size_frame = ttk.Frame(info_frame)
        size_frame.pack(fill='x', pady=2)
        
        ttk.Label(size_frame, text="文件大小:").pack(side='left')
        self.size_label = ttk.Label(
            size_frame,
            text="--",
            foreground="gray"
        )
        self.size_label.pack(side='left', padx=(5, 0))
        
        # 幻灯片数量（如果可以获取）
        slides_frame = ttk.Frame(info_frame)
        slides_frame.pack(fill='x', pady=2)
        
        ttk.Label(slides_frame, text="幻灯片数:").pack(side='left')
        self.slides_label = ttk.Label(
            slides_frame,
            text="--",
            foreground="gray"
        )
        self.slides_label.pack(side='left', padx=(5, 0))
        
        # 文件路径显示
        path_frame = ttk.Frame(info_frame)
        path_frame.pack(fill='x', pady=2)
        
        ttk.Label(path_frame, text="路径:").pack(side='left')
        self.path_text = tk.Text(
            path_frame,
            height=2,
            width=40,
            wrap='word',
            state='disabled'
        )
        self.path_text.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        # 操作按钮
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill='x', pady=10)
        
        self.btn_preview = ttk.Button(
            button_frame,
            text="🔍 预览PPT",
            command=self._preview_file,
            state='disabled'
        )
        self.btn_preview.pack(side='left', padx=(0, 5))
        
        self.btn_clear = ttk.Button(
            button_frame,
            text="🗑️ 清除",
            command=self._clear_file,
            state='disabled'
        )
        self.btn_clear.pack(side='left', padx=(0, 5))
        
        self.btn_open_folder = ttk.Button(
            button_frame,
            text="📂 打开文件夹",
            command=self._open_folder,
            state='disabled'
        )
        self.btn_open_folder.pack(side='left')
        
        # 状态标签
        self.status_label = ttk.Label(
            self.frame,
            text="请选择PPT文件",
            foreground="blue"
        )
        self.status_label.pack(pady=5)
        
        # 设置拖拽支持
        self._setup_drag_drop()
    
    def _setup_drag_drop(self):
        """设置拖拽支持"""
        # 这里可以添加拖拽功能的实现
        # 由于tkinter的拖拽支持较为复杂，这里先留空
        pass
    
    def _select_file(self):
        """选择文件"""
        filename = filedialog.askopenfilename(
            title="选择PPT文件",
            filetypes=[
                ("PowerPoint文件", "*.ppt *.pptx"),
                ("PPT文件", "*.ppt"),
                ("PPTX文件", "*.pptx"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            self._load_file(filename)
    
    def _load_file(self, filename: str):
        """加载文件"""
        try:
            # 验证文件
            is_valid, error = Validators.validate_ppt_file(filename)
            if not is_valid:
                messagebox.showerror("文件错误", error)
                return
            
            # 获取文件信息
            self.file_info = FileUtils.get_file_info(filename)
            self.current_file = filename
            
            # 更新界面
            self._update_file_info()
            
            # 启用按钮
            self.btn_preview.config(state='normal')
            self.btn_clear.config(state='normal')
            self.btn_open_folder.config(state='normal')
            
            # 触发回调
            if self.on_file_selected:
                self.on_file_selected(filename, self.file_info)
            
            self.status_label.config(text="✅ 文件加载成功", foreground="green")
            self.logger.info(f"文件加载成功: {filename}")
            
        except Exception as e:
            self.logger.error(f"文件加载失败: {e}")
            self.status_label.config(text="❌ 文件加载失败", foreground="red")
            messagebox.showerror("错误", f"文件加载失败: {e}")
    
    def _update_file_info(self):
        """更新文件信息显示"""
        if not self.current_file or not self.file_info:
            return
        
        # 更新文件名
        filename = Path(self.current_file).name
        self.name_label.config(text=filename, foreground="black")
        
        # 更新文件大小
        size = self.file_info.get('size', 0)
        if size > 1024 * 1024:
            size_text = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_text = f"{size / 1024:.1f} KB"
        else:
            size_text = f"{size} B"
        
        self.size_label.config(text=size_text, foreground="black")
        
        # 更新路径
        self.path_text.config(state='normal')
        self.path_text.delete(1.0, tk.END)
        self.path_text.insert(1.0, self.current_file)
        self.path_text.config(state='disabled')
        
        # 尝试获取幻灯片数量（这需要实际处理PPT文件）
        try:
            # 这里可以添加获取幻灯片数量的逻辑
            # 现在先显示占位符
            self.slides_label.config(text="需要分析", foreground="orange")
        except Exception:
            self.slides_label.config(text="无法获取", foreground="gray")
    
    def _preview_file(self):
        """预览文件"""
        if not self.current_file:
            return
        
        try:
            # 触发预览回调
            if self.on_file_preview:
                self.on_file_preview(self.current_file)
            else:
                # 默认使用系统程序打开
                import subprocess
                import platform
                
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", self.current_file])
                elif platform.system() == "Windows":  # Windows
                    subprocess.run(["start", self.current_file], shell=True)
                else:  # Linux
                    subprocess.run(["xdg-open", self.current_file])
            
            self.logger.info(f"预览文件: {self.current_file}")
            
        except Exception as e:
            self.logger.error(f"预览文件失败: {e}")
            messagebox.showerror("错误", f"预览文件失败: {e}")
    
    def _clear_file(self):
        """清除文件"""
        if messagebox.askyesno("确认", "是否要清除当前文件？"):
            self.current_file = None
            self.file_info = {}
            
            # 重置界面
            self.name_label.config(text="未选择文件", foreground="gray")
            self.size_label.config(text="--", foreground="gray")
            self.slides_label.config(text="--", foreground="gray")
            
            self.path_text.config(state='normal')
            self.path_text.delete(1.0, tk.END)
            self.path_text.config(state='disabled')
            
            # 禁用按钮
            self.btn_preview.config(state='disabled')
            self.btn_clear.config(state='disabled')
            self.btn_open_folder.config(state='disabled')
            
            self.status_label.config(text="请选择PPT文件", foreground="blue")
            
            # 触发回调
            if self.on_file_selected:
                self.on_file_selected(None, {})
            
            self.logger.info("文件已清除")
    
    def _open_folder(self):
        """打开文件夹"""
        if not self.current_file:
            return
        
        try:
            folder_path = Path(self.current_file).parent
            
            import subprocess
            import platform
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)])
            elif platform.system() == "Windows":  # Windows
                subprocess.run(["explorer", str(folder_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(folder_path)])
            
            self.logger.info(f"打开文件夹: {folder_path}")
            
        except Exception as e:
            self.logger.error(f"打开文件夹失败: {e}")
            messagebox.showerror("错误", f"打开文件夹失败: {e}")
    
    def get_current_file(self) -> Optional[str]:
        """获取当前文件"""
        return self.current_file
    
    def get_file_info(self) -> dict:
        """获取文件信息"""
        return self.file_info.copy()
    
    def set_file_selected_callback(self, callback: Callable):
        """设置文件选择回调"""
        self.on_file_selected = callback
    
    def set_file_preview_callback(self, callback: Callable):
        """设置文件预览回调"""
        self.on_file_preview = callback
    
    def update_slides_count(self, count: int):
        """更新幻灯片数量显示"""
        self.slides_label.config(text=str(count), foreground="black")
    
    def set_status(self, message: str, color: str = "blue"):
        """设置状态信息"""
        self.status_label.config(text=message, foreground=color)
    
    def pack(self, **kwargs):
        """打包布局"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self.frame.grid(**kwargs)