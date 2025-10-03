#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载状态标签页
负责热重载功能的控制和状态显示
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List

from libs.utils.hot_reload import HotReloadManager


class HotReloadTab:
    """热重载状态标签页"""
    
    def __init__(self, parent_notebook, hot_reload_manager: HotReloadManager, main_window=None):
        self.parent_notebook = parent_notebook
        self.hot_reload_manager = hot_reload_manager
        self.main_window = main_window  # 添加主窗口引用
        
        # 创建界面
        self.create_widgets()
        
        # 初始化日志显示
        self.update_reload_log_display()
        
        # 设置定时器来定期更新日志显示
        self.schedule_log_update()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="热重载状态")
        
        # 状态控制区域
        self.create_control_section()
        
        # 日志显示区域
        self.create_log_section()
    
    def create_control_section(self):
        """创建状态控制区域"""
        control_frame = ttk.LabelFrame(self.frame, text="热重载控制")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 热重载开关
        self.reload_var = tk.BooleanVar(value=self.hot_reload_manager.reload_enabled)
        reload_check = ttk.Checkbutton(control_frame, text="启用热重载", 
                                     variable=self.reload_var, 
                                     command=self.toggle_reload)
        reload_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 手动重载按钮
        ttk.Button(control_frame, text="手动重载", 
                  command=self.manual_reload).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 清空日志按钮
        ttk.Button(control_frame, text="清空日志", 
                  command=self.clear_reload_log).pack(side=tk.RIGHT, padx=5, pady=5)
    
    def create_log_section(self):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(self.frame, text="重载日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.reload_log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.reload_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def toggle_reload(self):
        """切换热重载状态"""
        enabled = self.reload_var.get()
        self.hot_reload_manager.toggle_reload(enabled)
    
    def manual_reload(self):
        """手动触发重载"""
        if self.main_window:
            # 调用主窗口的完整重载流程，并跳转到热重载标签页
            self.main_window.reload_code(auto_switch_tab=True)
        else:
            # 如果没有主窗口引用，使用原来的方法
            self.hot_reload_manager.manual_reload("__main__")
    
    def clear_reload_log(self):
        """清空重载日志"""
        self.hot_reload_manager.clear_reload_log()
        self.update_reload_log_display()
    
    def schedule_log_update(self):
        """设置定时器来定期更新日志显示"""
        self.update_reload_log_display()
        # 每500毫秒更新一次日志显示
        self.frame.after(500, self.schedule_log_update)
    
    def update_reload_log_display(self):
        """更新重载日志显示"""
        try:
            self.reload_log_text.delete(1.0, tk.END)
            for log_entry in self.hot_reload_manager.reload_log:
                self.reload_log_text.insert(tk.END, log_entry + "\n")
            self.reload_log_text.see(tk.END)
        except Exception as e:
            # 如果界面已经被销毁，忽略错误
            pass
