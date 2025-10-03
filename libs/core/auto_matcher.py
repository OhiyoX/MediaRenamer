#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动规则匹配模块
负责分析文件名并自动选择最合适的规则
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from libs.core.rule import RegexRule


class RuleMatcher:
    """规则匹配器"""
    
    def __init__(self):
        # 规则优先级权重
        self.rule_weights = {
            '乱马1/2专用格式': 25,  # 乱马1/2专用格式（最高优先级）
            '乱马1/2特殊格式': 24,  # 乱马1/2特殊格式（最高优先级）
            'CASO特殊格式': 12,    # CASO特殊格式
            'CASO普通格式': 12,    # CASO普通格式
            'CASO完整格式': 16,  # CASO完整格式（最高优先级）
            'Evangelion特殊格式': 22,  # Evangelion特殊格式（最高优先级）
            'Evangelion范围格式': 21,  # Evangelion范围格式（最高优先级）
            '通用方括号格式': 18,  # 通用方括号格式（最高优先级）
            '通用点分隔格式': 19,  # 通用点分隔格式（最高优先级）
            '通用横线分隔格式': 20,  # 通用横线分隔格式（最高优先级）
            '通用下划线分隔格式': 21,  # 通用下划线分隔格式（最高优先级）
            'HYSUB_OAD格式': 12,    # HYSUB OAD专用格式
            'HYSUB普通格式': 12,    # HYSUB普通格式
            'YYDM-11FANS格式': 12,    # YYDM-11FANS专用格式
            '异域字幕组格式': 12,    # 异域字幕组专用格式
            'DMG字幕组格式': 12,    # DMG字幕组专用格式
            'Cowboy Bebop智能格式': 15,  # Cowboy Bebop专用智能格式
            '通用字幕组格式': 14,  # 通用字幕组格式
            '带季数剧集格式': 10,  # 最精确的剧集格式
            '日式剧集格式': 9,     # 日式剧集格式
            '日式OPED格式': 8,     # 日式OP/ED格式
            '日式OVA格式': 8,      # 日式OVA格式
            '日式菜单格式': 7,     # 日式菜单格式
            '标准剧集格式': 8,
            '电影格式': 7,
            '纪录片格式': 6,
            '综合通用格式': 1,  # 兜底规则（最低优先级）
            '简单数字格式-保留技术信息': 5,  # 保留技术信息的格式
            '简单数字格式': 3,  # 最通用的格式
        }
        
        # 文件名特征模式
        self.feature_patterns = {
            'season_episode': [
                r'S\d+E\d+',  # S01E01
                r'Season\s*\d+\s*Episode\s*\d+',  # Season 1 Episode 1
                r'第\d+季\s*第\d+集',  # 第1季 第1集
            ],
            'episode_only': [
                r'第\d+集',  # 第1集
                r'第\d+話',  # 第1話 (日式)
                r'Episode\s*\d+',  # Episode 1
                r'EP\d+',  # EP01
            ],
            'year': [
                r'\(\d{4}\)',  # (2023)
                r'\d{4}',  # 2023
            ],
            'quality': [
                r'\[.*?\]',  # [1080p], [BluRay]
                r'\(.*?\)',  # (1080p), (BluRay)
            ],
            'series_name': [
                r'\[.*?\]',  # [剧集名]
                r'^[^\[\]\(\)]+',  # 开头的剧集名
            ],
            'japanese_format': [
                r'第\d+話',  # 第1話
                r'\.OP\.',  # .OP.
                r'\.ED\.',  # .ED.
                r'\.OVA\.',  # .OVA.
                r'\.MENU\.',  # .MENU.
            ]
        }
    
    def analyze_filename(self, filename: str) -> Dict[str, bool]:
        """
        分析文件名特征
        
        Args:
            filename: 文件名
            
        Returns:
            特征字典
        """
        features = {}
        
        for feature_name, patterns in self.feature_patterns.items():
            features[feature_name] = any(
                re.search(pattern, filename, re.IGNORECASE) 
                for pattern in patterns
            )
        
        return features
    
    def calculate_rule_score(self, rule: RegexRule, filename: str) -> float:
        """
        计算规则匹配分数
        
        Args:
            rule: 规则对象
            filename: 文件名
            
        Returns:
            匹配分数 (0-100)
        """
        # 基础分数
        base_score = self.rule_weights.get(rule.name, 5)
        
        # 尝试匹配
        match_result = rule.match(filename)
        if not match_result:
            return 0.0
        
        # 匹配成功，计算详细分数
        score = base_score
        
        # 分析文件名特征
        features = self.analyze_filename(filename)
        
        # 根据规则类型调整分数
        if '带季数剧集格式' in rule.name:
            if features['season_episode']:
                score += 20
            elif features['episode_only']:
                score += 10
        elif '日式剧集格式' in rule.name:
            if features['japanese_format']:
                score += 25
            if features['episode_only']:
                score += 15
        elif '日式OPED格式' in rule.name:
            if features['japanese_format']:
                score += 20
        elif '日式OVA格式' in rule.name:
            if features['japanese_format']:
                score += 20
        elif '日式菜单格式' in rule.name:
            if features['japanese_format']:
                score += 15
        elif '标准剧集格式' in rule.name:
            if features['episode_only']:
                score += 15
            if features['series_name']:
                score += 10
        elif '电影格式' in rule.name:
            if features['year']:
                score += 15
            if features['quality']:
                score += 10
        elif '纪录片格式' in rule.name:
            if features['episode_only']:
                score += 15
        elif '简单数字格式' in rule.name:
            # 简单格式作为兜底，分数较低
            score += 5
        
        # 检查匹配的组数量
        matched_groups = sum(1 for v in match_result.values() if v and v.strip())
        total_groups = len(rule.groups)
        if total_groups > 0:
            group_ratio = matched_groups / total_groups
            score += group_ratio * 10
        
        # 确保分数在合理范围内
        return min(score, 100.0)
    
    def find_best_rule(self, filename: str, rules: List[RegexRule]) -> Tuple[Optional[RegexRule], float, Dict]:
        """
        找到最匹配的规则
        
        Args:
            filename: 文件名
            rules: 规则列表
            
        Returns:
            (最佳规则, 分数, 匹配信息)
        """
        if not rules:
            return None, 0.0, {}
        
        best_rule = None
        best_score = 0.0
        best_match_info = {}
        
        for rule in rules:
            score = self.calculate_rule_score(rule, filename)
            if score > best_score:
                best_score = score
                best_rule = rule
                best_match_info = rule.match(filename) or {}
        
        return best_rule, best_score, best_match_info
    
    def auto_match_files(self, file_list: List[Path], rules: List[RegexRule]) -> Dict[str, Dict]:
        """
        自动匹配文件列表
        
        Args:
            file_list: 文件列表
            rules: 规则列表
            
        Returns:
            匹配结果字典
        """
        results = {}
        
        for file_path in file_list:
            filename = file_path.name
            best_rule, score, match_info = self.find_best_rule(filename, rules)
            
            results[filename] = {
                'rule': best_rule,
                'score': score,
                'match_info': match_info,
                'file_path': file_path
            }
        
        return results
    
    def get_rule_suggestions(self, filename: str, rules: List[RegexRule], top_n: int = 3) -> List[Tuple[RegexRule, float]]:
        """
        获取规则建议（按分数排序）
        
        Args:
            filename: 文件名
            rules: 规则列表
            top_n: 返回前N个建议
            
        Returns:
            建议列表 [(规则, 分数), ...]
        """
        suggestions = []
        
        for rule in rules:
            score = self.calculate_rule_score(rule, filename)
            if score > 0:
                suggestions.append((rule, score))
        
        # 按分数降序排序
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:top_n]
