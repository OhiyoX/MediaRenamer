#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则测试标签页
负责正则表达式测试和规则创建
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import json
import re
from typing import List

from libs.core.rule import RegexRule, RuleFileManager
from libs.core.file_manager import FileManager
from libs.core.auto_matcher import RuleMatcher
from libs.config import TREEVIEW_COLUMN_WIDTH, TEST_DEFAULT_FILENAME, TEST_DEFAULT_REGEX, TEST_DEFAULT_GROUPS, TEST_DEFAULT_FORMAT


class RuleTestingTab:
    """规则测试标签页"""
    
    def __init__(self, parent_notebook, rule_manager: RuleFileManager, rules: List[RegexRule]):
        self.parent_notebook = parent_notebook
        self.rule_manager = rule_manager
        self.rules = rules
        
        # 核心组件
        self.file_manager = FileManager()
        self.rule_matcher = RuleMatcher()
        
        # 数据
        self.test_dir = ""
        self.test_file_list: List[Path] = []
        
        # 创建界面
        self.create_widgets()
        
        # 初始化规则列表（在界面创建完成后）
        self.refresh_rule_list()
        
        # 初始化测试
        self.run_regex_test()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="规则测试")
        
        # 目录选择区域
        self.create_directory_section()
        
        # 规则选择区域
        self.create_rule_selection_section()
        
        # 测试输入区域
        self.create_input_section()
        
        # 正则表达式编辑区域
        self.create_regex_section()
        
        # 组映射编辑区域
        self.create_groups_section()
        
        # 输出格式编辑区域
        self.create_format_section()
        
        # 文件列表显示区域
        self.create_files_section()
        
        # 测试结果显示区域
        self.create_result_section()
        
        # 测试按钮
        self.create_button_section()
    
    def create_directory_section(self):
        """创建目录选择区域"""
        dir_frame = ttk.LabelFrame(self.frame, text="测试目录选择")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(dir_frame, text="选择测试目录", command=self.browse_test_directory).pack(side=tk.LEFT, padx=5)
        self.test_dir_label = ttk.Label(dir_frame, text="未选择目录")
        self.test_dir_label.pack(side=tk.LEFT, padx=10)
    
    def create_rule_selection_section(self):
        """创建规则选择区域"""
        rule_frame = ttk.LabelFrame(self.frame, text="规则选择与编辑")
        rule_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 规则选择下拉框
        rule_select_frame = ttk.Frame(rule_frame)
        rule_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(rule_select_frame, text="选择规则:").pack(side=tk.LEFT, padx=5)
        self.selected_rule_var = tk.StringVar()
        self.rule_combo = ttk.Combobox(rule_select_frame, textvariable=self.selected_rule_var, 
                                     state="readonly", width=30)
        self.rule_combo.pack(side=tk.LEFT, padx=5)
        self.rule_combo.bind('<<ComboboxSelected>>', self.on_rule_selected)
        
        # 按钮区域
        button_frame = ttk.Frame(rule_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="加载规则", command=self.load_selected_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存规则", command=self.save_current_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="新建规则", command=self.create_new_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除规则", command=self.delete_selected_rule).pack(side=tk.LEFT, padx=5)
        
        # 规则名称编辑
        name_frame = ttk.Frame(rule_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(name_frame, text="规则名称:").pack(side=tk.LEFT, padx=5)
        self.rule_name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.rule_name_var, width=40)
        name_entry.pack(side=tk.LEFT, padx=5)
        name_entry.bind('<KeyRelease>', self.on_rule_name_change)
        
        # 初始化规则列表
        self.refresh_rule_list()
    
    def refresh_rule_list(self):
        """刷新规则列表"""
        try:
            self.rule_manager = RuleFileManager()
            self.rules = self.rule_manager.load_all_rules()
            
            rule_names = [rule.name for rule in self.rules]
            self.rule_combo['values'] = rule_names
            
            if rule_names and not self.selected_rule_var.get():
                self.selected_rule_var.set(rule_names[0])
                # 只有在界面完全创建后才加载规则
                if hasattr(self, 'test_regex_var'):
                    self.load_selected_rule()
        except Exception as e:
            print(f"刷新规则列表失败: {e}")
    
    def on_rule_selected(self, event=None):
        """规则选择事件"""
        self.load_selected_rule()
    
    def load_selected_rule(self):
        """加载选中的规则"""
        selected_name = self.selected_rule_var.get()
        if not selected_name:
            return
        
        # 找到对应的规则
        selected_rule = None
        for rule in self.rules:
            if rule.name == selected_name:
                selected_rule = rule
                break
        
        if selected_rule:
            # 加载规则内容到编辑区域
            self.rule_name_var.set(selected_rule.name)
            self.test_regex_var.set(selected_rule.pattern)
            self.test_groups_var.set(json.dumps(selected_rule.groups, ensure_ascii=False, indent=2))
            self.test_format_var.set(selected_rule.output_format)
            
            # 触发测试
            self.test_single_file()
    
    def save_current_rule(self):
        """保存当前规则"""
        try:
            # 获取当前编辑的内容
            name = self.rule_name_var.get().strip()
            pattern = self.test_regex_var.get().strip()
            groups_str = self.test_groups_var.get().strip()
            output_format = self.test_format_var.get().strip()
            
            if not all([name, pattern, groups_str, output_format]):
                messagebox.showerror("错误", "请填写完整的规则信息")
                return
            
            # 解析组映射
            try:
                groups = json.loads(groups_str)
            except json.JSONDecodeError as e:
                messagebox.showerror("错误", f"组映射JSON格式错误: {e}")
                return
            
            # 创建规则对象
            from core.rule import RegexRule
            rule = RegexRule(name, pattern, groups, output_format)
            
            # 保存规则
            self.rule_manager.save_rule(rule)
            
            messagebox.showinfo("成功", f"规则 '{name}' 保存成功")
            
            # 刷新规则列表
            self.refresh_rule_list()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存规则失败: {e}")
    
    def create_new_rule(self):
        """创建新规则"""
        # 清空编辑区域
        self.rule_name_var.set("新规则")
        self.test_regex_var.set("")
        self.test_groups_var.set('{"title": 1}')
        self.test_format_var.set("{title}")
        
        # 清空选择
        self.selected_rule_var.set("")
    
    def delete_selected_rule(self):
        """删除选中的规则"""
        selected_name = self.selected_rule_var.get()
        if not selected_name:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
        
        # 确认删除
        result = messagebox.askyesno("确认删除", f"确定要删除规则 '{selected_name}' 吗？")
        if not result:
            return
        
        try:
            # 删除规则文件
            self.rule_manager.delete_rule(selected_name)
            messagebox.showinfo("成功", f"规则 '{selected_name}' 删除成功")
            
            # 刷新规则列表
            self.refresh_rule_list()
            
        except Exception as e:
            messagebox.showerror("错误", f"删除规则失败: {e}")
    
    def on_rule_name_change(self, event=None):
        """规则名称变化事件"""
        # 可以在这里添加实时验证逻辑
        pass
    
    def create_input_section(self):
        """创建测试输入区域"""
        input_frame = ttk.LabelFrame(self.frame, text="单个文件测试")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="测试文件名:").pack(anchor=tk.W, padx=5, pady=5)
        self.test_filename_var = tk.StringVar(value=TEST_DEFAULT_FILENAME)
        test_entry = ttk.Entry(input_frame, textvariable=self.test_filename_var, width=80)
        test_entry.pack(fill=tk.X, padx=5, pady=5)
        test_entry.bind('<KeyRelease>', self.on_test_input_change)
    
    def create_regex_section(self):
        """创建正则表达式编辑区域"""
        regex_frame = ttk.LabelFrame(self.frame, text="正则表达式编辑")
        regex_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(regex_frame, text="正则表达式:").pack(anchor=tk.W, padx=5, pady=5)
        self.test_regex_var = tk.StringVar(value=TEST_DEFAULT_REGEX)
        regex_entry = ttk.Entry(regex_frame, textvariable=self.test_regex_var, width=80)
        regex_entry.pack(fill=tk.X, padx=5, pady=5)
        regex_entry.bind('<KeyRelease>', self.on_regex_change)
    
    def create_groups_section(self):
        """创建组映射编辑区域"""
        groups_frame = ttk.LabelFrame(self.frame, text="组映射编辑")
        groups_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(groups_frame, text="组映射 (JSON格式):").pack(anchor=tk.W, padx=5, pady=5)
        self.test_groups_var = tk.StringVar(value=TEST_DEFAULT_GROUPS)
        groups_entry = ttk.Entry(groups_frame, textvariable=self.test_groups_var, width=80)
        groups_entry.pack(fill=tk.X, padx=5, pady=5)
        groups_entry.bind('<KeyRelease>', self.on_groups_change)
    
    def create_format_section(self):
        """创建输出格式编辑区域"""
        format_frame = ttk.LabelFrame(self.frame, text="输出格式编辑")
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(format_frame, text="输出格式:").pack(anchor=tk.W, padx=5, pady=5)
        self.test_format_var = tk.StringVar(value=TEST_DEFAULT_FORMAT)
        format_entry = ttk.Entry(format_frame, textvariable=self.test_format_var, width=80)
        format_entry.pack(fill=tk.X, padx=5, pady=5)
        format_entry.bind('<KeyRelease>', self.on_format_change)
    
    def create_files_section(self):
        """创建文件列表显示区域"""
        files_frame = ttk.LabelFrame(self.frame, text="目录文件列表")
        files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 文件列表工具栏
        files_toolbar = ttk.Frame(files_frame)
        files_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 复制按钮
        ttk.Button(files_toolbar, text="复制选中行", command=self.copy_selected_test_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(files_toolbar, text="复制所有行", command=self.copy_all_test_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(files_toolbar, text="复制所有行(含表头)", command=self.copy_all_test_files_with_header).pack(side=tk.LEFT, padx=5)
        
        # 创建文件列表Treeview
        columns = ('原文件名', '新文件名', '状态', '匹配信息')
        self.test_files_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=8)
        
        # 设置列标题和宽度
        for col in columns:
            self.test_files_tree.heading(col, text=col)
            self.test_files_tree.column(col, width=TREEVIEW_COLUMN_WIDTH)
        
        # 添加滚动条
        files_scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.test_files_tree.yview)
        self.test_files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        self.test_files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_result_section(self):
        """创建测试结果显示区域"""
        result_frame = ttk.LabelFrame(self.frame, text="单个文件测试结果")
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.test_result_text = scrolledtext.ScrolledText(result_frame, height=6, wrap=tk.WORD)
        self.test_result_text.pack(fill=tk.X, padx=5, pady=5)
    
    def create_button_section(self):
        """创建测试按钮"""
        test_button_frame = ttk.Frame(self.frame)
        test_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(test_button_frame, text="保存为规则", command=self.save_test_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_button_frame, text="刷新文件列表", command=self.scan_test_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_button_frame, text="自动匹配测试", command=self.auto_match_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_button_frame, text="清空", command=self.clear_test_inputs).pack(side=tk.LEFT, padx=5)
    
    def browse_test_directory(self):
        """浏览测试目录"""
        from tkinter import filedialog
        directory = filedialog.askdirectory()
        if directory:
            self.test_dir = directory
            self.test_dir_label.config(text=f"已选择: {directory}")
            self.scan_test_files()
    
    def scan_test_files(self):
        """扫描测试目录中的文件"""
        if not self.test_dir:
            return
        
        self.test_file_list = self.file_manager.scan_media_files(self.test_dir)
        # 更新文件列表显示
        self.update_test_files_display()
    
    def update_test_files_display(self):
        """更新测试文件列表显示"""
        # 清空现有项目
        for item in self.test_files_tree.get_children():
            self.test_files_tree.delete(item)
        
        if not self.test_file_list:
            return
        
        # 获取当前正则表达式和格式
        regex_pattern = self.test_regex_var.get().strip()
        groups_str = self.test_groups_var.get().strip()
        output_format = self.test_format_var.get().strip()
        
        if not all([regex_pattern, groups_str, output_format]):
            # 如果正则表达式不完整，只显示原文件名
            for file_path in self.test_file_list:
                filename = file_path.name
                self.test_files_tree.insert('', tk.END, values=(
                    filename, filename, "等待测试", "请完善正则表达式"
                ))
            return
        
        try:
            # 解析组映射
            groups = json.loads(groups_str)
            if not isinstance(groups, dict):
                raise ValueError("组映射必须是字典格式")
            
            # 测试正则表达式
            compiled_pattern = re.compile(regex_pattern)
            
            # 预览每个文件
            for file_path in self.test_file_list:
                filename = file_path.name
                extension = file_path.suffix
                
                # 尝试匹配
                match = compiled_pattern.search(filename)
                
                if match:
                    # 提取匹配信息
                    match_result = {}
                    for group_name, group_index in groups.items():
                        if group_index <= len(match.groups()):
                            match_result[group_name] = match.group(group_index)
                        else:
                            match_result[group_name] = ""
                    
                    # 生成输出文件名
                    try:
                        new_filename = output_format.format(**match_result) + extension
                        status = "匹配成功"
                        match_info = str(match_result)
                    except KeyError as e:
                        new_filename = filename
                        status = f"格式错误: 缺少 {e}"
                        match_info = "格式错误"
                else:
                    new_filename = filename
                    status = "匹配失败"
                    match_info = "无匹配"
                
                self.test_files_tree.insert('', tk.END, values=(
                    filename, new_filename, status, match_info
                ))
                
        except json.JSONDecodeError:
            # JSON格式错误
            for file_path in self.test_file_list:
                filename = file_path.name
                self.test_files_tree.insert('', tk.END, values=(
                    filename, filename, "JSON格式错误", "请检查组映射格式"
                ))
        except re.error:
            # 正则表达式错误
            for file_path in self.test_file_list:
                filename = file_path.name
                self.test_files_tree.insert('', tk.END, values=(
                    filename, filename, "正则表达式错误", "请检查正则表达式"
                ))
    
    def on_test_input_change(self, event=None):
        """测试输入变化事件"""
        self.run_regex_test()
    
    def on_regex_change(self, event=None):
        """正则表达式变化事件"""
        self.run_regex_test()
        self.update_test_files_display()
    
    def on_groups_change(self, event=None):
        """组映射变化事件"""
        self.run_regex_test()
        self.update_test_files_display()
    
    def on_format_change(self, event=None):
        """输出格式变化事件"""
        self.run_regex_test()
        self.update_test_files_display()
    
    def run_regex_test(self):
        """运行正则表达式测试"""
        self.test_result_text.delete(1.0, tk.END)
        
        filename = self.test_filename_var.get().strip()
        regex_pattern = self.test_regex_var.get().strip()
        groups_str = self.test_groups_var.get().strip()
        output_format = self.test_format_var.get().strip()
        
        if not filename:
            self.test_result_text.insert(tk.END, "请输入测试文件名")
            return
        
        if not regex_pattern:
            self.test_result_text.insert(tk.END, "请输入正则表达式")
            return
        
        if not groups_str:
            self.test_result_text.insert(tk.END, "请输入组映射")
            return
        
        if not output_format:
            self.test_result_text.insert(tk.END, "请输入输出格式")
            return
        
        try:
            # 解析组映射
            groups = json.loads(groups_str)
            if not isinstance(groups, dict):
                raise ValueError("组映射必须是字典格式")
            
            # 测试正则表达式
            compiled_pattern = re.compile(regex_pattern)
            match = compiled_pattern.search(filename)
            
            if match:
                # 提取匹配信息
                match_result = {}
                for group_name, group_index in groups.items():
                    if group_index <= len(match.groups()):
                        match_result[group_name] = match.group(group_index)
                    else:
                        match_result[group_name] = ""
                
                # 生成输出文件名
                extension = Path(filename).suffix
                try:
                    new_filename = output_format.format(**match_result) + extension
                except KeyError as e:
                    new_filename = f"格式错误: 缺少 {e}"
                
                # 显示结果
                result_text = f"""✅ 匹配成功！

原文件名: {filename}
新文件名: {new_filename}

匹配信息:
"""
                for key, value in match_result.items():
                    result_text += f"  {key}: {value}\n"
                
                result_text += f"""
正则表达式: {regex_pattern}
组映射: {groups}
输出格式: {output_format}"""
                
            else:
                result_text = f"""❌ 匹配失败！

文件名: {filename}
正则表达式: {regex_pattern}
组映射: {groups}
输出格式: {output_format}

请检查正则表达式是否正确。"""
            
            self.test_result_text.insert(tk.END, result_text)
            
        except json.JSONDecodeError as e:
            self.test_result_text.insert(tk.END, f"❌ 组映射JSON格式错误: {e}")
        except re.error as e:
            self.test_result_text.insert(tk.END, f"❌ 正则表达式错误: {e}")
        except Exception as e:
            self.test_result_text.insert(tk.END, f"❌ 测试失败: {e}")
    
    def save_test_rule(self):
        """保存测试规则"""
        name = f"自定义规则_{len(self.rules) + 1}"
        pattern = self.test_regex_var.get().strip()
        groups_str = self.test_groups_var.get().strip()
        output_format = self.test_format_var.get().strip()
        
        if not all([pattern, groups_str, output_format]):
            messagebox.showerror("错误", "请填写所有字段")
            return
        
        try:
            # 解析组映射
            groups = json.loads(groups_str)
            if not isinstance(groups, dict):
                raise ValueError("组映射必须是字典格式")
            
            # 测试正则表达式
            re.compile(pattern)
            
            # 创建规则
            rule = RegexRule(name, pattern, groups, output_format)
            
            # 保存规则
            if self.rule_manager.save_rule(rule):
                messagebox.showinfo("成功", f"规则 '{name}' 已保存")
                return True
            else:
                messagebox.showerror("错误", "保存规则失败")
                return False
                
        except Exception as e:
            messagebox.showerror("错误", f"保存规则失败: {e}")
            return False
    
    def copy_selected_test_files(self):
        """复制选中的测试文件行"""
        selection = self.test_files_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要复制的行")
            return
        
        # 获取列标题
        columns = [self.test_files_tree.heading(col)['text'] for col in self.test_files_tree['columns']]
        
        # 构建复制内容
        copy_content = []
        for item_id in selection:
            item = self.test_files_tree.item(item_id)
            values = item['values']
            # 将列标题和值组合成键值对
            row_data = []
            for i, value in enumerate(values):
                if i < len(columns):
                    row_data.append(f"{columns[i]}: {value}")
            copy_content.append(" | ".join(row_data))
        
        # 复制到剪贴板
        copy_text = "\n".join(copy_content)
        parent = self.parent_notebook.winfo_toplevel()
        parent.clipboard_clear()
        parent.clipboard_append(copy_text)
        parent.update()  # 确保剪贴板更新
        
        messagebox.showinfo("成功", f"已复制 {len(selection)} 行到剪贴板")
    
    def copy_all_test_files(self):
        """复制所有测试文件行（不含表头）"""
        items = self.test_files_tree.get_children()
        if not items:
            messagebox.showwarning("警告", "没有数据可复制")
            return
        
        # 获取列标题
        columns = [self.test_files_tree.heading(col)['text'] for col in self.test_files_tree['columns']]
        
        # 构建复制内容
        copy_content = []
        for item_id in items:
            item = self.test_files_tree.item(item_id)
            values = item['values']
            # 将列标题和值组合成键值对
            row_data = []
            for i, value in enumerate(values):
                if i < len(columns):
                    row_data.append(f"{columns[i]}: {value}")
            copy_content.append(" | ".join(row_data))
        
        # 复制到剪贴板
        copy_text = "\n".join(copy_content)
        parent = self.parent_notebook.winfo_toplevel()
        parent.clipboard_clear()
        parent.clipboard_append(copy_text)
        parent.update()  # 确保剪贴板更新
        
        messagebox.showinfo("成功", f"已复制 {len(items)} 行到剪贴板")
    
    def copy_all_test_files_with_header(self):
        """复制所有测试文件行（含表头）"""
        items = self.test_files_tree.get_children()
        if not items:
            messagebox.showwarning("警告", "没有数据可复制")
            return
        
        # 获取列标题
        columns = [self.test_files_tree.heading(col)['text'] for col in self.test_files_tree['columns']]
        
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
            item = self.test_files_tree.item(item_id)
            values = item['values']
            # 直接使用值，不添加列标题
            row_data = []
            for i, value in enumerate(values):
                if i < len(columns):
                    row_data.append(str(value))
            copy_content.append(" | ".join(row_data))
        
        # 复制到剪贴板
        copy_text = "\n".join(copy_content)
        parent = self.parent_notebook.winfo_toplevel()
        parent.clipboard_clear()
        parent.clipboard_append(copy_text)
        parent.update()  # 确保剪贴板更新
        
        messagebox.showinfo("成功", f"已复制 {len(items)} 行（含表头）到剪贴板")
    
    def clear_test_inputs(self):
        """清空测试输入"""
        self.test_filename_var.set(TEST_DEFAULT_FILENAME)
        self.test_regex_var.set(TEST_DEFAULT_REGEX)
        self.test_groups_var.set(TEST_DEFAULT_GROUPS)
        self.test_format_var.set(TEST_DEFAULT_FORMAT)
        self.test_result_text.delete(1.0, tk.END)
        
        # 清空文件列表
        for item in self.test_files_tree.get_children():
            self.test_files_tree.delete(item)
    
    def auto_match_test(self):
        """自动匹配测试"""
        if not self.test_file_list:
            messagebox.showwarning("警告", "请先选择测试目录并扫描文件")
            return
        
        if not self.rules:
            messagebox.showwarning("警告", "没有可用的规则")
            return
        
        # 执行自动匹配
        auto_results = self.rule_matcher.auto_match_files(self.test_file_list, self.rules)
        
        # 更新文件列表显示，显示自动匹配结果
        self.update_test_files_display_with_auto_match(auto_results)
        
        # 显示匹配统计
        matched_count = sum(1 for result in auto_results.values() if result['rule'])
        total_count = len(self.test_file_list)
        
        messagebox.showinfo("自动匹配测试完成", 
                           f"匹配结果：\n"
                           f"总文件数：{total_count}\n"
                           f"成功匹配：{matched_count}\n"
                           f"匹配率：{matched_count/total_count*100:.1f}%")
    
    def update_test_files_display_with_auto_match(self, auto_results):
        """更新测试文件列表显示（带自动匹配结果）"""
        # 清空现有项目
        for item in self.test_files_tree.get_children():
            self.test_files_tree.delete(item)
        
        if not self.test_file_list:
            return
        
        for file_path in self.test_file_list:
            filename = file_path.name
            extension = file_path.suffix
            
            # 获取自动匹配结果
            auto_result = auto_results.get(filename, {})
            auto_rule = auto_result.get('rule')
            auto_score = auto_result.get('score', 0)
            
            if auto_rule:
                # 使用自动匹配的规则
                match_result = auto_rule.match(filename)
                if match_result:
                    try:
                        new_filename = auto_rule.generate_output(match_result, extension)
                        status = f"自动匹配: {auto_rule.name}"
                        match_info = f"分数: {auto_score:.1f}"
                    except KeyError as e:
                        new_filename = filename
                        status = f"格式错误: 缺少 {e}"
                        match_info = "格式错误"
                else:
                    new_filename = filename
                    status = "自动匹配失败"
                    match_info = "无匹配"
            else:
                # 没有自动匹配结果
                new_filename = filename
                status = "无自动匹配"
                match_info = "建议手动测试"
            
            self.test_files_tree.insert('', tk.END, values=(
                filename, new_filename, status, match_info
            ))
    
    def update_rules(self, new_rules: List[RegexRule]):
        """更新规则列表"""
        self.rules = new_rules
