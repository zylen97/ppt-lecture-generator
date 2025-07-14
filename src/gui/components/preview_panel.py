"""
预览面板组件

提供结果预览、编辑和保存功能。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Callable, Dict, Any
import os
from pathlib import Path
import subprocess
import platform

from ...utils.file_utils import FileUtils
from ...utils.logger import get_logger


class PreviewPanel:
    """预览面板类"""
    
    def __init__(self, parent: tk.Widget):
        """
        初始化预览面板
        
        Args:
            parent: 父组件
        """
        self.parent = parent
        self.logger = get_logger()
        
        # 创建主框架
        self.frame = ttk.LabelFrame(parent, text="📋 讲稿预览", padding="10")
        
        # 内容状态
        self.current_content = ""
        self.original_content = ""
        self.is_modified = False
        self.output_file = ""
        
        # 回调函数
        self.on_content_change: Optional[Callable] = None
        self.on_save_content: Optional[Callable] = None
        
        # 创建界面
        self._create_widgets()
        
        self.logger.debug("预览面板初始化完成")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 工具栏
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill='x', pady=(0, 10))
        
        # 字体和显示选项
        font_frame = ttk.Frame(toolbar)
        font_frame.pack(side='left')
        
        ttk.Label(font_frame, text="字体大小:").pack(side='left')
        self.font_size_var = tk.StringVar(value="12")
        font_size_combo = ttk.Combobox(
            font_frame,
            textvariable=self.font_size_var,
            values=['9', '10', '11', '12', '14', '16', '18', '20'],
            width=5,
            state='readonly'
        )
        font_size_combo.pack(side='left', padx=(5, 10))
        font_size_combo.bind('<<ComboboxSelected>>', self._on_font_size_change)
        
        # 自动换行选项
        self.wrap_var = tk.BooleanVar(value=True)
        wrap_check = ttk.Checkbutton(
            font_frame,
            text="自动换行",
            variable=self.wrap_var,
            command=self._on_wrap_change
        )
        wrap_check.pack(side='left', padx=(0, 10))
        
        # 操作按钮
        button_frame = ttk.Frame(toolbar)
        button_frame.pack(side='right')
        
        self.btn_copy = ttk.Button(
            button_frame,
            text="📋 复制",
            command=self._copy_content,
            state='disabled'
        )
        self.btn_copy.pack(side='left', padx=(0, 5))
        
        self.btn_save = ttk.Button(
            button_frame,
            text="💾 保存",
            command=self._save_content,
            state='disabled'
        )
        self.btn_save.pack(side='left', padx=(0, 5))
        
        self.btn_save_as = ttk.Button(
            button_frame,
            text="💾 另存为",
            command=self._save_as_content,
            state='disabled'
        )
        self.btn_save_as.pack(side='left', padx=(0, 5))
        
        self.btn_open = ttk.Button(
            button_frame,
            text="📂 打开",
            command=self._open_file,
            state='disabled'
        )
        self.btn_open.pack(side='left')
        
        # 内容显示区域
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill='both', expand=True)
        
        # 创建文本框和滚动条
        self.text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Consolas', 12),
            state='disabled'
        )
        self.text_widget.pack(fill='both', expand=True)
        
        # 绑定文本变化事件
        self.text_widget.bind('<<Modified>>', self._on_text_modified)
        
        # 状态栏
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill='x', pady=(10, 0))
        
        # 内容统计
        self.stats_label = ttk.Label(
            status_frame,
            text="字符数: 0 | 行数: 0 | 字数: 0",
            foreground="gray"
        )
        self.stats_label.pack(side='left')
        
        # 修改状态
        self.modified_label = ttk.Label(
            status_frame,
            text="",
            foreground="orange"
        )
        self.modified_label.pack(side='right')
        
        # 主状态标签
        self.status_label = ttk.Label(
            self.frame,
            text="等待生成讲稿...",
            foreground="blue"
        )
        self.status_label.pack(pady=5)
        
        # 右键菜单
        self._create_context_menu()
    
    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="复制", command=self._copy_content)
        self.context_menu.add_command(label="全选", command=self._select_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="查找", command=self._find_text)
        self.context_menu.add_command(label="替换", command=self._replace_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="保存", command=self._save_content)
        self.context_menu.add_command(label="另存为", command=self._save_as_content)
        
        # 绑定右键事件
        self.text_widget.bind("<Button-3>", self._show_context_menu)
        if platform.system() == "Darwin":  # macOS
            self.text_widget.bind("<Button-2>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _on_font_size_change(self, event=None):
        """字体大小变化"""
        try:
            size = int(self.font_size_var.get())
            font = self.text_widget.cget('font')
            if isinstance(font, str):
                font_family = font.split()[0]
            else:
                font_family = 'Consolas'
            
            self.text_widget.config(font=(font_family, size))
            self.logger.debug(f"字体大小变更为: {size}")
        except ValueError:
            pass
    
    def _on_wrap_change(self):
        """自动换行变化"""
        wrap_mode = tk.WORD if self.wrap_var.get() else tk.NONE
        self.text_widget.config(wrap=wrap_mode)
        self.logger.debug(f"自动换行设置为: {self.wrap_var.get()}")
    
    def _on_text_modified(self, event=None):
        """文本修改事件"""
        if self.text_widget.edit_modified():
            self.current_content = self.text_widget.get(1.0, tk.END).rstrip('\\n')
            self.is_modified = self.current_content != self.original_content
            
            # 更新修改状态
            if self.is_modified:
                self.modified_label.config(text="● 已修改", foreground="orange")
            else:
                self.modified_label.config(text="")
            
            # 更新统计信息
            self._update_stats()
            
            # 触发回调
            if self.on_content_change:
                self.on_content_change(self.current_content)
            
            # 重置修改标志
            self.text_widget.edit_modified(False)
    
    def _update_stats(self):
        """更新统计信息"""
        content = self.current_content
        char_count = len(content)
        line_count = content.count('\\n') + 1 if content else 0
        word_count = len(content.split()) if content else 0
        
        stats_text = f"字符数: {char_count} | 行数: {line_count} | 字数: {word_count}"
        self.stats_label.config(text=stats_text)
    
    def _copy_content(self):
        """复制内容"""
        try:
            if self.text_widget.selection_get():
                # 复制选中内容
                selected_text = self.text_widget.selection_get()
                self.parent.clipboard_clear()
                self.parent.clipboard_append(selected_text)
            else:
                # 复制全部内容
                self.parent.clipboard_clear()
                self.parent.clipboard_append(self.current_content)
            
            self.status_label.config(text="✅ 内容已复制到剪贴板", foreground="green")
            self.logger.info("内容已复制到剪贴板")
            
        except tk.TclError:
            # 没有选中内容，复制全部
            self.parent.clipboard_clear()
            self.parent.clipboard_append(self.current_content)
            self.status_label.config(text="✅ 内容已复制到剪贴板", foreground="green")
        except Exception as e:
            self.logger.error(f"复制内容失败: {e}")
            messagebox.showerror("错误", f"复制内容失败: {e}")
    
    def _select_all(self):
        """全选"""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
    
    def _find_text(self):
        """查找文本"""
        # 简单的查找对话框
        search_text = tk.simpledialog.askstring("查找", "请输入要查找的文本:")
        if search_text:
            self._highlight_text(search_text)
    
    def _replace_text(self):
        """替换文本"""
        # 简单的替换对话框
        messagebox.showinfo("提示", "替换功能待实现")
    
    def _highlight_text(self, search_text: str):
        """高亮显示文本"""
        # 清除之前的高亮
        self.text_widget.tag_remove("search", "1.0", tk.END)
        
        if search_text:
            # 配置高亮样式
            self.text_widget.tag_configure("search", background="yellow")
            
            # 查找并高亮
            start_pos = "1.0"
            while True:
                start_pos = self.text_widget.search(search_text, start_pos, tk.END)
                if not start_pos:
                    break
                
                end_pos = f"{start_pos}+{len(search_text)}c"
                self.text_widget.tag_add("search", start_pos, end_pos)
                start_pos = end_pos
    
    def _save_content(self):
        """保存内容"""
        if not self.current_content:
            messagebox.showwarning("警告", "没有内容可以保存")
            return
        
        if not self.output_file:
            self._save_as_content()
            return
        
        try:
            success = FileUtils.write_text_file(self.output_file, self.current_content)
            if success:
                self.original_content = self.current_content
                self.is_modified = False
                self.modified_label.config(text="")
                self.status_label.config(text="✅ 文件已保存", foreground="green")
                
                # 触发回调
                if self.on_save_content:
                    self.on_save_content(self.output_file, self.current_content)
                
                self.logger.info(f"文件已保存: {self.output_file}")
            else:
                self.status_label.config(text="❌ 保存失败", foreground="red")
                messagebox.showerror("错误", "保存文件失败")
        
        except Exception as e:
            self.logger.error(f"保存文件失败: {e}")
            messagebox.showerror("错误", f"保存文件失败: {e}")
    
    def _save_as_content(self):
        """另存为内容"""
        if not self.current_content:
            messagebox.showwarning("警告", "没有内容可以保存")
            return
        
        filename = filedialog.asksaveasfilename(
            title="保存讲稿",
            defaultextension=".md",
            filetypes=[
                ("Markdown文件", "*.md"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            try:
                success = FileUtils.write_text_file(filename, self.current_content)
                if success:
                    self.output_file = filename
                    self.original_content = self.current_content
                    self.is_modified = False
                    self.modified_label.config(text="")
                    self.status_label.config(text="✅ 文件已保存", foreground="green")
                    self.btn_open.config(state='normal')
                    
                    # 触发回调
                    if self.on_save_content:
                        self.on_save_content(filename, self.current_content)
                    
                    self.logger.info(f"文件已保存: {filename}")
                else:
                    self.status_label.config(text="❌ 保存失败", foreground="red")
                    messagebox.showerror("错误", "保存文件失败")
            
            except Exception as e:
                self.logger.error(f"保存文件失败: {e}")
                messagebox.showerror("错误", f"保存文件失败: {e}")
    
    def _open_file(self):
        """打开文件"""
        if not self.output_file:
            return
        
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.output_file])
            elif platform.system() == "Windows":  # Windows
                subprocess.run(["start", self.output_file], shell=True)
            else:  # Linux
                subprocess.run(["xdg-open", self.output_file])
            
            self.logger.info(f"已打开文件: {self.output_file}")
        
        except Exception as e:
            self.logger.error(f"打开文件失败: {e}")
            messagebox.showerror("错误", f"打开文件失败: {e}")
    
    def set_content(self, content: str, title: str = ""):
        """设置内容"""
        self.current_content = content
        self.original_content = content
        self.is_modified = False
        
        # 更新文本框
        self.text_widget.config(state='normal')
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(1.0, content)
        self.text_widget.config(state='normal')  # 允许编辑
        
        # 更新统计信息
        self._update_stats()
        
        # 启用按钮
        self.btn_copy.config(state='normal')
        self.btn_save.config(state='normal')
        self.btn_save_as.config(state='normal')
        
        # 更新标题
        if title:
            self.frame.config(text=f"📋 讲稿预览 - {title}")
        
        self.status_label.config(text="✅ 讲稿已生成", foreground="green")
        self.modified_label.config(text="")
        
        self.logger.info(f"内容已设置，长度: {len(content)}")
    
    def get_content(self) -> str:
        """获取内容"""
        return self.current_content
    
    def clear_content(self):
        """清除内容"""
        self.current_content = ""
        self.original_content = ""
        self.is_modified = False
        self.output_file = ""
        
        # 清空文本框
        self.text_widget.config(state='normal')
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state='disabled')
        
        # 禁用按钮
        self.btn_copy.config(state='disabled')
        self.btn_save.config(state='disabled')
        self.btn_save_as.config(state='disabled')
        self.btn_open.config(state='disabled')
        
        # 重置状态
        self.status_label.config(text="等待生成讲稿...", foreground="blue")
        self.modified_label.config(text="")
        self.stats_label.config(text="字符数: 0 | 行数: 0 | 字数: 0")
        
        # 重置标题
        self.frame.config(text="📋 讲稿预览")
        
        self.logger.info("内容已清除")
    
    def is_content_modified(self) -> bool:
        """检查内容是否已修改"""
        return self.is_modified
    
    def set_output_file(self, filename: str):
        """设置输出文件"""
        self.output_file = filename
        if filename:
            self.btn_open.config(state='normal')
    
    def set_content_change_callback(self, callback: Callable):
        """设置内容变化回调"""
        self.on_content_change = callback
    
    def set_save_content_callback(self, callback: Callable):
        """设置保存内容回调"""
        self.on_save_content = callback
    
    def set_status(self, message: str, color: str = "blue"):
        """设置状态信息"""
        self.status_label.config(text=message, foreground=color)
    
    def pack(self, **kwargs):
        """打包布局"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self.frame.grid(**kwargs)