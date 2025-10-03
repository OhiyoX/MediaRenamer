#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块
负责文件扫描、备份等文件操作
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from libs.config import SUPPORTED_MEDIA_EXTENSIONS, BACKUP_DIR_NAME, RENAME_LOG_NAME


class FileManager:
    """文件管理器"""
    
    @staticmethod
    def scan_media_files(directory: str) -> List[Path]:
        """
        扫描目录中的媒体文件（视频+字幕）
        
        Args:
            directory: 要扫描的目录路径
            
        Returns:
            媒体文件路径列表
        """
        if not directory or not os.path.exists(directory):
            return []
        
        media_files = []
        for file_path in Path(directory).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS:
                media_files.append(file_path)
        
        return media_files
    
    @staticmethod
    def scan_video_files(directory: str) -> List[Path]:
        """
        扫描目录中的视频文件
        
        Args:
            directory: 要扫描的目录路径
            
        Returns:
            视频文件路径列表
        """
        if not directory or not os.path.exists(directory):
            return []
        
        video_files = []
        for file_path in Path(directory).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS:
                video_files.append(file_path)
        
        return video_files
    
    @staticmethod
    def create_backup(directory: str, file_list: List[Path]) -> Tuple[int, str]:
        """
        创建文件备份
        
        Args:
            directory: 目录路径
            file_list: 要备份的文件列表
            
        Returns:
            (备份文件数量, 备份目录路径)
        """
        backup_dir = Path(directory) / BACKUP_DIR_NAME
        backup_dir.mkdir(exist_ok=True)
        
        backup_count = 0
        for file_path in file_list:
            try:
                backup_path = backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                backup_count += 1
            except Exception as e:
                print(f"备份失败 {file_path}: {e}")
        
        return backup_count, str(backup_dir)
    
    @staticmethod
    def rename_file(file_path: Path, new_name: str) -> Tuple[bool, str]:
        """
        重命名文件
        
        Args:
            file_path: 原文件路径
            new_name: 新文件名
            
        Returns:
            (是否成功, 错误原因)
        """
        try:
            new_path = file_path.parent / new_name
            
            # 检查文件名是否有效
            if not new_name or new_name.strip() == "":
                return False, "文件名为空"
            
            # 检查文件名长度（Windows限制255字符）
            if len(new_name) > 255:
                return False, f"文件名过长 ({len(new_name)} > 255)"
            
            # 检查非法字符
            illegal_chars = '<>:"/\\|?*'
            for char in illegal_chars:
                if char in new_name:
                    return False, f"文件名包含非法字符: {char}"
            
            # 检查Windows保留名称
            reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
            name_without_ext = Path(new_name).stem.upper()
            if name_without_ext in reserved_names:
                return False, f"文件名使用了Windows保留名称: {name_without_ext}"
            
            # 检查是否已存在
            if new_path.exists() and new_path != file_path:
                return False, "目标文件已存在"
            
            # 检查文件是否被占用
            try:
                with open(file_path, 'r+b') as f:
                    pass
            except PermissionError:
                return False, "文件被占用或无权限访问"
            except Exception as e:
                return False, f"文件访问错误: {e}"
            
            # 执行重命名
            file_path.rename(new_path)
            return True, "成功"
            
        except PermissionError as e:
            return False, f"权限错误: {e}"
        except OSError as e:
            return False, f"系统错误: {e}"
        except Exception as e:
            return False, f"未知错误: {e}"
    
    @staticmethod
    def log_rename(directory: str, old_name: str, new_name: str, rule_name: str = None, status: str = "成功", reason: str = None) -> bool:
        """
        记录重命名操作
        
        Args:
            directory: 文件所在目录
            old_name: 原文件名
            new_name: 新文件名
            rule_name: 使用的规则名称
            status: 操作状态（成功/失败/跳过）
            reason: 操作原因或错误信息
            
        Returns:
            是否记录成功
        """
        try:
            log_file = Path(directory) / RENAME_LOG_NAME
            
            # 读取现有记录
            rename_log = []
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    rename_log = json.load(f)
            
            # 添加新记录
            rename_entry = {
                'timestamp': datetime.now().isoformat(),
                'old_name': old_name,
                'new_name': new_name,
                'rule_name': rule_name,
                'directory': directory,
                'status': status,
                'reason': reason or "无"
            }
            rename_log.append(rename_entry)
            
            # 保存记录
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(rename_log, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"记录重命名失败: {e}")
            return False
    
    @staticmethod
    def restore_single_from_log(directory: str, log_entry: Dict) -> bool:
        """
        从记录恢复文件名
        
        Args:
            directory: 文件所在目录
            log_entry: 重命名记录条目
            
        Returns:
            是否恢复成功
        """
        try:
            old_name = log_entry.get('old_name')
            new_name = log_entry.get('new_name')
            
            if not old_name or not new_name:
                return False
            
            # 检查新文件是否存在
            new_path = Path(directory) / new_name
            if not new_path.exists():
                return False
            
            # 检查原文件是否已存在
            old_path = Path(directory) / old_name
            if old_path.exists() and old_path != new_path:
                return False
            
            # 执行恢复
            new_path.rename(old_path)
            return True
            
        except Exception as e:
            print(f"恢复文件名失败: {e}")
            return False
    
    @staticmethod
    def restore_all_from_log(directory: str) -> Tuple[int, int, List[Dict]]:
        """
        从记录恢复所有文件名
        
        Args:
            directory: 文件所在目录
            
        Returns:
            (成功数量, 失败数量, 详细结果)
        """
        try:
            rename_log = FileManager.load_rename_log(directory)
            if not rename_log:
                return 0, 0, []
            
            success_count = 0
            error_count = 0
            detailed_results = []
            
            # 只处理成功的重命名记录
            successful_entries = [entry for entry in rename_log if entry.get('status') == '成功']
            
            for entry in successful_entries:
                old_name = entry.get('old_name')
                new_name = entry.get('new_name')
                
                if FileManager.restore_single_from_log(directory, entry):
                    success_count += 1
                    detailed_results.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': '恢复成功',
                        'reason': '文件名已恢复'
                    })
                else:
                    error_count += 1
                    detailed_results.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': '恢复失败',
                        'reason': '文件不存在或原文件已存在'
                    })
            
            return success_count, error_count, detailed_results
            
        except Exception as e:
            print(f"批量恢复失败: {e}")
            return 0, 1, [{'status': '恢复失败', 'reason': f'异常: {str(e)}'}]
    
    @staticmethod
    def load_rename_log(directory: str) -> List[Dict]:
        """
        加载重命名记录
        
        Args:
            directory: 目录路径
            
        Returns:
            重命名记录列表
        """
        try:
            log_file = Path(directory) / RENAME_LOG_NAME
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载重命名记录失败: {e}")
            return []
    
    @staticmethod
    def restore_from_log(directory: str, log_file_path: str = None) -> Tuple[int, str]:
        """
        从重命名记录恢复文件名
        
        Args:
            directory: 要恢复的目录
            log_file_path: 记录文件路径，如果为None则使用目录下的默认记录文件
            
        Returns:
            (恢复的文件数量, 记录文件路径)
        """
        try:
            if log_file_path:
                log_file = Path(log_file_path)
            else:
                log_file = Path(directory) / RENAME_LOG_NAME
            
            if not log_file.exists():
                return 0, str(log_file)
            
            # 读取记录
            with open(log_file, 'r', encoding='utf-8') as f:
                rename_log = json.load(f)
            
            # 按时间倒序排列（最新的在前）
            rename_log.sort(key=lambda x: x['timestamp'], reverse=True)
            
            restored_count = 0
            directory_path = Path(directory)
            
            # 恢复文件
            for entry in rename_log:
                if entry['directory'] != directory:
                    continue
                
                old_path = directory_path / entry['old_name']
                new_path = directory_path / entry['new_name']
                
                # 检查新文件是否存在，旧文件不存在
                if new_path.exists() and not old_path.exists():
                    try:
                        new_path.rename(old_path)
                        restored_count += 1
                    except Exception as e:
                        print(f"恢复文件失败 {new_path} -> {old_path}: {e}")
            
            return restored_count, str(log_file)
            
        except Exception as e:
            print(f"恢复文件失败: {e}")
            return 0, str(log_file) if 'log_file' in locals() else ""
    
    @staticmethod
    def clear_rename_log(directory: str) -> bool:
        """
        清除重命名记录
        
        Args:
            directory: 目录路径
            
        Returns:
            是否清除成功
        """
        try:
            log_file = Path(directory) / RENAME_LOG_NAME
            if log_file.exists():
                log_file.unlink()
            return True
        except Exception as e:
            print(f"清除重命名记录失败: {e}")
            return False
