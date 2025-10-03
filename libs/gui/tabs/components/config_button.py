#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置界面组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from libs.core.config_manager import ConfigManager


class ConfigDialog:
    """配置对话框"""
    
    def __init__(self, parent, config_manager: ConfigManager, callback: Optional[Callable] = None):
        self.parent = parent
        self.config_manager = config_manager
        self.callback = callback
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("配置选项")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # 使对话框模态
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.center_window()
        
        # 创建界面
        self.create_widgets()
        
        # 加载当前配置
        self.load_current_config()
    
    def center_window(self):
        """居中显示窗口"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="父文件夹识别配置", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 配置选项框架
        config_frame = ttk.LabelFrame(main_frame, text="识别选项", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 父文件夹识别总开关
        self.enable_parent_recognition_var = tk.BooleanVar()
        self.enable_parent_recognition_check = ttk.Checkbutton(
            config_frame,
            text="启用父文件夹识别",
            variable=self.enable_parent_recognition_var,
            command=self.on_parent_recognition_toggle
        )
        self.enable_parent_recognition_check.pack(anchor=tk.W, pady=2)
        
        # 剧名识别开关
        self.enable_series_recognition_var = tk.BooleanVar()
        self.enable_series_recognition_check = ttk.Checkbutton(
            config_frame,
            text="启用剧名识别",
            variable=self.enable_series_recognition_var
        )
        self.enable_series_recognition_check.pack(anchor=tk.W, pady=2)
        
        # 季数识别开关
        self.enable_season_recognition_var = tk.BooleanVar()
        self.enable_season_recognition_check = ttk.Checkbutton(
            config_frame,
            text="启用季数识别",
            variable=self.enable_season_recognition_var
        )
        self.enable_season_recognition_check.pack(anchor=tk.W, pady=2)
        
        # 自定义季数框架
        custom_season_frame = ttk.LabelFrame(main_frame, text="自定义季数", padding=10)
        custom_season_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 自定义季数开关
        self.enable_custom_season_var = tk.BooleanVar()
        self.enable_custom_season_check = ttk.Checkbutton(
            custom_season_frame,
            text="启用自定义季数",
            variable=self.enable_custom_season_var,
            command=self.on_custom_season_toggle
        )
        self.enable_custom_season_check.pack(anchor=tk.W, pady=2)
        
        # 默认季数设置
        default_season_frame = ttk.Frame(custom_season_frame)
        default_season_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(default_season_frame, text="默认季数:").pack(side=tk.LEFT)
        self.default_season_var = tk.StringVar()
        self.default_season_entry = ttk.Entry(default_season_frame, textvariable=self.default_season_var, width=10)
        self.default_season_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(default_season_frame, text="(例如: 01, 02, 03)", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        
        # 说明文本
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = """说明：
• 父文件夹识别：从文件路径中自动识别剧名和季数
• 剧名识别：从父文件夹提取剧集名称
• 季数识别：从S01、S02等文件夹识别季数
• 自定义季数：允许手动设置季数，优先级高于文件夹识别"""
        
        info_label = ttk.Label(info_frame, text=info_text, font=("Arial", 9), justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 按钮
        ttk.Button(button_frame, text="确定", command=self.on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.on_cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="重置", command=self.on_reset).pack(side=tk.LEFT)
    
    def on_parent_recognition_toggle(self):
        """父文件夹识别开关切换"""
        enabled = self.enable_parent_recognition_var.get()
        self.enable_series_recognition_check.config(state=tk.NORMAL if enabled else tk.DISABLED)
        self.enable_season_recognition_check.config(state=tk.NORMAL if enabled else tk.DISABLED)
        
        if not enabled:
            self.enable_series_recognition_var.set(False)
            self.enable_season_recognition_var.set(False)
    
    def on_custom_season_toggle(self):
        """自定义季数开关切换"""
        enabled = self.enable_custom_season_var.get()
        self.default_season_entry.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def load_current_config(self):
        """加载当前配置"""
        self.enable_parent_recognition_var.set(self.config_manager.is_parent_folder_recognition_enabled())
        self.enable_series_recognition_var.set(self.config_manager.is_series_recognition_enabled())
        self.enable_season_recognition_var.set(self.config_manager.is_season_recognition_enabled())
        self.enable_custom_season_var.set(self.config_manager.is_custom_season_enabled())
        self.default_season_var.set(self.config_manager.get_default_season())
        
        # 更新界面状态
        self.on_parent_recognition_toggle()
        self.on_custom_season_toggle()
    
    def on_ok(self):
        """确定按钮"""
        try:
            # 保存配置
            self.config_manager.set_parent_folder_recognition(self.enable_parent_recognition_var.get())
            self.config_manager.set_series_recognition(self.enable_series_recognition_var.get())
            self.config_manager.set_season_recognition(self.enable_season_recognition_var.get())
            self.config_manager.set_custom_season(self.enable_custom_season_var.get())
            
            # 验证默认季数
            default_season = self.default_season_var.get().strip()
            if default_season and not default_season.isdigit():
                messagebox.showerror("错误", "默认季数必须是数字")
                return
            
            self.config_manager.set_default_season(default_season or "01")
            
            # 保存到文件
            if self.config_manager.save_config():
                self.result = True
                if self.callback:
                    self.callback()
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "保存配置失败")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置时出错: {e}")
    
    def on_cancel(self):
        """取消按钮"""
        self.result = False
        self.dialog.destroy()
    
    def on_reset(self):
        """重置按钮"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            self.load_current_config()


class ConfigButton:
    """配置按钮组件"""
    
    def __init__(self, parent_frame, config_manager: ConfigManager, callback: Optional[Callable] = None):
        self.parent_frame = parent_frame
        self.config_manager = config_manager
        self.callback = callback
        
        # 创建配置按钮
        self.config_button = ttk.Button(
            parent_frame,
            text="⚙️ 配置",
            command=self.open_config_dialog
        )
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.config_button.pack(**kwargs)
    
    def open_config_dialog(self):
        """打开配置对话框"""
        dialog = ConfigDialog(self.parent_frame.winfo_toplevel(), self.config_manager, self.callback)
        self.parent_frame.wait_window(dialog.dialog)
