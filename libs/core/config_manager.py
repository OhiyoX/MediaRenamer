#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责管理应用程序的配置选项
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from libs.config import ENABLE_PARENT_FOLDER_RECOGNITION, PARENT_FOLDER_RECOGNITION_CONFIG


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 返回默认配置
        return {
            'parent_folder_recognition': {
                'enabled': ENABLE_PARENT_FOLDER_RECOGNITION,
                'enable_series_recognition': PARENT_FOLDER_RECOGNITION_CONFIG.get('enable_series_recognition', True),
                'enable_season_recognition': PARENT_FOLDER_RECOGNITION_CONFIG.get('enable_season_recognition', True),
                'enable_custom_season': PARENT_FOLDER_RECOGNITION_CONFIG.get('enable_custom_season', True),
                'default_season': PARENT_FOLDER_RECOGNITION_CONFIG.get('default_season', '01'),
                'season_patterns': PARENT_FOLDER_RECOGNITION_CONFIG.get('season_patterns', [])
            }
        }
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def is_parent_folder_recognition_enabled(self) -> bool:
        """检查是否启用父文件夹识别"""
        return self.get('parent_folder_recognition.enabled', ENABLE_PARENT_FOLDER_RECOGNITION)
    
    def is_series_recognition_enabled(self) -> bool:
        """检查是否启用剧名识别"""
        return self.get('parent_folder_recognition.enable_series_recognition', True)
    
    def is_season_recognition_enabled(self) -> bool:
        """检查是否启用季数识别"""
        return self.get('parent_folder_recognition.enable_season_recognition', True)
    
    def is_custom_season_enabled(self) -> bool:
        """检查是否启用自定义季数"""
        return self.get('parent_folder_recognition.enable_custom_season', True)
    
    def get_default_season(self) -> str:
        """获取默认季数"""
        return self.get('parent_folder_recognition.default_season', '01')
    
    def get_season_patterns(self) -> list:
        """获取季数识别模式"""
        return self.get('parent_folder_recognition.season_patterns', [
            r'S(\d+)',  # S01, S02
            r'Season\s*(\d+)',  # Season 1, Season 2
            r'第(\d+)季',  # 第1季, 第2季
        ])
    
    def set_parent_folder_recognition(self, enabled: bool):
        """设置父文件夹识别开关"""
        self.set('parent_folder_recognition.enabled', enabled)
    
    def set_series_recognition(self, enabled: bool):
        """设置剧名识别开关"""
        self.set('parent_folder_recognition.enable_series_recognition', enabled)
    
    def set_season_recognition(self, enabled: bool):
        """设置季数识别开关"""
        self.set('parent_folder_recognition.enable_season_recognition', enabled)
    
    def set_custom_season(self, enabled: bool):
        """设置自定义季数开关"""
        self.set('parent_folder_recognition.enable_custom_season', enabled)
    
    def set_default_season(self, season: str):
        """设置默认季数"""
        self.set('parent_folder_recognition.default_season', season)
