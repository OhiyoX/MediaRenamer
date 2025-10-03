#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理标签页
负责文件选择、规则选择、预览和执行重命名
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from typing import List

from libs.core.rule import RegexRule, RuleFileManager
from libs.core.file_manager import FileManager
from libs.core.renamer import MediaRenamer
from libs.config import TREEVIEW_COLUMN_WIDTH


class FileProcessingTab:
    """文件处理标签页"""
    
    def __init__(self, parent_notebook, rule_manager: RuleFileManager, rules: List[RegexRule]):
        self.parent_notebook = parent_notebook
        self.rule_manager = rule_manager
        self.rules = rules
        
        # 核心组件
        self.file_manager = FileManager()
        self.renamer = MediaRenamer()
        
        # 数据
        self.current_dir = ""
        self.file_list: List[Path] = []
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="文件处理")
        
        # 目录选择区域
        self.create_directory_section()
        
        # 规则选择区域
        self.create_rule_section()
        
        # 规则详情显示区域
        self.create_rule_detail_section()
        
        # 预览区域
        self.create_preview_section()
        
        # 操作按钮区域
        self.create_button_section()
        
        # 状态栏
        self.create_status_section()
    
    def create_directory_section(self):
        """创建目录选择区域"""
        dir_frame = ttk.LabelFrame(self.frame, text="目录选择")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(dir_frame, text="选择目录", command=self.browse_directory).pack(side=tk.LEFT, padx=5)
        self.dir_label = ttk.Label(dir_frame, text="未选择目录")
        self.dir_label.pack(side=tk.LEFT, padx=10)
    
    def create_rule_section(self):
        """创建规则选择区域"""
        rule_frame = ttk.LabelFrame(self.frame, text="规则选择")
        rule_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(rule_frame, text="选择规则:").pack(side=tk.LEFT, padx=5)
        self.rule_var = tk.StringVar()
        self.rule_combo = ttk.Combobox(rule_frame, textvariable=self.rule_var, width=30)
        self.rule_combo.pack(side=tk.LEFT, padx=5)
        self.rule_combo.bind('<<ComboboxSelected>>', self.on_rule_selected)
        
        # 更新规则下拉框
        self.update_rule_combo()
        
        ttk.Button(rule_frame, text="重新加载规则", command=self.reload_rules).pack(side=tk.RIGHT, padx=5)
        ttk.Button(rule_frame, text="扫描文件", command=self.scan_files).pack(side=tk.RIGHT, padx=5)
    
    def create_rule_detail_section(self):
        """创建规则详情显示区域"""
        rule_detail_frame = ttk.LabelFrame(self.frame, text="当前规则详情")
        rule_detail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 规则信息显示
        self.rule_info_text = scrolledtext.ScrolledText(rule_detail_frame, height=4, wrap=tk.WORD)
        self.rule_info_text.pack(fill=tk.X, padx=5, pady=5)
        self.rule_info_text.config(state=tk.DISABLED)
    
    def create_preview_section(self):
        """创建预览区域"""
        preview_frame = ttk.LabelFrame(self.frame, text="重命名预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview用于显示预览
        columns = ('原文件名', '新文件名', '状态', '匹配信息')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        for col in columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=TREEVIEW_COLUMN_WIDTH)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)
        
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_button_section(self):
        """创建操作按钮区域"""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="预览重命名", command=self.preview_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="执行重命名", command=self.execute_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="创建备份", command=self.create_backup).pack(side=tk.RIGHT, padx=5)
    
    def create_status_section(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=5)
    
    def update_rule_combo(self):
        """更新规则下拉框"""
        rule_names = [rule.name for rule in self.rules]
        self.rule_combo['values'] = rule_names
        if rule_names and not self.rule_var.get():
            self.rule_combo.set(rule_names[0])
    
    def browse_directory(self):
        """浏览目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.current_dir = directory
            self.dir_label.config(text=f"已选择: {directory}")
            self.scan_files()
    
    def scan_files(self):
        """扫描文件"""
        if not self.current_dir:
            messagebox.showerror("错误", "请选择有效的目录")
            return
        
        self.file_list = self.file_manager.scan_video_files(self.current_dir)
        self.status_var.set(f"找到 {len(self.file_list)} 个媒体文件")
        self.update_rule_info()
        self.preview_rename()
    
    def reload_rules(self):
        """重新加载规则"""
        self.rules = self.rule_manager.load_all_rules()
        self.update_rule_combo()
        self.update_rule_info()
        self.preview_rename()
    
    def on_rule_selected(self, event=None):
        """规则选择事件"""
        self.update_rule_info()
        self.preview_rename()
    
    def update_rule_info(self):
        """更新规则详情显示"""
        selected_rule_name = self.rule_var.get()
        if not selected_rule_name:
            self.rule_info_text.config(state=tk.NORMAL)
            self.rule_info_text.delete(1.0, tk.END)
            self.rule_info_text.insert(tk.END, "请选择一个规则")
            self.rule_info_text.config(state=tk.DISABLED)
            return
        
        # 找到选中的规则
        selected_rule = None
        for rule in self.rules:
            if rule.name == selected_rule_name:
                selected_rule = rule
                break
        
        if not selected_rule:
            return
        
        # 更新规则信息显示
        self.rule_info_text.config(state=tk.NORMAL)
        self.rule_info_text.delete(1.0, tk.END)
        
        info_text = f"""规则名称: {selected_rule.name}
