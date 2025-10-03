#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理业务逻辑
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
from pathlib import Path
from typing import List, Dict, Optional, Callable
from collections import Counter

from libs.core.rule import RegexRule, RuleFileManager
from libs.core.file_manager import FileManager
from libs.core.renamer import MediaRenamer
from libs.core.auto_matcher import RuleMatcher


class FileProcessingLogic:
    """文件处理业务逻辑"""
    
    def __init__(self, rule_manager: RuleFileManager, rules: List[RegexRule]):
        self.rule_manager = rule_manager
        self.rules = rules
        
        # 核心组件
        self.file_manager = FileManager()
        self.renamer = MediaRenamer()
        self.rule_matcher = RuleMatcher()
        
        # 数据
        self.current_dir = ""
        self.file_list: List[Path] = []
        self.auto_match_results = {}
        self.applied_rules = {}  # 存储每个文件应用的规则
    
    def scan_files(self, directory: str) -> List[Path]:
        """扫描文件"""
        if not directory:
            raise ValueError("请选择有效的目录")
        
        self.current_dir = directory
        self.file_list = self.file_manager.scan_media_files(directory)
        return self.file_list
    
    def reload_rules(self) -> List[RegexRule]:
        """重新加载规则"""
        self.rules = self.rule_manager.load_all_rules()
        return self.rules
    
    def get_rule_by_name(self, rule_name: str) -> Optional[RegexRule]:
        """根据名称获取规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def batch_match_suggested_rules(self) -> Dict[str, Dict]:
        """批量匹配建议规则"""
        if not self.file_list:
            raise ValueError("没有文件需要处理")
        
        if not self.rules:
            raise ValueError("没有可用的规则")
        
        # 执行自动匹配
        self.auto_match_results = self.rule_matcher.auto_match_files(self.file_list, self.rules)
        
        # 应用自动匹配的规则
        for filename, auto_result in self.auto_match_results.items():
            if auto_result['rule']:
                self.applied_rules[filename] = auto_result['rule']
        
        return self.auto_match_results
    
    def apply_rules_auto_first(self) -> bool:
        """应用规则：若已进行自动匹配，则使用自动匹配结果，否则使用手动选择的规则"""
        if not self.file_list:
            raise ValueError("没有文件需要处理")
        
        used_auto = False
        # 优先使用自动匹配结果
        if hasattr(self, 'auto_match_results') and self.auto_match_results:
            for filename, result in self.auto_match_results.items():
                rule = result.get('rule')
                file_path = result.get('file_path')
                if rule and file_path:
                    self.applied_rules[filename] = rule
                    used_auto = True
        
        return used_auto
    
    def apply_manual_rule(self, rule_name: str):
        """应用手动选择的规则"""
        if not self.file_list:
            raise ValueError("没有文件需要处理")
        
        selected_rule = self.get_rule_by_name(rule_name)
        if not selected_rule:
            raise ValueError("规则不存在")
        
        for file_path in self.file_list:
            filename = file_path.name
            self.applied_rules[filename] = selected_rule
    
    def clear_all_applied_rules(self):
        """清除所有应用规则"""
        self.applied_rules.clear()
    
    def get_applied_rules_count(self) -> int:
        """获取已应用规则的数量"""
        return len(self.applied_rules)
    
    def preview_rename(self, custom_title: Optional[str] = None, custom_season: Optional[str] = None) -> List[Dict]:
        """预览重命名"""
        if not self.file_list:
            return []
        
        preview_results = []
        new_filenames = []
        
        # 预览每个文件
        for file_path in self.file_list:
            filename = file_path.name
            
            # 检查是否有应用的规则
            if filename in self.applied_rules:
                applied_rule = self.applied_rules[filename]
                # 使用应用的规则进行预览
                results = self.renamer.preview_rename([file_path], applied_rule, custom_title, custom_season)
                if results:
                    result = results[0]
                    status = "已应用规则"
                    applied_rule_name = applied_rule.name
                    match_info = str(result['match_info'])
                    # 计算匹配分数
                    match_score = self.rule_matcher.calculate_rule_score(applied_rule, filename)
                    match_score = f"{match_score:.1f}" if match_score > 0 else "0.0"
                    new_filename = result['new_name']
                else:
                    result = None
                    status = "应用规则失败"
                    applied_rule_name = applied_rule.name
                    match_info = "无匹配"
                    match_score = "0.0"
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
                'match_score': match_score,
                'folder_info': result.get('folder_info', {}) if result else {}
            })
            
            new_filenames.append(new_filename)
        
        # 检测重复的新文件名
        filename_counts = Counter(new_filenames)
        duplicate_filenames = {name for name, count in filename_counts.items() if count > 1}
        
        # 标记重复文件名
        for preview_result in preview_results:
            preview_result['is_duplicate'] = preview_result['new_filename'] in duplicate_filenames
        
        return preview_results
    
    def execute_rename(self, custom_title: Optional[str] = None, 
                      progress_callback: Optional[Callable] = None) -> Dict:
        """执行重命名"""
        if not self.file_list:
            raise ValueError("没有文件需要处理")
        
        # 检查是否有应用的规则
        if not self.applied_rules:
            raise ValueError("没有应用任何规则，请先应用规则")
        
        # 统计要重命名的文件
        files_to_rename = []
        for file_path in self.file_list:
            filename = file_path.name
            if filename in self.applied_rules:
                files_to_rename.append(file_path)
        
        if not files_to_rename:
            raise ValueError("没有文件应用了规则")
        
        success_count = 0
        error_count = 0
        detailed_results = []
        
        # 执行重命名
        for i, file_path in enumerate(files_to_rename):
            filename = file_path.name
            applied_rule = self.applied_rules[filename]
            
            try:
                # 更新进度
                if progress_callback:
                    progress_callback(i + 1, len(files_to_rename), filename, "处理中...")
                
                # 执行重命名
                success, new_filename, match_info = self.renamer.match_filename_with_rule(filename, applied_rule, custom_title, str(file_path), None)
                
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
                        if progress_callback:
                            progress_callback(i + 1, len(files_to_rename), filename, "跳过 - 目标文件已存在")
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
                        if progress_callback:
                            progress_callback(i + 1, len(files_to_rename), filename, "成功")
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
                        if progress_callback:
                            progress_callback(i + 1, len(files_to_rename), filename, "失败 - 文件系统错误")
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
                    if progress_callback:
                        progress_callback(i + 1, len(files_to_rename), filename, "失败 - 规则匹配失败")
                    
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
                if progress_callback:
                    progress_callback(i + 1, len(files_to_rename), filename, f"失败 - {str(e)}")
        
        # 清除应用的规则
        self.applied_rules.clear()
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'detailed_results': detailed_results
        }
    
    def create_backup(self) -> tuple[int, str]:
        """创建备份"""
        if not self.current_dir:
            raise ValueError("请选择有效的目录")
        
        if not self.file_list:
            raise ValueError("没有文件需要备份")
        
        return self.file_manager.create_backup(self.current_dir, self.file_list)
    
    def restore_filenames(self) -> tuple[int, int, List[Dict]]:
        """恢复文件名"""
        if not self.current_dir:
            raise ValueError("请选择有效的目录")
        
        # 检查是否存在重命名记录
        rename_log = self.file_manager.load_rename_log(self.current_dir)
        if not rename_log:
            raise ValueError("没有找到重命名记录文件")
        
        return self.file_manager.restore_all_from_log(self.current_dir)
    
    def load_rename_log(self) -> List[Dict]:
        """加载重命名记录"""
        if not self.current_dir:
            raise ValueError("请选择有效的目录")
        
        return self.file_manager.load_rename_log(self.current_dir)
