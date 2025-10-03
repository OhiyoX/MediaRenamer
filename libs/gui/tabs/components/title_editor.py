#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧集名编辑组件（集成文件夹识别功能）
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional, Dict
from pathlib import Path
import re

from libs.core.rule import RegexRule
from libs.core.config_manager import ConfigManager


class TitleEditor:
    """剧集名编辑组件（集成文件夹识别功能）"""
    
    def __init__(self, parent_frame: ttk.Frame, 
                 on_title_change: Callable[[str], None],
                 on_apply_custom_title: Callable[[str], None],
                 on_clear_custom_title: Callable[[], None],
                 on_apply_custom_season: Callable[[str], None] = None,
                 config_manager: ConfigManager = None):
        self.parent_frame = parent_frame
        self.on_title_change = on_title_change
        self.on_apply_custom_title = on_apply_custom_title
        self.on_clear_custom_title = on_clear_custom_title
        self.on_apply_custom_season = on_apply_custom_season
        self.config_manager = config_manager or ConfigManager()
        
        # 文件夹识别相关
        self.current_folder_info = {}
        self.current_file_paths = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        title_frame = ttk.LabelFrame(self.parent_frame, text="剧集名编辑")
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 剧集名编辑说明
        ttk.Label(title_frame, text="可以自定义重命名时的剧集名部分，留空则使用原文件名中的剧集名").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(title_frame, text="注意：即使规则没有匹配到series字段，也可以设置自定义剧集名").pack(anchor=tk.W, padx=5, pady=2)
        
        # 统一的设置区域（文件夹识别 + 自定义设置）
        settings_frame = ttk.LabelFrame(title_frame, text="剧集设置")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行：文件夹识别信息（三列布局）
        folder_row = ttk.Frame(settings_frame)
        folder_row.pack(fill=tk.X, padx=5, pady=5)
        
        # 列1：识别到的剧名
        folder_series_col = ttk.Frame(folder_row)
        folder_series_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(folder_series_col, text="文件夹识别剧名:").pack(anchor=tk.W)
        self.folder_series_var = tk.StringVar()
        self.folder_series_entry = ttk.Entry(folder_series_col, textvariable=self.folder_series_var, state="readonly")
        self.folder_series_entry.pack(fill=tk.X, pady=(0, 5))
        
        # 列2：识别到的季数
        folder_season_col = ttk.Frame(folder_row)
        folder_season_col.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 5))
        
        ttk.Label(folder_season_col, text="文件夹识别季数:").pack(anchor=tk.W)
        self.folder_season_var = tk.StringVar()
        self.folder_season_entry = ttk.Entry(folder_season_col, textvariable=self.folder_season_var, state="readonly", width=8)
        self.folder_season_entry.pack(pady=(0, 5))
        
        # 列3：文件夹识别按钮
        folder_btn_col = ttk.Frame(folder_row)
        folder_btn_col.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        
        ttk.Label(folder_btn_col, text="文件夹操作:").pack(anchor=tk.W)
        folder_btn_frame = ttk.Frame(folder_btn_col)
        folder_btn_frame.pack(pady=(0, 5))
        
        self.apply_folder_series_button = ttk.Button(
            folder_btn_frame, 
            text="应用剧名", 
            command=self._apply_folder_series,
            state="disabled"
        )
        self.apply_folder_series_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.apply_folder_season_button = ttk.Button(
            folder_btn_frame, 
            text="应用季数", 
            command=self._apply_folder_season,
            state="disabled"
        )
        self.apply_folder_season_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.apply_folder_all_button = ttk.Button(
            folder_btn_frame, 
            text="应用全部", 
            command=self._apply_folder_all,
            state="disabled"
        )
        self.apply_folder_all_button.pack(side=tk.LEFT, padx=(0, 2))
        
        ttk.Button(folder_btn_frame, text="清除", command=self._clear_folder_info).pack(side=tk.LEFT)
        
        # 第二行：自定义设置（三列布局）
        custom_row = ttk.Frame(settings_frame)
        custom_row.pack(fill=tk.X, padx=5, pady=5)
        
        # 列1：自定义剧集名
        custom_title_col = ttk.Frame(custom_row)
        custom_title_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(custom_title_col, text="自定义剧集名:").pack(anchor=tk.W)
        self.custom_title_var = tk.StringVar()
        title_entry = ttk.Entry(custom_title_col, textvariable=self.custom_title_var)
        title_entry.pack(fill=tk.X, pady=(0, 5))
        title_entry.bind('<KeyRelease>', self._on_title_change)
        
        # 列2：自定义季数
        custom_season_col = ttk.Frame(custom_row)
        custom_season_col.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 5))
        
        ttk.Label(custom_season_col, text="自定义季数:").pack(anchor=tk.W)
        self.custom_season_var = tk.StringVar()
        season_entry = ttk.Entry(custom_season_col, textvariable=self.custom_season_var, width=8)
        season_entry.pack(pady=(0, 5))
        season_entry.bind('<KeyRelease>', self._on_season_change)
        
        # 列3：自定义设置按钮
        custom_btn_col = ttk.Frame(custom_row)
        custom_btn_col.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        
        ttk.Label(custom_btn_col, text="自定义操作:").pack(anchor=tk.W)
        custom_btn_frame = ttk.Frame(custom_btn_col)
        custom_btn_frame.pack(pady=(0, 5))
        
        ttk.Button(custom_btn_frame, text="应用剧集名", command=self._apply_custom_title).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(custom_btn_frame, text="应用季数", command=self._apply_custom_season).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(custom_btn_frame, text="清除", command=self._clear_custom_settings).pack(side=tk.LEFT)
        
        # 状态显示（跨三列）
        self.folder_status_var = tk.StringVar()
        self.folder_status_label = ttk.Label(settings_frame, textvariable=self.folder_status_var, foreground="gray")
        self.folder_status_label.pack(anchor=tk.W, padx=5, pady=2)
    
    def _on_title_change(self, event=None):
        """剧集名变化事件"""
        custom_title = self.custom_title_var.get().strip()
        self.on_title_change(custom_title)
    
    def _on_season_change(self, event=None):
        """季数变化事件"""
        custom_season = self.custom_season_var.get().strip()
        # 可以在这里添加季数变化的处理逻辑
        pass
    
    def _apply_custom_title(self):
        """应用自定义剧集名到所有文件"""
        custom_title = self.custom_title_var.get().strip()
        if not custom_title:
            messagebox.showwarning("警告", "请输入自定义剧集名")
            return
        
        self.on_apply_custom_title(custom_title)
    
    def _apply_custom_season(self):
        """应用自定义季数到所有文件"""
        custom_season = self.custom_season_var.get().strip()
        if not custom_season:
            messagebox.showwarning("警告", "请输入自定义季数")
            return
        
        # 确保季数格式正确（补零）
        try:
            season_num = int(custom_season)
            formatted_season = f"{season_num:02d}"
        except ValueError:
            # 如果不是数字，直接使用输入的值
            formatted_season = custom_season
        
        if self.on_apply_custom_season:
            self.on_apply_custom_season(formatted_season)
    
    def _clear_custom_settings(self):
        """清除自定义设置"""
        self.custom_title_var.set("")
        self.custom_season_var.set("")
        self.on_clear_custom_title()
    
    def _clear_custom_title(self):
        """清除自定义剧集名"""
        self.custom_title_var.set("")
        self.on_clear_custom_title()
    
    def get_custom_title(self) -> str:
        """获取自定义剧集名"""
        return self.custom_title_var.get().strip()
    
    def set_custom_title(self, title: str):
        """设置自定义剧集名"""
        self.custom_title_var.set(title)
    
    def get_custom_season(self) -> str:
        """获取自定义季数"""
        return self.custom_season_var.get().strip()
    
    def set_custom_season(self, season: str):
        """设置自定义季数"""
        self.custom_season_var.set(season)
    
    # 文件夹识别相关方法
    def analyze_files(self, file_paths: List[Path], applied_rule: Optional[RegexRule] = None):
        """
        分析文件路径，识别文件夹信息
        
        Args:
            file_paths: 文件路径列表
            applied_rule: 应用的规则
        """
        if not file_paths:
            self._clear_folder_info()
            return
        
        self.current_file_paths = file_paths
        
        # 检查是否启用文件夹识别
        if not self.config_manager.is_parent_folder_recognition_enabled():
            self.folder_status_var.set("文件夹识别功能已禁用")
            self._update_folder_button_states(False, False)
            return
        
        # 使用第一个文件路径进行分析
        first_file_path = str(file_paths[0])
        
        if applied_rule:
            # 使用规则进行识别
            folder_info = applied_rule.get_folder_recognition_info(first_file_path)
        else:
            # 直接分析路径
            folder_info = self._analyze_path_directly(first_file_path)
        
        self.current_folder_info = folder_info
        
        # 更新显示
        self._update_folder_display(folder_info)
    
    def _analyze_path_directly(self, file_path: str) -> Dict[str, str]:
        """
        直接分析文件路径，不依赖规则
        
        Args:
            file_path: 文件路径
            
        Returns:
            识别到的文件夹信息
        """
        folder_info = {}
        
        if not file_path:
            return folder_info
            
        path_parts = Path(file_path).parts
        
        # 使用配置中的季数识别模式
        season_patterns = self.config_manager.get_season_patterns()
        
        # 查找季数信息
        for part in reversed(path_parts):  # 从后往前查找
            for pattern in season_patterns:
                match = re.search(pattern, part, re.IGNORECASE)
                if match:
                    folder_info['season'] = match.group(1).zfill(2)  # 补零，如01, 02
                    break
            if 'season' in folder_info:
                break
        
        # 查找剧名
        if 'season' in folder_info:
            for i, part in enumerate(path_parts):
                # 查找包含季数信息的文件夹
                for pattern in season_patterns:
                    if re.search(pattern, part, re.IGNORECASE):
                        # 找到季数文件夹，其父文件夹通常是剧名
                        if i > 0:
                            folder_info['series'] = path_parts[i-1]
                        break
                if 'series' in folder_info:
                    break
        
        return folder_info
    
    def _update_folder_display(self, folder_info: Dict[str, str]):
        """更新文件夹识别显示信息"""
        if folder_info:
            # 有识别信息
            series = folder_info.get('series', '')
            season = folder_info.get('season', '')
            
            self.folder_series_var.set(series)
            self.folder_season_var.set(f"S{season}" if season else "")
            
            # 根据识别到的信息启用相应按钮
            has_series = bool(series)
            has_season = bool(season)
            self._update_folder_button_states(has_series, has_season)
            
            # 更新状态显示
            if series and season:
                self.folder_status_var.set(f"识别到: {series} - S{season}")
            elif series:
                self.folder_status_var.set(f"识别到剧名: {series}")
            elif season:
                self.folder_status_var.set(f"识别到季数: S{season}")
            else:
                self.folder_status_var.set("未识别到有效信息")
        else:
            # 无识别信息
            self.folder_series_var.set("")
            self.folder_season_var.set("")
            self.folder_status_var.set("未识别到文件夹信息")
            self._update_folder_button_states(False, False)
    
    def _update_folder_button_states(self, has_series: bool, has_season: bool):
        """更新文件夹识别按钮状态"""
        self.apply_folder_series_button.config(state="normal" if has_series else "disabled")
        self.apply_folder_season_button.config(state="normal" if has_season else "disabled")
        self.apply_folder_all_button.config(state="normal" if (has_series or has_season) else "disabled")
    
    def _apply_folder_series(self):
        """应用文件夹识别的剧名"""
        if not self.current_folder_info or not self.current_folder_info.get('series'):
            messagebox.showwarning("警告", "没有可应用的剧名信息")
            return
        
        series_name = self.current_folder_info['series']
        
        # 设置到自定义剧集名输入框
        self.custom_title_var.set(series_name)
        # 调用应用回调
        self.on_apply_custom_title(series_name)
        
        self.folder_status_var.set(f"剧名 '{series_name}' 已应用")
    
    def _apply_folder_season(self):
        """应用文件夹识别的季数"""
        if not self.current_folder_info or not self.current_folder_info.get('season'):
            messagebox.showwarning("警告", "没有可应用的季数信息")
            return
        
        season = self.current_folder_info['season']
        
        # 设置到自定义季数输入框
        self.custom_season_var.set(season)
        # 调用应用回调
        if self.on_apply_custom_season:
            self.on_apply_custom_season(season)
        
        self.folder_status_var.set(f"季数 'S{season}' 已应用")
    
    def _apply_folder_all(self):
        """应用所有文件夹识别信息"""
        if not self.current_folder_info:
            messagebox.showwarning("警告", "没有可应用的文件夹识别信息")
            return
        
        series = self.current_folder_info.get('series', '')
        season = self.current_folder_info.get('season', '')
        
        # 应用剧名（如果有）
        if series:
            self.custom_title_var.set(series)
            self.on_apply_custom_title(series)
        
        # 应用季数（如果有）
        if season:
            self.custom_season_var.set(season)
            if self.on_apply_custom_season:
                self.on_apply_custom_season(season)
        
        self.folder_status_var.set("文件夹识别信息已应用")
    
    def _clear_folder_info(self):
        """清除文件夹识别信息"""
        self.current_folder_info = {}
        self.current_file_paths = []
        self.folder_series_var.set("")
        self.folder_season_var.set("")
        self.folder_status_var.set("")
        self._update_folder_button_states(False, False)
    
    def get_folder_info(self) -> Dict[str, str]:
        """获取当前文件夹识别信息"""
        return self.current_folder_info.copy()
    
    def is_folder_info_available(self) -> bool:
        """检查是否有可用的文件夹识别信息"""
        return bool(self.current_folder_info)
