#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则详情显示组件
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Optional
from libs.core.rule import RegexRule


class RuleDetailDisplay:
    """规则详情显示组件"""
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        rule_detail_frame = ttk.LabelFrame(self.parent_frame, text="当前规则详情")
        rule_detail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 规则信息显示
        self.rule_info_text = scrolledtext.ScrolledText(rule_detail_frame, height=4, wrap=tk.WORD)
        self.rule_info_text.pack(fill=tk.X, padx=5, pady=5)
        self.rule_info_text.config(state=tk.DISABLED)
    
    def update_rule_info(self, rule: Optional[RegexRule]):
        """更新规则详情显示"""
        self.rule_info_text.config(state=tk.NORMAL)
        self.rule_info_text.delete(1.0, tk.END)
        
        if not rule:
            self.rule_info_text.insert(tk.END, "请选择一个规则")
        else:
            info_text = f"""规则名称: {rule.name}
正则表达式: {rule.pattern}
组映射: {rule.groups}
输出格式: {rule.output_format}"""
            self.rule_info_text.insert(tk.END, info_text)
        
        self.rule_info_text.config(state=tk.DISABLED)
