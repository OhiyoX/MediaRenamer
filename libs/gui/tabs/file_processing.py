#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理标签页
负责文件选择、规则选择、预览和执行重命名
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from typing import List, Dict

from libs.core.rule import RegexRule, RuleFileManager
from libs.core.file_manager import FileManager
from libs.core.renamer import MediaRenamer
from libs.core.auto_matcher import RuleMatcher
from libs.config import TREEVIEW_COLUMN_WIDTH


class FileProcessingTab:
    """文件处理标签页"""
    
    def __init__(self, parent_notebook, rule_manager: RuleFileManager, rules: List[RegexRule], main_window=None):
        self.parent_notebook = parent_notebook
        self.rule_manager = rule_manager
        self.rules = rules
        self.main_window = main_window  # 保存主窗口引用
        
        # 核心组件
        self.file_manager = FileManager()
        self.renamer = MediaRenamer()
        self.rule_matcher = RuleMatcher()
        
        # 数据
        self.current_dir = ""
        self.file_list: List[Path] = []
        self.auto_match_results = {}
        self.applied_rules = {}  # 存储每个文件应用的规则
        
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
        
        # Title编辑区域
        self.create_title_edit_section()
        
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
        
        # 第一行：规则选择
        rule_select_frame = ttk.Frame(rule_frame)
        rule_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(rule_select_frame, text="选择规则:").pack(side=tk.LEFT, padx=5)
        self.rule_var = tk.StringVar()
        self.rule_combo = ttk.Combobox(rule_select_frame, textvariable=self.rule_var, width=30)
        self.rule_combo.pack(side=tk.LEFT, padx=5)
        self.rule_combo.bind('<<ComboboxSelected>>', self.on_rule_selected)
        
        # 更新规则下拉框
        self.update_rule_combo()
        
        # 第二行：操作按钮
        button_frame = ttk.Frame(rule_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="重新加载规则", command=self.reload_rules).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="扫描文件", command=self.scan_files).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="清除所有应用规则", command=self.clear_all_applied_rules).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="应用选中规则到所有文件", command=self.apply_selected_rule_to_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="自动匹配规则", command=self.batch_match_suggested_rules).pack(side=tk.RIGHT, padx=5)
        
        # 应用规则说明标签
        self.apply_info_label = ttk.Label(button_frame, text="", foreground="gray")
        self.apply_info_label.pack(side=tk.LEFT, padx=10)
        
        # 初始化应用规则信息
        self.update_apply_info()
    
    def apply_selected_rule_to_all(self):
        """应用选中的规则到所有文件"""
        selected_rule_name = self.rule_var.get()
        if not selected_rule_name:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
        
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件需要处理")
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
        
        # 应用规则到所有文件
        for file_path in self.file_list:
            filename = file_path.name
            self.applied_rules[filename] = selected_rule
        
        # 更新预览和应用信息
        self.preview_rename()
        self.update_apply_info()
        
        messagebox.showinfo("完成", f"已应用规则 '{selected_rule_name}' 到所有文件")
    
    def clear_all_applied_rules(self):
        """清除所有应用规则"""
        self.applied_rules.clear()
        self.preview_rename()
        self.update_apply_info()
        messagebox.showinfo("完成", "已清除所有应用规则")
    
    def update_apply_info(self):
        """更新应用规则说明信息"""
        applied_count = len(self.applied_rules)
        total_count = len(self.file_list) if self.file_list else 0
        
        if applied_count == 0:
            self.apply_info_label.config(text="没有应用任何规则")
        elif applied_count == total_count:
            self.apply_info_label.config(text=f"已应用规则到所有文件 ({applied_count}/{total_count})")
        else:
            self.apply_info_label.config(text=f"已应用规则到部分文件 ({applied_count}/{total_count})")
    
    
    def create_rule_detail_section(self):
        """创建规则详情显示区域"""
        rule_detail_frame = ttk.LabelFrame(self.frame, text="当前规则详情")
        rule_detail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 规则信息显示
        self.rule_info_text = scrolledtext.ScrolledText(rule_detail_frame, height=4, wrap=tk.WORD)
        self.rule_info_text.pack(fill=tk.X, padx=5, pady=5)
        self.rule_info_text.config(state=tk.DISABLED)
    
    def create_title_edit_section(self):
        """创建剧集名编辑区域"""
        title_frame = ttk.LabelFrame(self.frame, text="剧集名编辑")
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
        title_entry.bind('<KeyRelease>', self.on_title_change)
        
        # 剧集名应用按钮
        button_frame = ttk.Frame(title_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="应用剧集名到所有文件", command=self.apply_custom_title).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除自定义剧集名", command=self.clear_custom_title).pack(side=tk.LEFT, padx=5)
    
    def on_title_change(self, event=None):
        """剧集名变化事件"""
        # 可以在这里添加实时预览逻辑
        pass
    
    def apply_custom_title(self):
        """应用自定义剧集名到所有文件"""
        custom_title = self.custom_title_var.get().strip()
        if not custom_title:
            messagebox.showwarning("警告", "请输入自定义剧集名")
            return
        
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件需要处理")
            return
        
        # 更新预览
        self.preview_rename()
        messagebox.showinfo("完成", f"已应用自定义剧集名: '{custom_title}'\n请查看预览区域")
    
    def clear_custom_title(self):
        """清除自定义剧集名"""
        self.custom_title_var.set("")
        self.preview_rename()
        messagebox.showinfo("完成", "已清除自定义剧集名")
    
    def create_preview_section(self):
        """创建预览区域"""
        preview_frame = ttk.LabelFrame(self.frame, text="重命名预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 预览工具栏
        preview_toolbar = ttk.Frame(preview_frame)
        preview_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 复制按钮
        ttk.Button(preview_toolbar, text="复制选中行", command=self.copy_selected_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_toolbar, text="复制所有行", command=self.copy_all_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_toolbar, text="复制所有行(含表头)", command=self.copy_all_preview_with_header).pack(side=tk.LEFT, padx=5)
        
        # 创建Treeview用于显示预览
        columns = ('原文件名', '新文件名', '状态', '应用规则', '匹配信息', '匹配分数', '重命名状态')
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
        ttk.Button(button_frame, text="恢复文件名", command=self.restore_filenames).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看重命名记录", command=self.view_rename_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="创建备份", command=self.create_backup).pack(side=tk.RIGHT, padx=5)
    
    def create_status_section(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.frame)
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
    
    def progress_callback(self, current, total, filename, status):
        """进度回调函数"""
        # 更新进度条
        progress_percent = (current / total) * 100
        self.progress_var.set(progress_percent)
        
        # 更新进度标签
        self.progress_label_var.set(f"{current}/{total}")
        
        # 更新状态
        self.status_var.set(f"正在处理: {filename} - {status}")
        
        # 强制更新界面
        self.frame.update_idletasks()
    
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
        
        # 重置进度条
        self.progress_var.set(0)
        self.progress_label_var.set("0/0")
        self.status_var.set("正在扫描文件...")
        
        self.file_list = self.file_manager.scan_media_files(self.current_dir)
        self.status_var.set(f"找到 {len(self.file_list)} 个媒体文件")
        self.update_rule_info()
        self.update_apply_info()
        self.preview_rename()
    
    def reload_rules(self):
        """重新加载规则"""
        # 重置进度条
        self.progress_var.set(0)
        self.progress_label_var.set("0/0")
        self.status_var.set("正在重新加载规则...")
        
        try:
            # 重新加载规则
            self.rules = self.rule_manager.load_all_rules()
            
            # 更新界面
            self.update_rule_combo()
            self.update_rule_info()
            self.update_apply_info()
            self.preview_rename()
            
            self.status_var.set("规则重新加载完成")
            
        except Exception as e:
            self.status_var.set(f"规则重新加载失败: {e}")
            messagebox.showerror("错误", f"重新加载规则失败: {e}")
    
    def on_rule_selected(self, event=None):
        """规则选择事件"""
        self.update_rule_info()
        self.update_apply_info()
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
            applied_rule = selected_rule.name if result['success'] else "无"
            match_info = result['match_info'] if result['success'] else "无匹配"
            match_score = "N/A"  # 手动选择规则时没有匹配分数
            
            self.preview_tree.insert('', tk.END, values=(
                result['original_name'],
                result['new_name'],
                status,
                applied_rule,
                match_info,
                match_score,
                "未执行"
            ))
    
    def execute_rename(self):
        """执行重命名"""
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件需要处理")
            return
        
        # 检查是否有应用的规则
        if not self.applied_rules:
            messagebox.showwarning("警告", "没有应用任何规则，请先应用规则")
            return
        
        # 统计要重命名的文件
        files_to_rename = []
        for file_path in self.file_list:
            filename = file_path.name
            if filename in self.applied_rules:
                files_to_rename.append(file_path)
        
        if not files_to_rename:
            messagebox.showwarning("警告", "没有文件应用了规则")
            return
        
        # 显示确认对话框
        result = messagebox.askyesno("确认执行重命名", 
                                   f"即将重命名 {len(files_to_rename)} 个文件\n\n"
                                   f"确定要执行重命名吗？\n"
                                   f"建议先创建备份！")
        
        if not result:
            return
        
        # 执行重命名
        self._execute_rename_internal(files_to_rename)
    
    def _execute_rename_internal(self, files_to_rename):
        """执行重命名（内部方法）"""
        # 获取自定义标题
        custom_title = None
        if hasattr(self, 'custom_title_var') and self.custom_title_var.get().strip():
            custom_title = self.custom_title_var.get().strip()
        
        # 初始化进度
        self.progress_var.set(0)
        self.progress_label_var.set("准备重命名...")
        self.status_var.set("正在执行重命名...")
        
        success_count = 0
        error_count = 0
        detailed_results = []
        
        # 执行重命名
        for i, file_path in enumerate(files_to_rename):
            filename = file_path.name
            applied_rule = self.applied_rules[filename]
            
            try:
                # 更新进度
                self.progress_callback(i + 1, len(files_to_rename), filename, "处理中...")
                
                # 执行重命名
                success, new_filename, match_info = self.renamer.match_filename_with_rule(filename, applied_rule, custom_title)
                
                if success:
                    new_path = file_path.parent / new_filename
                    if new_path.exists() and new_path != file_path:
                        # 目标文件已存在 - 记录跳过操作
                        self.file_manager.log_rename(
                            str(file_path.parent), 
                            filename, 
                            new_filename, 
                            applied_rule.name,
                            "跳过",
                            "目标文件已存在"
                        )
                        detailed_results.append({
                            'original_name': filename,
                            'new_name': new_filename,
                            'status': '跳过',
                            'reason': '目标文件已存在'
                        })
                        self.progress_callback(i + 1, len(files_to_rename), filename, "跳过 - 目标文件已存在")
                    elif self.file_manager.rename_file(file_path, new_filename):
                        # 重命名成功 - 记录成功操作
                        self.file_manager.log_rename(
                            str(file_path.parent), 
                            filename, 
                            new_filename, 
                            applied_rule.name,
                            "成功",
                            "重命名成功"
                        )
                        success_count += 1
                        detailed_results.append({
                            'original_name': filename,
                            'new_name': new_filename,
                            'status': '成功',
                            'reason': '重命名成功'
                        })
                        self.progress_callback(i + 1, len(files_to_rename), filename, "成功")
                    else:
                        # 文件系统错误 - 记录失败操作
                        self.file_manager.log_rename(
                            str(file_path.parent), 
                            filename, 
                            new_filename, 
                            applied_rule.name,
                            "失败",
                            "文件系统错误"
                        )
                        error_count += 1
                        detailed_results.append({
                            'original_name': filename,
                            'new_name': new_filename,
                            'status': '失败',
                            'reason': '文件系统错误'
                        })
                        self.progress_callback(i + 1, len(files_to_rename), filename, "失败 - 文件系统错误")
                else:
                    # 规则匹配失败 - 记录失败操作
                    self.file_manager.log_rename(
                        str(file_path.parent), 
                        filename, 
                        filename, 
                        applied_rule.name,
                        "失败",
                        "规则匹配失败"
                    )
                    error_count += 1
                    detailed_results.append({
                        'original_name': filename,
                        'new_name': filename,
                        'status': '失败',
                        'reason': '规则匹配失败'
                    })
                    self.progress_callback(i + 1, len(files_to_rename), filename, "失败 - 规则匹配失败")
                    
            except Exception as e:
                # 异常情况 - 记录失败操作
                self.file_manager.log_rename(
                    str(file_path.parent), 
                    filename, 
                    filename, 
                    applied_rule.name if applied_rule else "未知",
                    "失败",
                    f"异常: {str(e)}"
                )
                error_count += 1
                detailed_results.append({
                    'original_name': filename,
                    'new_name': filename,
                    'status': '失败',
                    'reason': f'异常: {str(e)}'
                })
                self.progress_callback(i + 1, len(files_to_rename), filename, f"失败 - {str(e)}")
        
        # 更新状态
        self.status_var.set("重命名完成")
        self.progress_label_var.set("重命名完成")
        
        # 显示结果
        skipped_count = len(files_to_rename) - success_count - error_count
        self.show_rename_results(success_count, error_count, skipped_count, detailed_results)
        
        # 显示失败文件详情
        if error_count > 0:
            self.show_failed_files_details(detailed_results)
        
        # 更新预览状态
        self.update_preview_rename_status(detailed_results)
        
        # 清除应用的规则
        self.applied_rules.clear()
        self.update_apply_info()
    
    
    
    def _execute_manual_rename_with_confirmation(self):
        """执行手动选择规则的重命名（带确认）"""
        # 确认对话框
        result = messagebox.askyesno("确认", f"确定要重命名 {len(self.file_list)} 个文件吗？\n建议先创建备份！")
        if not result:
            return
        
        self._execute_manual_rename()
    
    def _execute_manual_rename(self):
        """执行手动选择规则的重命名（内部方法）"""
        
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
        
        # 获取自定义标题
        custom_title = None
        if hasattr(self, 'custom_title_var') and self.custom_title_var.get().strip():
            custom_title = self.custom_title_var.get().strip()
        
        # 重置进度条
        self.progress_var.set(0)
        self.progress_label_var.set("0/0")
        
        # 执行重命名
        success_count, error_count, detailed_results = self.renamer.execute_rename(
            self.file_list, selected_rule, custom_title, self.progress_callback
        )
        
        # 更新状态
        self.status_var.set("重命名完成")
        self.progress_var.set(100)
        
        # 更新预览树中的重命名状态
        self.update_preview_rename_status(detailed_results)
        
        # 显示详细结果
        skipped_count = len(self.file_list) - success_count - error_count
        self.show_rename_results(success_count, error_count, skipped_count, detailed_results)
        
        # 刷新文件列表
        self.scan_files()
    
    
    def _execute_auto_rename_with_confirmation(self):
        """执行自动匹配建议规则的重命名（带确认）"""
        if not hasattr(self, 'auto_match_results') or not self.auto_match_results:
            messagebox.showwarning("警告", "请先执行批量匹配建议规则")
            return
        
        # 统计建议规则
        rule_counts = {}
        for result in self.auto_match_results.values():
            if result['rule']:
                rule_name = result['rule'].name
                rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
        
        if not rule_counts:
            messagebox.showwarning("警告", "没有找到可用的建议规则")
            return
        
        # 显示建议规则统计
        stats_text = "建议规则统计:\n"
        for rule_name, count in rule_counts.items():
            stats_text += f"  {rule_name}: {count} 个文件\n"
        
        # 确认对话框
        result = messagebox.askyesno("确认执行自动匹配重命名", 
                                   f"{stats_text}\n\n确定要执行自动匹配重命名吗？\n"
                                   f"这将为每个文件应用最合适的规则。\n建议先创建备份！")
        if not result:
            return
        
        self._execute_auto_rename()
    
    def _execute_auto_rename(self):
        """执行自动匹配建议规则的重命名（内部方法）"""
        # 重置进度条
        self.progress_var.set(0)
        self.progress_label_var.set("0/0")
        
        # 执行批量应用
        applied_count = 0
        failed_count = 0
        detailed_results = []
        
        for i, (filename, auto_result) in enumerate(self.auto_match_results.items()):
            # 更新进度
            self.progress_callback(i + 1, len(self.auto_match_results), filename, "处理中...")
            
            if auto_result['rule']:
                # 找到对应的文件路径
                file_path = None
                for path in self.file_list:
                    if path.name == filename:
                        file_path = path
                        break
                
                if file_path:
                    # 使用建议的规则进行重命名
                    try:
                        match_result = auto_result['rule'].match(filename)
                        if match_result:
                            extension = file_path.suffix
                            new_filename = auto_result['rule'].generate_output(match_result, extension)
                            new_path = file_path.parent / new_filename
                            
                            # 检查是否已存在
                            if new_path.exists() and new_path != file_path:
                                failed_count += 1
                                detailed_results.append({
                                    'file_path': file_path,
                                    'original_name': filename,
                                    'new_name': new_filename,
                                    'status': '跳过',
                                    'reason': '目标文件已存在',
                                    'match_info': str(match_result)
                                })
                                self.progress_callback(i + 1, len(self.auto_match_results), filename, "跳过 - 目标文件已存在")
                                continue
                            
                            # 重命名
                            file_path.rename(new_path)
                            
                            # 记录重命名操作
                            self.file_manager.log_rename(
                                str(file_path.parent),
                                filename,
                                new_filename,
                                auto_result['rule'].name
                            )
                            
                            applied_count += 1
                            detailed_results.append({
                                'file_path': file_path,
                                'original_name': filename,
                                'new_name': new_filename,
                                'status': '成功',
                                'reason': '重命名成功',
                                'match_info': str(match_result)
                            })
                            self.progress_callback(i + 1, len(self.auto_match_results), filename, "成功")
                        else:
                            failed_count += 1
                            detailed_results.append({
                                'file_path': file_path,
                                'original_name': filename,
                                'new_name': filename,
                                'status': '失败',
                                'reason': '规则匹配失败',
                                'match_info': '无匹配'
                            })
                            self.progress_callback(i + 1, len(self.auto_match_results), filename, "失败 - 规则匹配失败")
                    except Exception as e:
                        failed_count += 1
                        detailed_results.append({
                            'file_path': file_path,
                            'original_name': filename,
                            'new_name': filename,
                            'status': '失败',
                            'reason': f'异常: {str(e)}',
                            'match_info': '无'
                        })
                        self.progress_callback(i + 1, len(self.auto_match_results), filename, f"失败 - {str(e)}")
                        print(f"重命名失败 {file_path}: {e}")
            else:
                failed_count += 1
                detailed_results.append({
                    'file_path': None,
                    'original_name': filename,
                    'new_name': filename,
                    'status': '失败',
                    'reason': '无自动匹配规则',
                    'match_info': '无匹配'
                })
                self.progress_callback(i + 1, len(self.auto_match_results), filename, "失败 - 无自动匹配规则")
        
        # 更新状态
        self.status_var.set("自动匹配重命名完成")
        self.progress_var.set(100)
        
        # 更新预览树中的重命名状态
        self.update_preview_rename_status(detailed_results)
        
        # 显示详细结果
        skipped_count = len(self.file_list) - applied_count - failed_count
        self.show_rename_results(applied_count, failed_count, skipped_count, detailed_results)
        
        # 刷新文件列表
        self.scan_files()
    
    def update_preview_rename_status(self, detailed_results):
        """更新预览树中的重命名状态"""
        if not detailed_results:
            return
            
        # 创建文件名到结果的映射
        result_map = {}
        for result in detailed_results:
            if isinstance(result, dict) and 'original_name' in result:
                result_map[result['original_name']] = result
        
        # 更新预览树中的状态
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, 'values'))
            if len(values) >= 7:  # 确保有足够的列
                original_name = values[0]
                if original_name in result_map:
                    result = result_map[original_name]
                    values[6] = result.get('status', '未知')  # 更新重命名状态列
                    self.preview_tree.item(item, values=values)
    
    def show_rename_results(self, success_count, error_count, skipped_count, detailed_results):
        """显示重命名结果"""
        # 确保detailed_results是列表
        if not isinstance(detailed_results, list):
            detailed_results = []
        
        # 统计各种状态
        status_counts = {}
        for result in detailed_results:
            if isinstance(result, dict) and 'status' in result:
                status = result['status']
                status_counts[status] = status_counts.get(status, 0) + 1
        
        # 构建结果文本
        result_text = f"重命名完成！\n\n"
        result_text += f"总文件数: {success_count + error_count + skipped_count}\n"
        result_text += f"成功: {success_count}\n"
        result_text += f"失败: {error_count}\n"
        result_text += f"跳过: {skipped_count}\n\n"
        
        # 添加详细状态统计
        if status_counts:
            result_text += "详细状态:\n"
            for status, count in status_counts.items():
                result_text += f"  {status}: {count}\n"
        
        # 显示结果对话框
        messagebox.showinfo("重命名完成", result_text)
        
        # 如果有失败的文件，显示详细错误信息
        failed_results = [r for r in detailed_results if isinstance(r, dict) and r.get('status') == '失败']
        if failed_results:
            self.show_failed_files_details(failed_results)
    
    def show_failed_files_details(self, failed_results):
        """显示失败文件的详细信息"""
        if not failed_results:
            return
        
        # 创建详细信息窗口
        detail_window = tk.Toplevel(self.frame)
        detail_window.title("重命名失败详情")
        detail_window.geometry("800x400")
        
        # 创建文本区域
        text_frame = ttk.Frame(detail_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 添加失败文件信息
        text_widget.insert(tk.END, f"失败文件详情 ({len(failed_results)} 个文件):\n\n")
        
        for i, result in enumerate(failed_results, 1):
            text_widget.insert(tk.END, f"{i}. 文件: {result['original_name']}\n")
            text_widget.insert(tk.END, f"   原因: {result['reason']}\n")
            text_widget.insert(tk.END, f"   匹配信息: {result['match_info']}\n\n")
        
        # 添加关闭按钮
        button_frame = ttk.Frame(detail_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=detail_window.destroy).pack(side=tk.RIGHT)
    
    def view_rename_log(self):
        """查看重命名记录"""
        if not self.current_dir:
            messagebox.showwarning("警告", "请先选择目录")
            return
        
        try:
            # 加载重命名记录
            rename_log = self.file_manager.load_rename_log(self.current_dir)
            
            if not rename_log:
                messagebox.showinfo("信息", "该目录下没有重命名记录")
                return
            
            # 创建记录查看窗口
            log_window = tk.Toplevel(self.frame)
            log_window.title(f"重命名记录 - {Path(self.current_dir).name}")
            log_window.geometry("1000x600")
            
            # 创建Treeview显示记录
            columns = ("时间", "原文件名", "新文件名", "状态", "原因", "规则")
            tree = ttk.Treeview(log_window, columns=columns, show="headings")
            
            # 设置列标题和宽度
            tree.heading("时间", text="时间")
            tree.heading("原文件名", text="原文件名")
            tree.heading("新文件名", text="新文件名")
            tree.heading("状态", text="状态")
            tree.heading("原因", text="原因")
            tree.heading("规则", text="规则")
            
            tree.column("时间", width=150)
            tree.column("原文件名", width=200)
            tree.column("新文件名", width=200)
            tree.column("状态", width=80)
            tree.column("原因", width=150)
            tree.column("规则", width=120)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(log_window, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # 插入记录数据
            for record in rename_log:
                timestamp = record.get('timestamp', '')
                old_name = record.get('old_name', '')
                new_name = record.get('new_name', '')
                status = record.get('status', '')
                reason = record.get('reason', '')
                rule_name = record.get('rule_name', '')
                
                # 格式化时间
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = timestamp
                
                tree.insert("", "end", values=(
                    formatted_time,
                    old_name,
                    new_name,
                    status,
                    reason,
                    rule_name
                ))
            
            # 布局
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 添加统计信息
            stats_frame = ttk.Frame(log_window)
            stats_frame.pack(fill=tk.X, padx=5, pady=5)
            
            success_count = sum(1 for r in rename_log if r.get('status') == '成功')
            failed_count = sum(1 for r in rename_log if r.get('status') == '失败')
            skipped_count = sum(1 for r in rename_log if r.get('status') == '跳过')
            
            stats_text = f"总计: {len(rename_log)} | 成功: {success_count} | 失败: {failed_count} | 跳过: {skipped_count}"
            ttk.Label(stats_frame, text=stats_text).pack()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载重命名记录失败: {e}")
    
    def copy_selected_preview(self):
        """复制选中的预览行"""
        selection = self.preview_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要复制的行")
            return
        
        # 获取列标题
        columns = [self.preview_tree.heading(col)['text'] for col in self.preview_tree['columns']]
        
        # 构建复制内容
        copy_content = []
        for item_id in selection:
            item = self.preview_tree.item(item_id)
            values = item['values']
            # 将列标题和值组合成键值对
            row_data = []
            for i, value in enumerate(values):
                if i < len(columns):
                    row_data.append(f"{columns[i]}: {value}")
            copy_content.append(" | ".join(row_data))
        
        # 复制到剪贴板
        copy_text = "\n".join(copy_content)
        if self.main_window and hasattr(self.main_window, 'root'):
            self.main_window.root.clipboard_clear()
            self.main_window.root.clipboard_append(copy_text)
            self.main_window.root.update()  # 确保剪贴板更新
        else:
            # 备用方案：使用父窗口
            parent = self.parent_notebook.winfo_toplevel()
            parent.clipboard_clear()
            parent.clipboard_append(copy_text)
            parent.update()
        
        messagebox.showinfo("成功", f"已复制 {len(selection)} 行到剪贴板")
    
    def copy_all_preview(self):
        """复制所有预览行（不含表头）"""
        items = self.preview_tree.get_children()
        if not items:
            messagebox.showwarning("警告", "没有数据可复制")
            return
        
        # 获取列标题
        columns = [self.preview_tree.heading(col)['text'] for col in self.preview_tree['columns']]
        
        # 构建复制内容
        copy_content = []
        for item_id in items:
            item = self.preview_tree.item(item_id)
            values = item['values']
            # 将列标题和值组合成键值对
            row_data = []
            for i, value in enumerate(values):
                if i < len(columns):
                    row_data.append(f"{columns[i]}: {value}")
            copy_content.append(" | ".join(row_data))
        
        # 复制到剪贴板
        copy_text = "\n".join(copy_content)
        if self.main_window and hasattr(self.main_window, 'root'):
            self.main_window.root.clipboard_clear()
            self.main_window.root.clipboard_append(copy_text)
            self.main_window.root.update()  # 确保剪贴板更新
        else:
            # 备用方案：使用父窗口
            parent = self.parent_notebook.winfo_toplevel()
            parent.clipboard_clear()
            parent.clipboard_append(copy_text)
            parent.update()
        
        messagebox.showinfo("成功", f"已复制 {len(items)} 行到剪贴板")
    
    def copy_all_preview_with_header(self):
        """复制所有预览行（含表头）"""
        items = self.preview_tree.get_children()
        if not items:
            messagebox.showwarning("警告", "没有数据可复制")
            return
        
        # 获取列标题
        columns = [self.preview_tree.heading(col)['text'] for col in self.preview_tree['columns']]
        
        # 构建复制内容
        copy_content = []
        
        # 添加表头
        header_row = " | ".join(columns)
        copy_content.append(header_row)
        
        # 添加分隔线
        separator = " | ".join(["-" * len(col) for col in columns])
        copy_content.append(separator)
        
        # 添加数据行
        for item_id in items:
            item = self.preview_tree.item(item_id)
            values = item['values']
            # 直接使用值，不添加列标题
            row_data = []
            for i, value in enumerate(values):
                if i < len(columns):
                    row_data.append(str(value))
            copy_content.append(" | ".join(row_data))
        
        # 复制到剪贴板
        copy_text = "\n".join(copy_content)
        if self.main_window and hasattr(self.main_window, 'root'):
            self.main_window.root.clipboard_clear()
            self.main_window.root.clipboard_append(copy_text)
            self.main_window.root.update()  # 确保剪贴板更新
        else:
            # 备用方案：使用父窗口
            parent = self.parent_notebook.winfo_toplevel()
            parent.clipboard_clear()
            parent.clipboard_append(copy_text)
            parent.update()
        
        messagebox.showinfo("成功", f"已复制 {len(items)} 行（含表头）到剪贴板")
    
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
    
    def restore_filenames(self):
        """恢复文件名"""
        if not self.current_dir:
            messagebox.showerror("错误", "请选择有效的目录")
            return
        
        # 检查是否存在重命名记录
        rename_log = self.file_manager.load_rename_log(self.current_dir)
        if not rename_log:
            messagebox.showwarning("警告", "没有找到重命名记录文件")
            return
        
        # 显示恢复确认对话框
        log_count = len(rename_log)
        result = messagebox.askyesno("确认恢复", 
                                   f"找到 {log_count} 条重命名记录\n\n"
                                   f"确定要恢复文件名吗？\n"
                                   f"这将把文件从新名称恢复为原始名称。")
        if not result:
            return
        
        # 执行恢复
        success_count, error_count, detailed_results = self.file_manager.restore_all_from_log(self.current_dir)
        
        # 显示结果
        self.show_restore_results(success_count, error_count, detailed_results)
        
        # 刷新文件列表
        self.scan_files()
    
    def show_restore_results(self, success_count: int, error_count: int, detailed_results: List[Dict]):
        """显示恢复结果"""
        # 创建结果窗口
        result_window = tk.Toplevel(self.frame)
        result_window.title("恢复结果")
        result_window.geometry("800x500")
        
        # 标题
        title_frame = ttk.Frame(result_window)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(title_frame, text="文件名恢复结果", font=("Arial", 14, "bold")).pack()
        
        # 统计信息
        stats_frame = ttk.Frame(result_window)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_text = f"总计: {success_count + error_count} | 成功: {success_count} | 失败: {error_count}"
        ttk.Label(stats_frame, text=stats_text, font=("Arial", 12)).pack()
        
        # 详细结果
        detail_frame = ttk.LabelFrame(result_window, text="详细结果")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview
        columns = ("原文件名", "新文件名", "状态", "原因")
        tree = ttk.Treeview(detail_frame, columns=columns, show="headings")
        
        # 设置列标题和宽度
        tree.heading("原文件名", text="原文件名")
        tree.heading("新文件名", text="新文件名")
        tree.heading("状态", text="状态")
        tree.heading("原因", text="原因")
        
        tree.column("原文件名", width=250)
        tree.column("新文件名", width=250)
        tree.column("状态", width=100)
        tree.column("原因", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 插入数据
        for result in detailed_results:
            old_name = result.get('old_name', '')
            new_name = result.get('new_name', '')
            status = result.get('status', '')
            reason = result.get('reason', '')
            
            tree.insert("", "end", values=(old_name, new_name, status, reason))
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮
        button_frame = ttk.Frame(result_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=result_window.destroy).pack(side=tk.RIGHT)
    
    def batch_match_suggested_rules(self):
        """批量匹配建议规则（仅匹配，不执行重命名）"""
        if not self.file_list:
            messagebox.showwarning("警告", "没有文件需要处理")
            return
        
        if not self.rules:
            messagebox.showwarning("警告", "没有可用的规则")
            return
        
        # 执行自动匹配
        self.auto_match_results = self.rule_matcher.auto_match_files(self.file_list, self.rules)
        
        # 统计匹配结果
        matched_count = sum(1 for result in self.auto_match_results.values() if result['rule'])
        total_count = len(self.file_list)
        
        # 显示匹配统计
        messagebox.showinfo("批量匹配完成", 
                           f"匹配结果：\n"
                           f"总文件数：{total_count}\n"
                           f"成功匹配：{matched_count}\n"
                           f"匹配率：{matched_count/total_count*100:.1f}%\n\n"
                           f"请查看预览区域，确认无误后点击'执行重命名'")
        
        # 应用自动匹配的规则
        for filename, auto_result in self.auto_match_results.items():
            if auto_result['rule']:
                self.applied_rules[filename] = auto_result['rule']
        
        # 更新预览显示自动匹配结果
        self.preview_rename()
        
        # 更新应用规则信息
        self.update_apply_info()
    
    
    def batch_apply_suggested_rules(self):
        """批量应用建议规则（已废弃，请使用自动匹配规则 + 执行重命名）"""
        messagebox.showinfo("提示", "此功能已更新！\n请使用：\n1. 自动匹配规则\n2. 执行重命名")
    
    def preview_rename(self):
        """预览重命名"""
        if not self.file_list:
            return
        
        # 清空预览
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # 获取自定义标题
        custom_title = None
        if hasattr(self, 'custom_title_var') and self.custom_title_var.get().strip():
            custom_title = self.custom_title_var.get().strip()
        
        # 收集所有新文件名，用于检测重复
        new_filenames = []
        preview_results = []
        
        # 预览每个文件
        for file_path in self.file_list:
            filename = file_path.name
            
            # 检查是否有应用的规则
            if filename in self.applied_rules:
                applied_rule = self.applied_rules[filename]
                # 使用应用的规则进行预览
                results = self.renamer.preview_rename([file_path], applied_rule, custom_title)
                if results:
                    result = results[0]
                    status = "已应用规则"
                    applied_rule_name = applied_rule.name
                    match_info = str(result['match_info'])
                    match_score = "N/A"
                    new_filename = result['new_name']
                else:
                    result = None
                    status = "应用规则失败"
                    applied_rule_name = applied_rule.name
                    match_info = "无匹配"
                    match_score = "N/A"
                    new_filename = filename
            else:
                # 没有应用规则
                result = None
                status = "未应用规则"
                applied_rule_name = "无"
                match_info = "请先应用规则"
                match_score = "N/A"
                new_filename = filename
            
            preview_results.append({
                'result': result,
                'filename': filename,
                'new_filename': new_filename,
                'status': status,
                'applied_rule_name': applied_rule_name,
                'match_info': match_info,
                'match_score': match_score
            })
            
            new_filenames.append(new_filename)
        
        # 检测重复的新文件名
        from collections import Counter
        filename_counts = Counter(new_filenames)
        duplicate_filenames = {name for name, count in filename_counts.items() if count > 1}
        
        # 插入预览结果到树形控件
        for preview_result in preview_results:
            result = preview_result['result']
            filename = preview_result['filename']
            new_filename = preview_result['new_filename']
            status = preview_result['status']
            applied_rule_name = preview_result['applied_rule_name']
            match_info = preview_result['match_info']
            match_score = preview_result['match_score']
            
            # 检查是否重复
            is_duplicate = new_filename in duplicate_filenames
            if is_duplicate:
                status = "重复文件名"
            
            if result:
                item = self.preview_tree.insert('', tk.END, values=(
                    result['original_name'],
                    result['new_name'],
                    status,
                    applied_rule_name,
                    match_info,
                    match_score,
                    "未执行"
                ))
            else:
                item = self.preview_tree.insert('', tk.END, values=(
                    filename,
                    filename,
                    status,
                    applied_rule_name,
                    match_info,
                    match_score,
                    "未执行"
                ))
            
            # 如果是重复文件名，设置红色标签
            if is_duplicate:
                self.preview_tree.set(item, '新文件名', new_filename + " ⚠️")
                # 设置行颜色为红色
                self.preview_tree.item(item, tags=('duplicate',))
        
        # 配置重复文件名的标签样式
        self.preview_tree.tag_configure('duplicate', foreground='red')
    
    def update_rules(self, new_rules: List[RegexRule]):
        """更新规则列表"""
        self.rules = new_rules
        self.update_rule_combo()
        self.update_rule_info()
        self.preview_rename()
