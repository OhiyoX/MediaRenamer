#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理标签页
负责规则的查看、删除等管理操作
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import platform
from typing import List

from libs.core.rule import RegexRule, RuleFileManager


class RuleManagementTab:
    """规则管理标签页"""
    
    def __init__(self, parent_notebook, rule_manager: RuleFileManager, rules: List[RegexRule]):
        self.parent_notebook = parent_notebook
        self.rule_manager = rule_manager
        self.rules = rules
        
        # 创建界面
        self.create_widgets()
        
        # 加载规则列表
        self.refresh_rules_list()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="规则管理")
        
        # 规则列表区域
        self.create_rules_section()
        
        # 规则操作按钮
        self.create_button_section()
    
    def create_rules_section(self):
        """创建规则列表区域"""
        list_frame = ttk.LabelFrame(self.frame, text="规则列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 规则列表
        self.rules_tree = ttk.Treeview(list_frame, columns=('name', 'pattern'), show='headings', height=15)
        self.rules_tree.heading('name', text='规则名称')
        self.rules_tree.heading('pattern', text='正则表达式')
        self.rules_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_button_section(self):
        """创建规则操作按钮"""
        rules_button_frame = ttk.Frame(self.frame)
        rules_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(rules_button_frame, text="刷新列表", command=self.refresh_rules_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(rules_button_frame, text="删除规则", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(rules_button_frame, text="打开规则文件夹", command=self.open_rules_folder).pack(side=tk.RIGHT, padx=5)
    
    def refresh_rules_list(self):
        """刷新规则列表显示"""
        # 清空现有项目
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # 添加规则
        for rule in self.rules:
            self.rules_tree.insert('', tk.END, values=(rule.name, rule.pattern))
    
    def delete_rule(self):
        """删除规则"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的规则")
            return
        
        item = self.rules_tree.item(selection[0])
        rule_name = item['values'][0]
        
        result = messagebox.askyesno("确认", f"确定要删除规则 '{rule_name}' 吗？")
        if result:
            if self.rule_manager.delete_rule(rule_name):
                # 从规则列表中移除
                self.rules = [rule for rule in self.rules if rule.name != rule_name]
                self.refresh_rules_list()
                messagebox.showinfo("成功", f"规则 '{rule_name}' 已删除")
                return True
            else:
                messagebox.showerror("错误", "删除规则失败")
                return False
        return False
    
    def open_rules_folder(self):
        """打开规则文件夹"""
        rules_path = self.rule_manager.rules_dir.absolute()
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(rules_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(rules_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(rules_path)])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
    
    def update_rules(self, new_rules: List[RegexRule]):
        """更新规则列表"""
        self.rules = new_rules
        self.refresh_rules_list()
