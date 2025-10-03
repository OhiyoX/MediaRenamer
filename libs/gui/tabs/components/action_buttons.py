#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作按钮组件
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ActionButtons:
    """操作按钮组件"""
    
    def __init__(self, parent_frame: ttk.Frame,
                 on_preview_rename: Callable[[], None],
                 on_execute_rename: Callable[[], None],
                 on_restore_filenames: Callable[[], None],
                 on_view_rename_log: Callable[[], None],
                 on_create_backup: Callable[[], None]):
        self.parent_frame = parent_frame
        self.on_preview_rename = on_preview_rename
        self.on_execute_rename = on_execute_rename
        self.on_restore_filenames = on_restore_filenames
        self.on_view_rename_log = on_view_rename_log
        self.on_create_backup = on_create_backup
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        button_frame = ttk.Frame(self.parent_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="预览重命名", command=self.on_preview_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="执行重命名", command=self.on_execute_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="恢复文件名", command=self.on_restore_filenames).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看重命名记录", command=self.on_view_rename_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="创建备份", command=self.on_create_backup).pack(side=tk.RIGHT, padx=5)
