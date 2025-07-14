"""
配置面板组件

提供API配置、模型选择和参数设置功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional
import threading

from ...config.settings import Settings
from ...config.constants import SUPPORTED_MODELS, DEFAULT_API_ENDPOINTS
from ...utils.validators import Validators
from ...utils.logger import get_logger


class ConfigPanel:
    """配置面板类"""
    
    def __init__(self, parent: tk.Widget, settings: Settings):
        """
        初始化配置面板
        
        Args:
            parent: 父组件
            settings: 设置管理器
        """
        self.parent = parent
        self.settings = settings
        self.logger = get_logger()
        
        # 创建主框架
        self.frame = ttk.LabelFrame(parent, text="🔧 API配置", padding="10")
        
        # 配置变量
        self.var_endpoint = tk.StringVar(value=settings.get('api', 'endpoint', ''))
        self.var_api_key = tk.StringVar(value=settings.get('api', 'api_key', ''))
        self.var_model = tk.StringVar(value=settings.get('api', 'model', ''))
        self.var_timeout = tk.StringVar(value=str(settings.get('api', 'timeout', 30)))
        self.var_duration = tk.StringVar(value=str(settings.get('lecture', 'default_duration', 90)))
        
        # 回调函数
        self.on_config_change: Optional[Callable] = None
        self.on_test_connection: Optional[Callable] = None
        
        # 创建界面
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        
        self.logger.debug("配置面板初始化完成")
    
    def _create_widgets(self):
        """创建界面组件"""
        # API端点配置
        endpoint_frame = ttk.Frame(self.frame)
        endpoint_frame.pack(fill='x', pady=5)
        
        ttk.Label(endpoint_frame, text="API地址:").pack(side='left')
        
        self.endpoint_combo = ttk.Combobox(
            endpoint_frame,
            textvariable=self.var_endpoint,
            values=list(DEFAULT_API_ENDPOINTS.values()),
            width=40
        )
        self.endpoint_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        self.btn_test = ttk.Button(
            endpoint_frame,
            text="测试连接",
            command=self._test_connection
        )
        self.btn_test.pack(side='right', padx=(5, 0))
        
        # API密钥配置
        key_frame = ttk.Frame(self.frame)
        key_frame.pack(fill='x', pady=5)
        
        ttk.Label(key_frame, text="API密钥:").pack(side='left')
        
        self.key_entry = ttk.Entry(
            key_frame,
            textvariable=self.var_api_key,
            show="*",
            width=40
        )
        self.key_entry.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        self.btn_show_key = ttk.Button(
            key_frame,
            text="显示",
            command=self._toggle_key_visibility
        )
        self.btn_show_key.pack(side='right', padx=(5, 0))
        
        # 模型选择
        model_frame = ttk.Frame(self.frame)
        model_frame.pack(fill='x', pady=5)
        
        ttk.Label(model_frame, text="模型选择:").pack(side='left')
        
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.var_model,
            values=list(SUPPORTED_MODELS.keys()),
            state="readonly",
            width=30
        )
        self.model_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        self.btn_refresh = ttk.Button(
            model_frame,
            text="刷新模型",
            command=self._refresh_models
        )
        self.btn_refresh.pack(side='right', padx=(5, 0))
        
        # 高级设置
        advanced_frame = ttk.LabelFrame(self.frame, text="高级设置")
        advanced_frame.pack(fill='x', pady=10)
        
        # 超时设置
        timeout_frame = ttk.Frame(advanced_frame)
        timeout_frame.pack(fill='x', pady=2)
        
        ttk.Label(timeout_frame, text="超时时间:").pack(side='left')
        ttk.Entry(
            timeout_frame,
            textvariable=self.var_timeout,
            width=10
        ).pack(side='left', padx=(5, 0))
        ttk.Label(timeout_frame, text="秒").pack(side='left', padx=(2, 0))
        
        # 课程时长设置
        duration_frame = ttk.Frame(advanced_frame)
        duration_frame.pack(fill='x', pady=2)
        
        ttk.Label(duration_frame, text="课程时长:").pack(side='left')
        ttk.Entry(
            duration_frame,
            textvariable=self.var_duration,
            width=10
        ).pack(side='left', padx=(5, 0))
        ttk.Label(duration_frame, text="分钟").pack(side='left', padx=(2, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            button_frame,
            text="保存配置",
            command=self._save_config
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="重置配置",
            command=self._reset_config
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="导入配置",
            command=self._import_config
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="导出配置",
            command=self._export_config
        ).pack(side='left')
        
        # 状态标签
        self.status_label = ttk.Label(
            self.frame,
            text="请配置API设置",
            foreground="blue"
        )
        self.status_label.pack(pady=5)
    
    def _bind_events(self):
        """绑定事件"""
        # 配置变化监听
        self.var_endpoint.trace_add('write', self._on_config_change)
        self.var_api_key.trace_add('write', self._on_config_change)
        self.var_model.trace_add('write', self._on_config_change)
        self.var_timeout.trace_add('write', self._on_config_change)
        self.var_duration.trace_add('write', self._on_config_change)
    
    def _on_config_change(self, *args):
        """配置变化回调"""
        if self.on_config_change:
            self.on_config_change(self.get_config())
    
    def _test_connection(self):
        """测试API连接"""
        # 获取当前配置
        config = self.get_config()
        
        # 验证配置
        if not self._validate_config(config):
            return
        
        # 更新状态
        self.status_label.config(text="正在测试连接...", foreground="orange")
        self.btn_test.config(state="disabled")
        
        # 异步测试连接
        def test_thread():
            try:
                if self.on_test_connection:
                    success, message = self.on_test_connection(config)
                    
                    # 更新UI（需要在主线程中）
                    self.parent.after(0, self._update_test_result, success, message)
                else:
                    self.parent.after(0, self._update_test_result, False, "测试功能未实现")
                    
            except Exception as e:
                self.parent.after(0, self._update_test_result, False, str(e))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def _update_test_result(self, success: bool, message: str):
        """更新测试结果"""
        if success:
            self.status_label.config(text=f"✅ {message}", foreground="green")
        else:
            self.status_label.config(text=f"❌ {message}", foreground="red")
        
        self.btn_test.config(state="normal")
    
    def _toggle_key_visibility(self):
        """切换密钥可见性"""
        if self.key_entry.cget('show') == '*':
            self.key_entry.config(show='')
            self.btn_show_key.config(text="隐藏")
        else:
            self.key_entry.config(show='*')
            self.btn_show_key.config(text="显示")
    
    def _refresh_models(self):
        """刷新模型列表"""
        self.status_label.config(text="正在刷新模型列表...", foreground="orange")
        self.btn_refresh.config(state="disabled")
        
        # 这里可以实现动态获取模型列表的逻辑
        # 现在使用静态列表
        models = list(SUPPORTED_MODELS.keys())
        self.model_combo.config(values=models)
        
        self.status_label.config(text="模型列表已刷新", foreground="green")
        self.btn_refresh.config(state="normal")
    
    def _save_config(self):
        """保存配置"""
        config = self.get_config()
        
        if not self._validate_config(config):
            return
        
        try:
            # 保存到设置管理器
            self.settings.set_section('api', config['api'])
            self.settings.set_section('lecture', config['lecture'])
            
            if self.settings.save_config():
                self.status_label.config(text="✅ 配置已保存", foreground="green")
                messagebox.showinfo("成功", "配置已保存")
            else:
                self.status_label.config(text="❌ 配置保存失败", foreground="red")
                messagebox.showerror("错误", "配置保存失败")
                
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            self.status_label.config(text="❌ 配置保存失败", foreground="red")
            messagebox.showerror("错误", f"配置保存失败: {e}")
    
    def _reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "是否要重置所有配置到默认值？"):
            try:
                # 重置到默认值
                self.var_endpoint.set('')
                self.var_api_key.set('')
                self.var_model.set('gpt-4-vision-preview')
                self.var_timeout.set('30')
                self.var_duration.set('90')
                
                self.status_label.config(text="配置已重置", foreground="blue")
                
            except Exception as e:
                self.logger.error(f"重置配置失败: {e}")
                messagebox.showerror("错误", f"重置配置失败: {e}")
    
    def _import_config(self):
        """导入配置"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("配置文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                # 这里可以实现配置导入逻辑
                messagebox.showinfo("提示", "导入功能待实现")
            except Exception as e:
                self.logger.error(f"导入配置失败: {e}")
                messagebox.showerror("错误", f"导入配置失败: {e}")
    
    def _export_config(self):
        """导出配置"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("配置文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                # 这里可以实现配置导出逻辑
                messagebox.showinfo("提示", "导出功能待实现")
            except Exception as e:
                self.logger.error(f"导出配置失败: {e}")
                messagebox.showerror("错误", f"导出配置失败: {e}")
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        api_config = config.get('api', {})
        
        # 验证API端点
        is_valid, error = Validators.validate_api_endpoint(api_config.get('endpoint', ''))
        if not is_valid:
            messagebox.showerror("配置错误", f"API端点: {error}")
            return False
        
        # 验证API密钥
        is_valid, error = Validators.validate_api_key(api_config.get('api_key', ''))
        if not is_valid:
            messagebox.showerror("配置错误", f"API密钥: {error}")
            return False
        
        # 验证模型
        is_valid, error = Validators.validate_model(api_config.get('model', ''))
        if not is_valid:
            messagebox.showerror("配置错误", f"模型: {error}")
            return False
        
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'api': {
                'endpoint': self.var_endpoint.get(),
                'api_key': self.var_api_key.get(),
                'model': self.var_model.get(),
                'timeout': int(self.var_timeout.get()) if self.var_timeout.get().isdigit() else 30
            },
            'lecture': {
                'default_duration': int(self.var_duration.get()) if self.var_duration.get().isdigit() else 90
            }
        }
    
    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        api_config = config.get('api', {})
        lecture_config = config.get('lecture', {})
        
        self.var_endpoint.set(api_config.get('endpoint', ''))
        self.var_api_key.set(api_config.get('api_key', ''))
        self.var_model.set(api_config.get('model', ''))
        self.var_timeout.set(str(api_config.get('timeout', 30)))
        self.var_duration.set(str(lecture_config.get('default_duration', 90)))
    
    def set_config_change_callback(self, callback: Callable):
        """设置配置变化回调"""
        self.on_config_change = callback
    
    def set_test_connection_callback(self, callback: Callable):
        """设置测试连接回调"""
        self.on_test_connection = callback
    
    def pack(self, **kwargs):
        """打包布局"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self.frame.grid(**kwargs)