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

from libs.config import DEFAULT_RULES_DIR, DEFAULT_RULES


class RegexRule:
    """正则表达式规则类"""
    
    def __init__(self, name: str, pattern: str, groups: Dict[str, int], output_format: str, special_handling: Dict = None):
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
    
    def generate_output(self, extracted_info: Dict[str, str], extension: str = "") -> str:
        """根据提取的信息生成输出文件名"""
        try:
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
            
            # 特殊处理：空episode字段
            if 'episode' in processed_info and not processed_info['episode']:
                processed_info['episode'] = '01'  # 默认为01
            
            # 特殊处理：检查是否是年份而不是集数
            if 'episode' in processed_info and self.special_handling:
                episode_num = processed_info['episode']
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
