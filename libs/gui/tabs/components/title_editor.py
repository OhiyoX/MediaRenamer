#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧集名编辑组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable


class TitleEditor:
    """剧集名编辑组件"""
    
    def __init__(self, parent_frame: ttk.Frame, 
                 on_title_change: Callable[[str], None],
                 on_apply_custom_title: Callable[[str], None],
                 on_clear_custom_title: Callable[[], None]):
        self.parent_frame = parent_frame
        self.on_title_change = on_title_change
        self.on_apply_custom_title = on_apply_custom_title
        self.on_clear_custom_title = on_clear_custom_title
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        title_frame = ttk.LabelFrame(self.parent_frame, text="剧集名编辑")
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 剧集名编辑说明
        ttk.Label(title_frame, text="可以自定义重命名时的剧集名部分，留空则使用原文件名中的剧集名").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(title_frame, text="注意：即使规则没有匹配到series字段，也可以设置自定义剧集名").pack(anchor=tk.W, padx=5, pady=2)
        
        # 剧集名输入框
        input_frame = ttk.Frame(title_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="自定义剧集名:").pack(side=tk.LEFT, padx=5)
        self.custom_title_var = tk.StringVar()
        title_entry = ttk.Entry(input_frame, textvariable=self.custom_title_var, width=50)
        title_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        title_entry.bind('<KeyRelease>', self._on_title_change)
        
        # 剧集名应用按钮
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="应用剧集名到所有文件", command=self._apply_custom_title).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除自定义剧集名", command=self._clear_custom_title).pack(side=tk.LEFT, padx=5)
    
    def _on_title_change(self, event=None):
        """剧集名变化事件"""
        custom_title = self.custom_title_var.get().strip()
        self.on_title_change(custom_title)
    
    def _apply_custom_title(self):
        """应用自定义剧集名到所有文件"""
        custom_title = self.custom_title_var.get().strip()
        if not custom_title:
            messagebox.showwarning("警告", "请输入自定义剧集名")
            return
        
        self.on_apply_custom_title(custom_title)
    
    def _clear_custom_title(self):
        """清除自定义剧集名"""
        self.custom_title_var.set("")
        self.on_clear_custom_title()
    
    def get_custom_title(self) -> str:
        """获取自定义剧集名"""
        return self.custom_title_var.get().strip()
    
    def set_custom_title(self, title: str):
        """设置自定义剧集名"""
        self.custom_title_var.set(title)
