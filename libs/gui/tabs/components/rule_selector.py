#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则选择组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional
from libs.core.rule import RegexRule


class RuleSelector:
    """规则选择组件"""
    
    def __init__(self, parent_frame: ttk.Frame, rules: List[RegexRule], 
                 on_rule_selected: Callable[[str], None],
                 on_validate_rules: Callable[[], None],
                 on_reload_rules: Callable[[], None],
                 on_scan_files: Callable[[], None],
                 on_clear_applied_rules: Callable[[], None],
                 on_apply_rules_auto_first: Callable[[], None],
                 on_batch_match_rules: Callable[[], None]):
        self.parent_frame = parent_frame
        self.rules = rules
        self.on_rule_selected = on_rule_selected
        self.on_validate_rules = on_validate_rules
        self.on_reload_rules = on_reload_rules
        self.on_scan_files = on_scan_files
        self.on_clear_applied_rules = on_clear_applied_rules
        self.on_apply_rules_auto_first = on_apply_rules_auto_first
        self.on_batch_match_rules = on_batch_match_rules
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        rule_frame = ttk.LabelFrame(self.parent_frame, text="规则选择")
        rule_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行：规则选择
        rule_select_frame = ttk.Frame(rule_frame)
        rule_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(rule_select_frame, text="选择规则:").pack(side=tk.LEFT, padx=5)
        self.rule_var = tk.StringVar()
        self.rule_combo = ttk.Combobox(rule_select_frame, textvariable=self.rule_var, width=30)
        self.rule_combo.pack(side=tk.LEFT, padx=5)
        self.rule_combo.bind('<<ComboboxSelected>>', self.on_rule_selected)
        
        # 更新规则下拉框
        self.update_rule_combo()
        
        # 第二行：操作按钮
        button_frame = ttk.Frame(rule_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="验证所有规则", command=self.on_validate_rules).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="重新加载规则", command=self.on_reload_rules).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="扫描文件", command=self.on_scan_files).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="清除所有应用规则", command=self.on_clear_applied_rules).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="应用规则(自动匹配优先)", command=self.on_apply_rules_auto_first).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="自动匹配规则", command=self.on_batch_match_rules).pack(side=tk.RIGHT, padx=5)
        
        # 应用规则说明标签
        self.apply_info_label = ttk.Label(button_frame, text="", foreground="gray")
        self.apply_info_label.pack(side=tk.LEFT, padx=10)
    
    def update_rule_combo(self):
        """更新规则下拉框"""
        rule_names = [rule.name for rule in self.rules]
        self.rule_combo['values'] = rule_names
        if rule_names and not self.rule_var.get():
            self.rule_combo.set(rule_names[0])
    
    def get_selected_rule_name(self) -> str:
        """获取选中的规则名称"""
        return self.rule_var.get()
    
    def set_selected_rule_name(self, rule_name: str):
        """设置选中的规则名称"""
        self.rule_var.set(rule_name)
    
    def update_rules(self, new_rules: List[RegexRule]):
        """更新规则列表"""
        self.rules = new_rules
        self.update_rule_combo()
    
    def update_apply_info(self, applied_count: int, total_count: int):
        """更新应用规则说明信息"""
        if applied_count == 0:
            self.apply_info_label.config(text="没有应用任何规则")
        elif applied_count == total_count:
            self.apply_info_label.config(text=f"已应用规则到所有文件 ({applied_count}/{total_count})")
        else:
            self.apply_info_label.config(text=f"已应用规则到部分文件 ({applied_count}/{total_count})")
    
    def validate_all_rules(self):
        """验证所有规则文件的JSON与正则可用性"""
        import json, glob, re
        from pathlib import Path
        from libs.core.rule import RuleFileManager
        
        # 获取规则目录
        rule_manager = RuleFileManager()
        rules_dir = rule_manager.rules_dir
        rule_files = glob.glob(str(rules_dir / "*.json"))
        errors = []
        checked = 0
        
        for rf in rule_files:
            checked += 1
            try:
                with open(rf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 基本字段
                name = data.get('name')
                pattern = data.get('pattern')
                groups = data.get('groups', {})
                output_format = data.get('output_format')
                if not all([name, pattern, groups is not None, output_format]):
                    errors.append(f"{Path(rf).name}: 必填字段缺失")
                    continue
                # 编译正则
                re.compile(pattern)
                # 校验分组索引为数字
                for k, v in groups.items():
                    if not isinstance(v, int):
                        errors.append(f"{Path(rf).name}: 分组 '{k}' 索引不是整数")
                        break
            except Exception as e:
                errors.append(f"{Path(rf).name}: {e}")
        
        if errors:
            messagebox.showerror("规则验证结果", "发现问题:\n" + "\n".join(errors[:50]))
        else:
            messagebox.showinfo("规则验证结果", f"已验证 {checked} 个规则文件，未发现错误。")
