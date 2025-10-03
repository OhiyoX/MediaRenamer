#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录选择组件
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable


class DirectorySelector:
    """目录选择组件"""
    
    def __init__(self, parent_frame: ttk.Frame, on_directory_selected: Callable[[str], None]):
        self.parent_frame = parent_frame
        self.on_directory_selected = on_directory_selected
        self.current_dir = ""
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        dir_frame = ttk.LabelFrame(self.parent_frame, text="目录选择")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(dir_frame, text="选择目录", command=self.browse_directory).pack(side=tk.LEFT, padx=5)
        self.dir_label = ttk.Label(dir_frame, text="未选择目录")
        self.dir_label.pack(side=tk.LEFT, padx=10)
    
    def browse_directory(self):
        """浏览目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.current_dir = directory
            self.dir_label.config(text=f"已选择: {directory}")
            self.on_directory_selected(directory)
    
    def get_current_directory(self) -> str:
        """获取当前选择的目录"""
        return self.current_dir
    
    def set_current_directory(self, directory: str):
        """设置当前目录"""
        self.current_dir = directory
        self.dir_label.config(text=f"已选择: {directory}")
