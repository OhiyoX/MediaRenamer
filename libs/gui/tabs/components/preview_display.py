#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Callable, Optional
from libs.config import TREEVIEW_COLUMN_WIDTH


class PreviewDisplay:
    """预览显示组件"""
    
    def __init__(self, parent_frame: ttk.Frame, main_window=None):
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        preview_frame = ttk.LabelFrame(self.parent_frame, text="重命名预览")
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
    
    def clear_preview(self):
        """清空预览"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
    
    def add_preview_item(self, original_name: str, new_name: str, status: str, 
                        applied_rule: str, match_info: str, match_score: str, 
                        rename_status: str = "未执行", is_duplicate: bool = False):
        """添加预览项"""
        item = self.preview_tree.insert('', tk.END, values=(
            original_name, new_name, status, applied_rule, match_info, match_score, rename_status
        ))
        
        # 如果是重复文件名，设置红色标签
        if is_duplicate:
            self.preview_tree.set(item, '新文件名', new_name + " ⚠️")
            self.preview_tree.item(item, tags=('duplicate',))
        
        return item
    
    def update_rename_status(self, detailed_results: List[Dict]):
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
        self._copy_to_clipboard(copy_text)
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
        self._copy_to_clipboard(copy_text)
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
        self._copy_to_clipboard(copy_text)
        messagebox.showinfo("成功", f"已复制 {len(items)} 行（含表头）到剪贴板")
    
    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        if self.main_window and hasattr(self.main_window, 'root'):
            self.main_window.root.clipboard_clear()
            self.main_window.root.clipboard_append(text)
            self.main_window.root.update()  # 确保剪贴板更新
        else:
            # 备用方案：使用父窗口
            parent = self.parent_frame.winfo_toplevel()
            parent.clipboard_clear()
            parent.clipboard_append(text)
            parent.update()
