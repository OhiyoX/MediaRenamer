#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理标签页 - 重构版本
负责文件选择、规则选择、预览和执行重命名
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Optional

from libs.core.rule import RegexRule, RuleFileManager
from libs.gui.tabs.components.directory_selector import DirectorySelector
from libs.gui.tabs.components.rule_selector import RuleSelector
from libs.gui.tabs.components.rule_detail_display import RuleDetailDisplay
from libs.gui.tabs.components.title_editor import TitleEditor
from libs.gui.tabs.components.preview_display import PreviewDisplay
from libs.gui.tabs.components.action_buttons import ActionButtons
from libs.gui.tabs.components.status_bar import StatusBar
from libs.gui.tabs.components.config_button import ConfigButton
from libs.core.config_manager import ConfigManager
from libs.gui.tabs.logic.file_processing_logic import FileProcessingLogic
from libs.gui.tabs.logic.result_handler import ResultHandler


class FileProcessingTab:
    """文件处理标签页 - 重构版本"""
    
    def __init__(self, parent_notebook, rule_manager: RuleFileManager, rules: List[RegexRule], main_window=None):
        self.parent_notebook = parent_notebook
        self.main_window = main_window
        
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 业务逻辑
        self.logic = FileProcessingLogic(rule_manager, rules)
        
        # 结果处理
        self.result_handler = ResultHandler(None)  # 将在create_widgets中设置
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="文件处理")
        
        # 设置结果处理的父框架
        self.result_handler.parent_frame = self.frame
        
        # 目录选择组件
        self.directory_selector = DirectorySelector(
            self.frame, 
            self.on_directory_selected
        )
        
        # 规则选择组件
        self.rule_selector = RuleSelector(
            self.frame,
            self.logic.rules,
            self.on_rule_selected,
            self.on_validate_rules,
            self.on_reload_rules,
            self.on_scan_files,
            self.on_clear_applied_rules,
            self.on_apply_rules_auto_first,
            self.on_batch_match_rules
        )
        
        # 规则详情显示组件
        self.rule_detail_display = RuleDetailDisplay(self.frame)
        
        # 剧集名编辑组件（集成文件夹识别功能）
        self.title_editor = TitleEditor(
            self.frame,
            self.on_title_change,
            self.on_apply_custom_title,
            self.on_clear_custom_title,
            self.on_apply_custom_season,
            self.config_manager
        )
        
        # 预览组件
        self.preview_display = PreviewDisplay(self.frame, self.main_window)
        
        # 操作按钮组件
        self.action_buttons = ActionButtons(
            self.frame,
            self.on_preview_rename,
            self.on_execute_rename,
            self.on_restore_filenames,
            self.on_view_rename_log,
            self.on_create_backup
        )
        
        # 状态栏组件
        self.status_bar = StatusBar(self.frame)
        
        # 配置按钮组件
        self.config_button = ConfigButton(
            self.frame,
            self.config_manager,
            self.on_config_changed
        )
        
        # 确保组件正确显示
        self.frame.update_idletasks()
        self.frame.update()
    
    # 事件处理方法
    def on_directory_selected(self, directory: str):
        """目录选择事件"""
        try:
            self.logic.scan_files(directory)
            self.status_bar.update_status(f"找到 {len(self.logic.file_list)} 个媒体文件")
            self.update_rule_info()
            self.update_apply_info()
            self.update_folder_recognition()  # 更新文件夹识别信息
            self.preview_rename()
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def on_rule_selected(self, event=None):
        """规则选择事件"""
        self.update_rule_info()
        self.update_apply_info()
        self.preview_rename()
    
    def on_validate_rules(self):
        """验证规则事件"""
        self.rule_selector.validate_all_rules()
    
    def on_reload_rules(self):
        """重新加载规则事件"""
        try:
            self.status_bar.reset_progress()
            self.status_bar.update_status("正在重新加载规则...")
            
            # 重新加载规则
            self.logic.reload_rules()
            
            # 更新界面
            self.rule_selector.update_rules(self.logic.rules)
            self.update_rule_info()
            self.update_apply_info()
            self.preview_rename()
            
            self.status_bar.update_status("规则重新加载完成")
            
        except Exception as e:
            self.status_bar.update_status(f"规则重新加载失败: {e}")
            messagebox.showerror("错误", f"重新加载规则失败: {e}")
    
    def on_scan_files(self):
        """扫描文件事件"""
        try:
            directory = self.directory_selector.get_current_directory()
            if not directory:
                messagebox.showerror("错误", "请先选择目录")
                return
            
            self.logic.scan_files(directory)
            self.status_bar.update_status(f"找到 {len(self.logic.file_list)} 个媒体文件")
            self.update_rule_info()
            self.update_apply_info()
            self.preview_rename()
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def on_clear_applied_rules(self):
        """清除应用规则事件"""
        self.logic.clear_all_applied_rules()
        self.preview_rename()
        self.update_apply_info()
        messagebox.showinfo("完成", "已清除所有应用规则")
    
    def on_apply_rules_auto_first(self):
        """应用规则（自动匹配优先）事件"""
        try:
            used_auto = self.logic.apply_rules_auto_first()
            
            if not used_auto:
                # 回退到手动选择
                selected_rule_name = self.rule_selector.get_selected_rule_name()
                if not selected_rule_name:
                    self.status_bar.update_status("警告: 未找到自动匹配结果，请先选择一个规则")
                    return
                self.logic.apply_manual_rule(selected_rule_name)
            
            # 更新预览与提示
            self.preview_rename()
            self.update_apply_info()
            
            if used_auto:
                self.status_bar.update_status("完成: 已应用自动匹配的规则到所有文件")
            else:
                self.status_bar.update_status("完成: 已应用手动选择的规则到所有文件")
                
        except Exception as e:
            self.status_bar.update_status(f"错误: {str(e)}")
            messagebox.showerror("错误", str(e))
    
    def on_batch_match_rules(self):
        """批量匹配规则事件"""
        try:
            # 执行自动匹配
            auto_match_results = self.logic.batch_match_suggested_rules()
            
            # 统计匹配结果
            matched_count = sum(1 for result in auto_match_results.values() if result['rule'])
            total_count = len(self.logic.file_list)
            
            # 显示匹配统计到状态栏
            match_rate = matched_count/total_count*100 if total_count > 0 else 0
            self.status_bar.update_status(
                f"批量匹配完成: 总文件数 {total_count}, 成功匹配 {matched_count}, 匹配率 {match_rate:.1f}%"
            )
            
            # 更新预览显示自动匹配结果
            self.preview_rename()
            
            # 更新应用规则信息
            self.update_apply_info()
            
            # 更新文件夹识别信息
            self.update_folder_recognition()
            
        except Exception as e:
            self.status_bar.update_status(f"错误: {str(e)}")
            messagebox.showerror("错误", str(e))
    
    def on_title_change(self, custom_title: str):
        """剧集名变化事件"""
        # 可以在这里添加实时预览逻辑
        pass
    
    def _apply_custom_settings(self, custom_title: str = None, custom_season: str = None):
        """统一的应用自定义设置方法"""
        if not self.logic.file_list:
            self.status_bar.update_status("没有文件需要处理")
            return
        
        # 更新预览
        self.preview_rename(custom_title=custom_title, custom_season=custom_season)
        
        # 更新状态栏
        status_parts = []
        if custom_title:
            status_parts.append(f"剧集名: '{custom_title}'")
        if custom_season:
            status_parts.append(f"季数: S{custom_season}")
        
        if status_parts:
            self.status_bar.update_status(f"已应用自定义设置: {', '.join(status_parts)}")
        else:
            self.status_bar.update_status("已更新预览")
    
    def on_apply_custom_title(self, custom_title: str):
        """应用自定义剧集名事件"""
        self._apply_custom_settings(custom_title=custom_title)
    
    def on_clear_custom_title(self):
        """清除自定义剧集名事件"""
        self._apply_custom_settings()
        self.status_bar.update_status("已清除自定义剧集名")
    
    def on_apply_custom_season(self, custom_season: str):
        """应用自定义季数事件"""
        self._apply_custom_settings(custom_season=custom_season)
    
    def on_preview_rename(self):
        """预览重命名事件"""
        self.preview_rename()
    
    def on_execute_rename(self):
        """执行重命名事件"""
        try:
            if not self.logic.file_list:
                messagebox.showwarning("警告", "没有文件需要处理")
                return
            
            # 检查是否有应用的规则
            if not self.logic.applied_rules:
                messagebox.showwarning("警告", "没有应用任何规则，请先应用规则")
                return
            
            # 统计要重命名的文件
            files_to_rename = []
            for file_path in self.logic.file_list:
                filename = file_path.name
                if filename in self.logic.applied_rules:
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
            
            # 获取自定义标题
            custom_title = self.title_editor.get_custom_title() or None
            
            # 执行重命名
            result = self.logic.execute_rename(custom_title, self.status_bar.update_progress)
            
            # 显示结果
            skipped_count = len(files_to_rename) - result['success_count'] - result['error_count']
            self.result_handler.show_rename_results(
                result['success_count'], 
                result['error_count'], 
                skipped_count, 
                result['detailed_results']
            )
            
            # 更新预览状态
            self.preview_display.update_rename_status(result['detailed_results'])
            
            # 更新应用规则信息
            self.update_apply_info()
            
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def on_restore_filenames(self):
        """恢复文件名事件"""
        try:
            # 显示恢复确认对话框
            rename_log = self.logic.load_rename_log()
            log_count = len(rename_log)
            result = messagebox.askyesno("确认恢复", 
                                       f"找到 {log_count} 条重命名记录\n\n"
                                       f"确定要恢复文件名吗？\n"
                                       f"这将把文件从新名称恢复为原始名称。")
            if not result:
                return
            
            # 执行恢复
            success_count, error_count, detailed_results = self.logic.restore_filenames()
            
            # 显示结果
            self.result_handler.show_restore_results(success_count, error_count, detailed_results)
            
            # 刷新文件列表
            self.on_scan_files()
            
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def on_view_rename_log(self):
        """查看重命名记录事件"""
        try:
            rename_log = self.logic.load_rename_log()
            directory_name = Path(self.logic.current_dir).name
            self.result_handler.show_rename_log(rename_log, directory_name)
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def on_create_backup(self):
        """创建备份事件"""
        try:
            backup_count, backup_dir = self.logic.create_backup()
            messagebox.showinfo("完成", f"备份完成！\n已备份 {backup_count} 个文件到 {backup_dir}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    # 辅助方法
    def update_rule_info(self):
        """更新规则详情显示"""
        selected_rule_name = self.rule_selector.get_selected_rule_name()
        if not selected_rule_name:
            self.rule_detail_display.update_rule_info(None)
            return
        
        # 找到选中的规则
        selected_rule = self.logic.get_rule_by_name(selected_rule_name)
        self.rule_detail_display.update_rule_info(selected_rule)
    
    def update_apply_info(self):
        """更新应用规则说明信息"""
        applied_count = self.logic.get_applied_rules_count()
        total_count = len(self.logic.file_list) if self.logic.file_list else 0
        self.rule_selector.update_apply_info(applied_count, total_count)
    
    def preview_rename(self, custom_title: str = None, custom_season: str = None):
        """预览重命名"""
        try:
            if not self.logic.file_list:
                return
            
            # 清空预览
            self.preview_display.clear_preview()
            
            # 获取自定义标题和季数
            if custom_title is None:
                custom_title = self.title_editor.get_custom_title() or None
            if custom_season is None:
                custom_season = self.title_editor.get_custom_season() or None
            
            # 预览每个文件
            preview_results = self.logic.preview_rename(custom_title, custom_season)
            
            # 插入预览结果到树形控件
            for preview_result in preview_results:
                result = preview_result['result']
                filename = preview_result['filename']
                new_filename = preview_result['new_filename']
                status = preview_result['status']
                applied_rule_name = preview_result['applied_rule_name']
                match_info = preview_result['match_info']
                match_score = preview_result['match_score']
                is_duplicate = preview_result['is_duplicate']
                folder_info = preview_result['folder_info']
                
                if result:
                    self.preview_display.add_preview_item(
                        result['original_name'],
                        result['new_name'],
                        status,
                        applied_rule_name,
                        match_info,
                        match_score,
                        "未执行",
                        is_duplicate,
                        folder_info
                    )
                else:
                    self.preview_display.add_preview_item(
                        filename,
                        filename,
                        status,
                        applied_rule_name,
                        match_info,
                        match_score,
                        "未执行",
                        is_duplicate,
                        folder_info
                    )
            
            # 配置重复文件名的标签样式
            self.preview_display.preview_tree.tag_configure('duplicate', foreground='red')
            
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def on_config_changed(self):
        """配置变更事件"""
        try:
            # 重新预览重命名结果
            self.preview_rename()
            self.status_bar.update_status("配置已更新，重新预览完成")
        except Exception as e:
            self.status_bar.update_status(f"配置更新失败: {e}")
    
    def update_folder_recognition(self):
        """更新文件夹识别信息"""
        try:
            if self.logic.file_list:
                # 获取当前应用的规则
                applied_rules = {}
                for filename in self.logic.file_list:
                    if filename.name in self.logic.applied_rules:
                        applied_rules[filename.name] = self.logic.applied_rules[filename.name]
                
                # 使用第一个文件的规则进行分析
                if applied_rules:
                    first_rule = list(applied_rules.values())[0]
                    self.title_editor.analyze_files(self.logic.file_list, first_rule)
                else:
                    self.title_editor.analyze_files(self.logic.file_list, None)
            else:
                self.title_editor._clear_folder_info()
                
        except Exception as e:
            self.status_bar.update_status(f"更新文件夹识别失败: {e}")
    
    def update_rules(self, new_rules: List[RegexRule]):
        """更新规则列表"""
        self.logic.rules = new_rules
        self.rule_selector.update_rules(new_rules)
        self.update_rule_info()
        self.preview_rename()