正则表达式: {selected_rule.pattern}
组映射: {selected_rule.groups}
输出格式: {selected_rule.output_format}"""
        
        self.rule_info_text.insert(tk.END, info_text)
        self.rule_info_text.config(state=tk.DISABLED)
    
    def preview_rename(self):
        """预览重命名"""
        if not self.file_list:
            return
        
        selected_rule_name = self.rule_var.get()
        if not selected_rule_name:
            return
        
        # 找到选中的规则
        selected_rule = None
        for rule in self.rules:
            if rule.name == selected_rule_name:
                selected_rule = rule
                break
        
        if not selected_rule:
            return
        
        # 清空预览
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # 预览每个文件
        results = self.renamer.preview_rename(self.file_list, selected_rule)
        
        for result in results:
            status = "匹配成功" if result['success'] else "匹配失败"
            self.preview_tree.insert('', tk.END, values=(
                result['original_name'],
                result['new_name'],
                status,
                result['match_info']
            ))
    
    def execute_rename(self):
        """执行重命名"""
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件需要重命名")
            return
        
        # 确认对话框
        result = messagebox.askyesno("确认", f"确定要重命名 {len(self.file_list)} 个文件吗？\n建议先创建备份！")
        if not result:
            return
        
        selected_rule_name = self.rule_var.get()
        if not selected_rule_name:
            messagebox.showerror("错误", "请选择规则")
            return
        
        # 找到选中的规则
        selected_rule = None
        for rule in self.rules:
            if rule.name == selected_rule_name:
                selected_rule = rule
                break
        
        if not selected_rule:
            messagebox.showerror("错误", "规则不存在")
            return
        
        # 执行重命名
        success_count, error_count = self.renamer.execute_rename(self.file_list, selected_rule)
        
        # 显示结果
        messagebox.showinfo("完成", f"重命名完成！\n成功: {success_count}\n失败: {error_count}")
        
        # 刷新文件列表
        self.scan_files()
    
    def create_backup(self):
        """创建备份"""
        if not self.current_dir:
            messagebox.showerror("错误", "请选择有效的目录")
            return
        
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件需要备份")
            return
        
        backup_count, backup_dir = self.file_manager.create_backup(self.current_dir, self.file_list)
        messagebox.showinfo("完成", f"备份完成！\n已备份 {backup_count} 个文件到 {backup_dir}")
    
    def update_rules(self, new_rules: List[RegexRule]):
        """更新规则列表"""
        self.rules = new_rules
        self.update_rule_combo()
        self.update_rule_info()
        self.preview_rename()
