#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重命名逻辑模块
负责文件重命名的核心逻辑
"""

from pathlib import Path
from typing import List, Dict, Tuple, Optional

from libs.core.rule import RegexRule
from libs.core.file_manager import FileManager


class MediaRenamer:
    """媒体文件重命名器"""
    
    def __init__(self):
        self.file_manager = FileManager()
    
    def clean_filename(self, filename: str) -> str:
        """
        清理文件名，移除或替换非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        if not filename:
            return filename
        
        import re
        
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        cleaned = filename
        
        for char in illegal_chars:
            if char in cleaned:
                if char in ':/\\':
                    cleaned = cleaned.replace(char, '-')
                elif char in '<>|?*':
                    cleaned = cleaned.replace(char, '')
                elif char == '"':
                    cleaned = cleaned.replace(char, "'")
        
        # 移除连续的空格和点
        cleaned = re.sub(r'\s+', ' ', cleaned)  # 多个空格合并为一个
        cleaned = re.sub(r'\.+', '.', cleaned)  # 多个点合并为一个
        cleaned = re.sub(r'-+', '-', cleaned)   # 多个横线合并为一个
        
        # 移除开头和结尾的空格、点、横线
        cleaned = cleaned.strip(' .-')
        
        # 确保文件名不为空
        if not cleaned:
            cleaned = "unnamed"
        
        # 检查Windows保留名称
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        name_without_ext = Path(cleaned).stem.upper()
        if name_without_ext in reserved_names:
            cleaned = f"_{cleaned}"
        
        # 限制文件名长度
        if len(cleaned) > 200:  # 留一些余量给扩展名
            name_part = Path(cleaned).stem
            ext_part = Path(cleaned).suffix
            cleaned = name_part[:200-len(ext_part)] + ext_part
        
        return cleaned
    
    def match_filename_with_rule(self, filename: str, rule: RegexRule, custom_title: str = None) -> Tuple[bool, str, str]:
        """
        使用规则匹配文件名
        
        Args:
            filename: 要匹配的文件名
            rule: 匹配规则
            custom_title: 自定义剧集名，如果提供则替换原剧集名
            
        Returns:
            (是否匹配成功, 新文件名, 匹配信息)
        """
        # 处理tc后缀：对于.tc.ass文件，需要保留.tc.ass而不是只取.ass
        if filename.endswith('.tc.ass'):
            extension = '.tc.ass'
        else:
            extension = Path(filename).suffix
        match_result = rule.match(filename)
        
        if match_result:
            try:
                # 如果有自定义剧集名，替换或添加series字段
                if custom_title:
                    if 'series' in match_result:
                        # 如果规则匹配到了series，替换它
                        match_result['series'] = custom_title
                    else:
                        # 如果规则没有匹配到series，添加自定义series
                        match_result['series'] = custom_title
                
                new_filename = rule.generate_output(match_result, extension)
                
                # 清理文件名
                new_filename = self.clean_filename(new_filename)
                
                return True, new_filename, str(match_result)
            except KeyError as e:
                return False, filename, f"格式错误: 缺少 {e}"
        else:
            return False, filename, "无匹配"
    
    def preview_rename(self, file_list: List[Path], rule: RegexRule, custom_title: str = None) -> List[Dict]:
        """
        预览重命名结果
        
        Args:
            file_list: 文件列表
            rule: 重命名规则
            custom_title: 自定义标题
            
        Returns:
            预览结果列表
        """
        results = []
        
        for file_path in file_list:
            filename = file_path.name
            success, new_filename, match_info = self.match_filename_with_rule(filename, rule, custom_title)
            
            results.append({
                'file_path': file_path,
                'original_name': filename,
                'new_name': new_filename,
                'success': success,
                'match_info': match_info
            })
        
        return results
    
    def execute_rename(self, file_list: List[Path], rule: RegexRule, custom_title: str = None, progress_callback=None) -> Tuple[int, int, List[Dict]]:
        """
        执行重命名操作
        
        Args:
            file_list: 文件列表
            rule: 重命名规则
            custom_title: 自定义剧集名
            progress_callback: 进度回调函数，接收(current, total, filename, status)参数
            
        Returns:
            (成功数量, 失败数量, 详细结果列表)
        """
        success_count = 0
        error_count = 0
        detailed_results = []
        
        for i, file_path in enumerate(file_list):
            try:
                filename = file_path.name
                
                # 更新进度
                if progress_callback:
                    progress_callback(i + 1, len(file_list), filename, "处理中...")
                
                success, new_filename, match_info = self.match_filename_with_rule(filename, rule, custom_title)
                
                if success:
                    # 检查目标文件是否已存在
                    new_path = file_path.parent / new_filename
                    if new_path.exists() and new_path != file_path:
                        error_count += 1
                        detailed_results.append({
                            'file_path': file_path,
                            'original_name': filename,
                            'new_name': new_filename,
                            'status': '跳过',
                            'reason': '目标文件已存在',
                            'match_info': match_info
                        })
                        if progress_callback:
                            progress_callback(i + 1, len(file_list), filename, "跳过 - 目标文件已存在")
                        continue
                    
                    # 执行重命名
                    success, error_reason = self.file_manager.rename_file(file_path, new_filename)
                    if success:
                        # 记录重命名操作（成功）
                        self.file_manager.log_rename(
                            str(file_path.parent), 
                            filename, 
                            new_filename, 
                            rule.name,
                            "成功",
                            "重命名成功"
                        )
                        success_count += 1
                        detailed_results.append({
                            'file_path': file_path,
                            'original_name': filename,
                            'new_name': new_filename,
                            'status': '成功',
                            'reason': '重命名成功',
                            'match_info': match_info
                        })
                        if progress_callback:
                            progress_callback(i + 1, len(file_list), filename, "成功")
                    else:
                        # 记录重命名操作（失败）
                        self.file_manager.log_rename(
                            str(file_path.parent), 
                            filename, 
                            new_filename, 
                            rule.name,
                            "失败",
                            error_reason
                        )
                        error_count += 1
                        detailed_results.append({
                            'file_path': file_path,
                            'original_name': filename,
                            'new_name': new_filename,
                            'status': '失败',
                            'reason': error_reason,
                            'match_info': match_info
                        })
                        if progress_callback:
                            progress_callback(i + 1, len(file_list), filename, f"失败 - {error_reason}")
                else:
                    # 记录重命名操作（规则匹配失败）
                    self.file_manager.log_rename(
                        str(file_path.parent), 
                        filename, 
                        filename, 
                        rule.name,
                        "失败",
                        "规则匹配失败"
                    )
                    error_count += 1
                    detailed_results.append({
                        'file_path': file_path,
                        'original_name': filename,
                        'new_name': filename,
                        'status': '失败',
                        'reason': '规则匹配失败',
                        'match_info': match_info
                    })
                    if progress_callback:
                        progress_callback(i + 1, len(file_list), filename, "失败 - 规则匹配失败")
                    
            except Exception as e:
                # 记录重命名操作（异常）
                self.file_manager.log_rename(
                    str(file_path.parent), 
                    filename, 
                    filename, 
                    rule.name,
                    "失败",
                    f"异常: {str(e)}"
                )
                error_count += 1
                detailed_results.append({
                    'file_path': file_path,
                    'original_name': filename,
                    'new_name': filename,
                    'status': '失败',
                    'reason': f'异常: {str(e)}',
                    'match_info': '无'
                })
                if progress_callback:
                    progress_callback(i + 1, len(file_list), filename, f"失败 - {str(e)}")
                print(f"重命名失败 {file_path}: {e}")
        
        return success_count, error_count, detailed_results
