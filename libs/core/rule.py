#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理模块
包含正则表达式规则类和规则文件管理器
"""

import re
import json
import glob
from pathlib import Path
from typing import List, Dict, Optional

from libs.config import DEFAULT_RULES_DIR, DEFAULT_RULES, ENABLE_PARENT_FOLDER_RECOGNITION, PARENT_FOLDER_RECOGNITION_CONFIG
from libs.core.config_manager import ConfigManager


class RegexRule:
    """正则表达式规则类"""
    
    def __init__(self, name: str, pattern: str, groups: Dict[str, int], output_format: str, special_handling: Dict = None, config_manager: ConfigManager = None):
        """
        初始化正则表达式规则
        
        Args:
            name: 规则名称
            pattern: 正则表达式模式
            groups: 捕获组映射，键为变量名，值为组索引
            output_format: 输出文件名格式模板
            special_handling: 特殊处理配置
        """
        self.name = name
        self.pattern = pattern
        self.groups = groups
        self.output_format = output_format
        self.special_handling = special_handling or {}
        self.config_manager = config_manager or ConfigManager()
        self.compiled_pattern = re.compile(pattern)
    
    def match(self, filename: str) -> Optional[Dict[str, str]]:
        """匹配文件名并返回提取的信息"""
        match = self.compiled_pattern.search(filename)
        if not match:
            return None
        
        result = {}
        for group_name, group_index in self.groups.items():
            if group_index <= len(match.groups()):
                result[group_name] = match.group(group_index)
            else:
                result[group_name] = ""
        
        return result
    
    def get_folder_recognition_info(self, file_path: str) -> Dict[str, str]:
        """
        获取文件夹识别信息（仅用于预览显示，不应用到输出）
        
        Args:
            file_path: 文件完整路径
            
        Returns:
            包含识别到的剧名和季数的字典
        """
        folder_info = {}
        
        if not file_path:
            return folder_info
        
        # 检查是否启用父文件夹识别
        if not self.config_manager.is_parent_folder_recognition_enabled():
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
    
    def extract_parent_info(self, file_path: str) -> Dict[str, str]:
        """
        从父文件夹路径中提取剧名和季数信息
        
        Args:
            file_path: 文件完整路径
            
        Returns:
            包含剧名和季数的字典
        """
        parent_info = {}
        
        # 检查是否启用父文件夹识别
        if not self.config_manager.is_parent_folder_recognition_enabled():
            return parent_info
            
        path_parts = Path(file_path).parts
        
        # 使用配置中的季数识别模式
        season_patterns = self.config_manager.get_season_patterns()
        
        # 查找季数信息（如果启用）
        if self.config_manager.is_season_recognition_enabled():
            for part in reversed(path_parts):  # 从后往前查找
                for pattern in season_patterns:
                    match = re.search(pattern, part, re.IGNORECASE)
                    if match:
                        parent_info['season'] = match.group(1).zfill(2)  # 补零，如01, 02
                        break
                if 'season' in parent_info:
                    break
        
        # 查找剧名（如果启用）
        if self.config_manager.is_series_recognition_enabled():
            if 'season' in parent_info:
                for i, part in enumerate(path_parts):
                    # 查找包含季数信息的文件夹
                    for pattern in season_patterns:
                        if re.search(pattern, part, re.IGNORECASE):
                            # 找到季数文件夹，其父文件夹通常是剧名
                            if i > 0:
                                parent_info['series_name'] = path_parts[i-1]
                            break
                    if 'series_name' in parent_info:
                        break
        
        return parent_info

    def generate_output(self, extracted_info: Dict[str, str], extension: str = "", file_path: str = "", custom_season: str = None, apply_folder_info: bool = True) -> str:
        """根据提取的信息生成输出文件名"""
        try:
            # 从父文件夹路径提取信息（仅在启用时）
            parent_info = {}
            if file_path and apply_folder_info:
                parent_info = self.extract_parent_info(file_path)
            
            # 处理空标题的情况
            processed_info = {}
            for key, value in extracted_info.items():
                if value is None or value.strip() == "":
                    processed_info[key] = ""
                else:
                    processed_info[key] = value
            
            # 特殊处理：大写字段
            if self.special_handling and 'uppercase_fields' in self.special_handling:
                for field in self.special_handling['uppercase_fields']:
                    if field in processed_info:
                        processed_info[field] = processed_info[field].upper()

            # 特殊处理：字段回退（将缺失字段从其他字段或默认值填充）
            if self.special_handling and 'fallback_fields' in self.special_handling:
                fallback_config = self.special_handling['fallback_fields']
                for target_field, sources in fallback_config.items():
                    current_value = processed_info.get(target_field, '')
                    if current_value is None or str(current_value).strip() == "":
                        # 允许列表或标量
                        if isinstance(sources, list):
                            assigned = False
                            for src in sources:
                                # 如果是其他字段名
                                if src in processed_info and str(processed_info[src]).strip() != "":
                                    processed_info[target_field] = processed_info[src]
                                    assigned = True
                                    break
                                # 否则将其视为字面默认值
                                elif isinstance(src, str) and src not in processed_info:
                                    processed_info[target_field] = src
                                    assigned = True
                                    break
                            if not assigned:
                                processed_info[target_field] = ""
                        else:
                            # 标量默认值
                            processed_info[target_field] = sources if isinstance(sources, str) else ""

            # 使用父文件夹信息覆盖或补充提取的信息
            if parent_info:
                # 如果有父文件夹的剧名信息，优先使用
                if 'series_name' in parent_info and parent_info['series_name']:
                    processed_info['series'] = parent_info['series_name']
                
                # 如果有父文件夹的季数信息，用于生成正确的季数格式
                if 'season' in parent_info and parent_info['season']:
                    processed_info['parent_season'] = parent_info['season']

            # 特殊处理：空episode字段
            if 'episode' in processed_info and not processed_info['episode']:
                processed_info['episode'] = '01'  # 默认为01

            # 特殊处理：集数信息处理
            if 'episode' in processed_info and self.special_handling:
                episode_num = processed_info['episode']
                
                # 处理特殊集数标识（OVA, SP, END等）
                special_episodes = ['OVA', 'SP', 'SPECIAL', 'END']
                
                # 检查是否是特殊集数
                episode_upper = episode_num.upper()
                is_special = any(special in episode_upper for special in special_episodes)
                
                if is_special:
                    # 所有特殊集数都保持原样，不进行数字提取
                    processed_info['episode'] = episode_num
                
                # 检查是否是年份而不是集数（仅对纯数字进行年份检查）
                if episode_num.isdigit():
                    episode_int = int(episode_num)
                    
                    # 检查是否是年份
                    if 'year_pattern' in self.special_handling:
                        import re
                        year_pattern = self.special_handling['year_pattern']
                        if re.search(year_pattern, episode_num):
                            # 这是年份，不是集数
                            processed_info['episode'] = "01"  # 电影通常作为第1集
                            if not processed_info.get('title'):
                                processed_info['title'] = f"({episode_num})"
                    
                    # 检查集数是否过大
                    elif 'max_episode' in self.special_handling:
                        max_ep = self.special_handling['max_episode']
                        if episode_int > max_ep:
                            # 可能是年份，处理为电影
                            processed_info['episode'] = "01"
                            if not processed_info.get('title'):
                                processed_info['title'] = f"({episode_num})"
            
            # 生成基础格式
            base_output = self.output_format.format(**processed_info)
            
            # 处理季数信息（优先级：自定义季数 > 父文件夹季数 > 默认季数）
            import re
            episode_value = processed_info.get('episode', '')
            
            # 确定使用的季数
            season_num = None
            
            # 1. 优先使用自定义季数
            if custom_season:
                season_num = custom_season.zfill(2)  # 补零
            # 2. 其次使用父文件夹识别的季数
            elif 'parent_season' in processed_info:
                season_num = processed_info['parent_season']
            # 3. 最后使用默认季数
            elif self.config_manager.is_custom_season_enabled():
                season_num = self.config_manager.get_default_season()
            
            # 如果确定了季数，替换输出中的季数部分
            if season_num:
                base_output = re.sub(r'S\d+', f'S{season_num}', base_output)
            
            # 特殊处理：特殊集数的显示格式
            if 'episode' in processed_info:
                episode_value = processed_info['episode']
                episode_upper = episode_value.upper()
                
                if episode_upper in ['OVA', 'SP', 'SPECIAL']:
                    # OVA/SP显示为S{season} {episode_value}格式
                    # 例如：S02EOVA -> S02 OVA
                    base_output = re.sub(r'S(\d+)E[^-\s]*', rf'S\1 {episode_value}', base_output)
                elif 'END' in episode_upper:
                    # END保持原样，如S01E13 END
                    pass  # 不需要特殊处理，保持原样
            
            # 清理多余的 " - " 和 "None"
            base_output = base_output.replace(" - None", "")
            base_output = base_output.replace(" -  - ", " - ")
            base_output = base_output.replace(" -  ", "")
            # 清理末尾的 " - "
            if base_output.endswith(" - "):
                base_output = base_output[:-3]
            
            # 特殊处理：如果技术信息前面没有空格，添加空格
            import re
            base_output = re.sub(r'(S\d+E\d+)(\[)', r'\1 \2', base_output)
            
            # 特殊处理：CASO完整格式需要添加后缀
            if self.name == 'CASO完整格式' and 'suffix' in processed_info:
                suffix = processed_info['suffix']
                return base_output + '.' + suffix
            
            # 特殊处理：保留完整扩展名
            if self.special_handling and self.special_handling.get('preserve_full_extension'):
                return base_output + '.' + processed_info.get('extension', '')
            
            return base_output + extension
        except KeyError as e:
            return f"格式错误: 缺少 {e}"
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'name': self.name,
            'pattern': self.pattern,
            'groups': self.groups,
            'output_format': self.output_format
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RegexRule':
        """从字典创建规则"""
        return cls(
            name=data['name'],
            pattern=data['pattern'],
            groups=data['groups'],
            output_format=data['output_format'],
            special_handling=data.get('special_handling', {})
        )


class RuleFileManager:
    """规则文件管理器"""
    
    def __init__(self, rules_dir=DEFAULT_RULES_DIR):
        self.rules_dir = Path(rules_dir)
        self.rules_dir.mkdir(exist_ok=True)
    
    def load_all_rules(self) -> List[RegexRule]:
        """加载所有规则文件"""
        rules = []
        rule_files = glob.glob(str(self.rules_dir / "*.json"))
        
        for rule_file in rule_files:
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rule = RegexRule.from_dict(data)
                    rules.append(rule)
            except Exception as e:
                print(f"加载规则文件失败 {rule_file}: {e}")
        
        return rules
    
    def save_rule(self, rule: RegexRule) -> bool:
        """保存规则到文件"""
        try:
            rule_file = self.rules_dir / f"{rule.name}.json"
            with open(rule_file, 'w', encoding='utf-8') as f:
                json.dump(rule.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存规则失败: {e}")
            return False
    
    def delete_rule(self, rule_name: str) -> bool:
        """删除规则文件"""
        try:
            rule_file = self.rules_dir / f"{rule_name}.json"
            if rule_file.exists():
                rule_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"删除规则失败: {e}")
            return False
    
    def create_default_rules(self):
        """创建默认规则文件"""
        for rule_data in DEFAULT_RULES:
            rule = RegexRule(
                name=rule_data['name'],
                pattern=rule_data['pattern'],
                groups=rule_data['groups'],
                output_format=rule_data['output_format']
            )
            self.save_rule(rule)
