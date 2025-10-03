#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果处理组件
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class ResultHandler:
    """结果处理组件"""
    
    def __init__(self, parent_frame: ttk.Frame):
        self.parent_frame = parent_frame
    
    def show_rename_results(self, success_count: int, error_count: int, 
                          skipped_count: int, detailed_results: List[Dict]):
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
    
    def show_failed_files_details(self, failed_results: List[Dict]):
        """显示失败文件的详细信息"""
        if not failed_results:
            return
        
        # 创建详细信息窗口
        detail_window = tk.Toplevel(self.parent_frame)
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
            text_widget.insert(tk.END, f"   匹配信息: {result.get('match_info', '无')}\n\n")
        
        # 添加关闭按钮
        button_frame = ttk.Frame(detail_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=detail_window.destroy).pack(side=tk.RIGHT)
    
    def show_restore_results(self, success_count: int, error_count: int, detailed_results: List[Dict]):
        """显示恢复结果"""
        # 创建结果窗口
        result_window = tk.Toplevel(self.parent_frame)
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
    
    def show_rename_log(self, rename_log: List[Dict], directory_name: str):
        """显示重命名记录"""
        if not rename_log:
            messagebox.showinfo("信息", "该目录下没有重命名记录")
            return
        
        # 创建记录查看窗口
        log_window = tk.Toplevel(self.parent_frame)
        log_window.title(f"重命名记录 - {directory_name}")
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
