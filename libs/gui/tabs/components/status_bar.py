#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态栏组件
"""

import tkinter as tk
from tkinter import ttk


class StatusBar:
    """状态栏组件"""
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        status_frame = ttk.Frame(self.parent_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态文本
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 进度标签
        self.progress_label_var = tk.StringVar()
        self.progress_label = ttk.Label(status_frame, textvariable=self.progress_label_var)
        self.progress_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def update_status(self, status: str):
        """更新状态文本"""
        self.status_var.set(status)
    
    def update_progress(self, current: int, total: int, filename: str = "", status: str = ""):
        """更新进度"""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress_var.set(progress_percent)
            self.progress_label_var.set(f"{current}/{total}")
        
        if filename and status:
            self.status_var.set(f"正在处理: {filename} - {status}")
        
        # 强制更新界面
        self.parent_frame.update_idletasks()
    
    def reset_progress(self):
        """重置进度条"""
        self.progress_var.set(0)
        self.progress_label_var.set("0/0")
        self.status_var.set("就绪")
