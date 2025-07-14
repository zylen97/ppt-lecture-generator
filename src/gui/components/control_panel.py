"""
控制面板组件

提供处理控制、进度显示和状态管理功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any
import threading
import time

from ...utils.logger import get_logger


class ControlPanel:
    """控制面板类"""
    
    def __init__(self, parent: tk.Widget):
        """
        初始化控制面板
        
        Args:
            parent: 父组件
        """
        self.parent = parent
        self.logger = get_logger()
        
        # 创建主框架
        self.frame = ttk.LabelFrame(parent, text="⚙️ 处理控制", padding="10")
        
        # 处理状态
        self.is_processing = False
        self.current_task = ""
        self.progress_value = 0
        self.total_steps = 0
        
        # 回调函数
        self.on_start_processing: Optional[Callable] = None
        self.on_stop_processing: Optional[Callable] = None
        self.on_step_processing: Optional[Callable] = None
        
        # 创建界面
        self._create_widgets()
        
        self.logger.debug("控制面板初始化完成")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 操作按钮区域
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill='x', pady=5)
        
        # 主要操作按钮
        self.btn_generate = ttk.Button(
            button_frame,
            text="🔄 一键生成讲稿",
            command=self._start_full_processing,
            state='disabled'
        )
        self.btn_generate.pack(side='left', padx=(0, 5))
        
        # 分步操作按钮
        self.btn_analyze = ttk.Button(
            button_frame,
            text="📸 生成截图",
            command=self._start_screenshot,
            state='disabled'
        )
        self.btn_analyze.pack(side='left', padx=(0, 5))
        
        self.btn_ai_analyze = ttk.Button(
            button_frame,
            text="🤖 AI分析",
            command=self._start_ai_analysis,
            state='disabled'
        )
        self.btn_ai_analyze.pack(side='left', padx=(0, 5))
        
        self.btn_generate_script = ttk.Button(
            button_frame,
            text="📝 生成讲稿",
            command=self._start_script_generation,
            state='disabled'
        )
        self.btn_generate_script.pack(side='left', padx=(0, 5))
        
        # 停止按钮
        self.btn_stop = ttk.Button(
            button_frame,
            text="⏹️ 停止",
            command=self._stop_processing,
            state='disabled'
        )
        self.btn_stop.pack(side='right')
        
        # 进度显示区域
        progress_frame = ttk.LabelFrame(self.frame, text="处理进度")
        progress_frame.pack(fill='x', pady=10)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(fill='x', pady=5)
        
        # 进度文本
        self.progress_text = ttk.Label(
            progress_frame,
            text="0%",
            anchor='center'
        )
        self.progress_text.pack(pady=2)
        
        # 当前任务显示
        self.task_label = ttk.Label(
            progress_frame,
            text="等待开始...",
            foreground="blue"
        )
        self.task_label.pack(pady=2)
        
        # 处理统计
        stats_frame = ttk.LabelFrame(self.frame, text="处理统计")
        stats_frame.pack(fill='x', pady=10)
        
        # 统计信息
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x', pady=5)
        
        # 处理时间
        ttk.Label(stats_grid, text="处理时间:").grid(row=0, column=0, sticky='w')
        self.time_label = ttk.Label(stats_grid, text="--", foreground="gray")
        self.time_label.grid(row=0, column=1, sticky='w', padx=(5, 0))
        
        # 处理幻灯片数
        ttk.Label(stats_grid, text="处理幻灯片:").grid(row=1, column=0, sticky='w')
        self.slides_label = ttk.Label(stats_grid, text="--", foreground="gray")
        self.slides_label.grid(row=1, column=1, sticky='w', padx=(5, 0))
        
        # API调用次数
        ttk.Label(stats_grid, text="API调用:").grid(row=2, column=0, sticky='w')
        self.api_calls_label = ttk.Label(stats_grid, text="--", foreground="gray")
        self.api_calls_label.grid(row=2, column=1, sticky='w', padx=(5, 0))
        
        # 生成的讲稿长度
        ttk.Label(stats_grid, text="讲稿长度:").grid(row=3, column=0, sticky='w')
        self.script_length_label = ttk.Label(stats_grid, text="--", foreground="gray")
        self.script_length_label.grid(row=3, column=1, sticky='w', padx=(5, 0))
        
        # 配置stats_grid的列权重
        stats_grid.columnconfigure(1, weight=1)
        
        # 状态显示
        self.status_label = ttk.Label(
            self.frame,
            text="请选择PPT文件并配置API设置",
            foreground="blue"
        )
        self.status_label.pack(pady=5)
        
        # 处理时间追踪
        self.start_time = None
        self.time_thread = None
        self.stop_time_thread = False
    
    def _start_full_processing(self):
        """开始完整处理"""
        if self.is_processing:
            return
        
        self.logger.info("开始完整处理流程")
        self._set_processing_state(True)
        self.current_task = "完整处理"
        
        # 重置进度
        self.set_progress(0, 100, "开始处理...")
        
        # 启动时间追踪
        self._start_time_tracking()
        
        # 触发回调
        if self.on_start_processing:
            threading.Thread(
                target=self._run_processing,
                args=("full",),
                daemon=True
            ).start()
    
    def _start_screenshot(self):
        """开始截图处理"""
        if self.is_processing:
            return
        
        self.logger.info("开始截图处理")
        self._set_processing_state(True)
        self.current_task = "截图处理"
        
        # 触发回调
        if self.on_step_processing:
            threading.Thread(
                target=self._run_processing,
                args=("screenshot",),
                daemon=True
            ).start()
    
    def _start_ai_analysis(self):
        """开始AI分析"""
        if self.is_processing:
            return
        
        self.logger.info("开始AI分析")
        self._set_processing_state(True)
        self.current_task = "AI分析"
        
        # 触发回调
        if self.on_step_processing:
            threading.Thread(
                target=self._run_processing,
                args=("ai_analysis",),
                daemon=True
            ).start()
    
    def _start_script_generation(self):
        """开始讲稿生成"""
        if self.is_processing:
            return
        
        self.logger.info("开始讲稿生成")
        self._set_processing_state(True)
        self.current_task = "讲稿生成"
        
        # 触发回调
        if self.on_step_processing:
            threading.Thread(
                target=self._run_processing,
                args=("script_generation",),
                daemon=True
            ).start()
    
    def _run_processing(self, task_type: str):
        """运行处理任务"""
        try:
            if task_type == "full" and self.on_start_processing:
                result = self.on_start_processing()
            elif self.on_step_processing:
                result = self.on_step_processing(task_type)
            else:
                result = False
            
            # 更新UI（在主线程中）
            self.parent.after(0, self._processing_completed, result)
            
        except Exception as e:
            self.logger.error(f"处理任务失败: {e}")
            self.parent.after(0, self._processing_failed, str(e))
    
    def _processing_completed(self, success: bool):
        """处理完成"""
        if success:
            self.set_progress(100, 100, "处理完成!")
            self.status_label.config(text="✅ 处理完成", foreground="green")
        else:
            self.status_label.config(text="❌ 处理失败", foreground="red")
        
        self._set_processing_state(False)
        self._stop_time_tracking()
    
    def _processing_failed(self, error: str):
        """处理失败"""
        self.status_label.config(text=f"❌ 处理失败: {error}", foreground="red")
        self._set_processing_state(False)
        self._stop_time_tracking()
        
        messagebox.showerror("处理失败", f"处理过程中发生错误:\\n{error}")
    
    def _stop_processing(self):
        """停止处理"""
        if not self.is_processing:
            return
        
        if messagebox.askyesno("确认", "是否要停止当前处理？"):
            self.logger.info("用户停止处理")
            
            # 触发停止回调
            if self.on_stop_processing:
                self.on_stop_processing()
            
            self.status_label.config(text="⏹️ 处理已停止", foreground="orange")
            self._set_processing_state(False)
            self._stop_time_tracking()
    
    def _set_processing_state(self, processing: bool):
        """设置处理状态"""
        self.is_processing = processing
        
        if processing:
            # 禁用操作按钮
            self.btn_generate.config(state='disabled')
            self.btn_analyze.config(state='disabled')
            self.btn_ai_analyze.config(state='disabled')
            self.btn_generate_script.config(state='disabled')
            self.btn_stop.config(state='normal')
        else:
            # 启用操作按钮
            self.btn_generate.config(state='normal')
            self.btn_analyze.config(state='normal')
            self.btn_ai_analyze.config(state='normal')
            self.btn_generate_script.config(state='normal')
            self.btn_stop.config(state='disabled')
    
    def _start_time_tracking(self):
        """开始时间追踪"""
        self.start_time = time.time()
        self.stop_time_thread = False
        
        def update_time():
            while not self.stop_time_thread:
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    time_str = self._format_time(elapsed)
                    self.parent.after(0, self._update_time_display, time_str)
                time.sleep(1)
        
        self.time_thread = threading.Thread(target=update_time, daemon=True)
        self.time_thread.start()
    
    def _stop_time_tracking(self):
        """停止时间追踪"""
        self.stop_time_thread = True
        if self.time_thread:
            self.time_thread.join(timeout=1)
    
    def _update_time_display(self, time_str: str):
        """更新时间显示"""
        self.time_label.config(text=time_str, foreground="black")
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            seconds = seconds % 60
            return f"{minutes}分{seconds:.0f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分钟"
    
    def set_progress(self, current: int, total: int, message: str = ""):
        """设置进度"""
        self.progress_value = current
        self.total_steps = total
        
        # 更新进度条
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar.config(value=percentage)
            self.progress_text.config(text=f"{percentage:.1f}%")
        else:
            self.progress_bar.config(value=0)
            self.progress_text.config(text="0%")
        
        # 更新任务信息
        if message:
            self.task_label.config(text=message, foreground="blue")
        
        # 强制更新UI
        self.parent.update_idletasks()
    
    def update_stats(self, stats: Dict[str, Any]):
        """更新统计信息"""
        if 'slides_processed' in stats:
            self.slides_label.config(
                text=str(stats['slides_processed']),
                foreground="black"
            )
        
        if 'api_calls' in stats:
            self.api_calls_label.config(
                text=str(stats['api_calls']),
                foreground="black"
            )
        
        if 'script_length' in stats:
            length = stats['script_length']
            if length > 1000:
                length_str = f"{length/1000:.1f}K字符"
            else:
                length_str = f"{length}字符"
            
            self.script_length_label.config(
                text=length_str,
                foreground="black"
            )
    
    def enable_processing(self, enabled: bool):
        """启用/禁用处理功能"""
        if not self.is_processing:
            state = 'normal' if enabled else 'disabled'
            self.btn_generate.config(state=state)
            self.btn_analyze.config(state=state)
            self.btn_ai_analyze.config(state=state)
            self.btn_generate_script.config(state=state)
    
    def set_status(self, message: str, color: str = "blue"):
        """设置状态信息"""
        self.status_label.config(text=message, foreground=color)
    
    def set_start_processing_callback(self, callback: Callable):
        """设置开始处理回调"""
        self.on_start_processing = callback
    
    def set_stop_processing_callback(self, callback: Callable):
        """设置停止处理回调"""
        self.on_stop_processing = callback
    
    def set_step_processing_callback(self, callback: Callable):
        """设置分步处理回调"""
        self.on_step_processing = callback
    
    def reset_progress(self):
        """重置进度"""
        self.set_progress(0, 100, "等待开始...")
        self.progress_bar.config(value=0)
        self.progress_text.config(text="0%")
        
        # 重置统计信息
        self.time_label.config(text="--", foreground="gray")
        self.slides_label.config(text="--", foreground="gray")
        self.api_calls_label.config(text="--", foreground="gray")
        self.script_length_label.config(text="--", foreground="gray")
    
    def pack(self, **kwargs):
        """打包布局"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self.frame.grid(**kwargs)