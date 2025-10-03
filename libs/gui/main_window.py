#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
负责应用程序的主界面和各个标签页的协调
"""

import tkinter as tk
import sys
from tkinter import ttk
from typing import List

from libs.core.rule import RegexRule, RuleFileManager
from libs.core.file_manager import FileManager
from libs.utils.hot_reload import HotReloadManager
import libs.gui.tabs.file_processing as file_processing_tab
import libs.gui.tabs.rule_testing as rule_testing_tab
import libs.gui.tabs.rule_management as rule_management_tab
import libs.gui.tabs.hot_reload as hot_reload_tab
from libs.config import WINDOW_TITLE, WINDOW_SIZE


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # 核心组件
        self.rule_manager = RuleFileManager()
        self.file_manager = FileManager()
        self.hot_reload_manager = HotReloadManager()
        
        # 数据
        self.rules: List[RegexRule] = []
        
        # 标签页
        self.tabs = {}
        
        # 初始化
        self.load_rules()
        self.create_widgets()
        self.setup_hot_reload()
    
    def load_rules(self):
        """加载所有规则"""
        self.rules = self.rule_manager.load_all_rules()
        
        # 如果没有规则，创建默认规则
        if not self.rules:
            self.rule_manager.create_default_rules()
            self.rules = self.rule_manager.load_all_rules()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页（通过模块引用类，确保热重载后获取最新定义）
        self.tabs['file_processing'] = file_processing_tab.FileProcessingTab(self.notebook, self.rule_manager, self.rules, self)
        self.tabs['rule_testing'] = rule_testing_tab.RuleTestingTab(self.notebook, self.rule_manager, self.rules)
        self.tabs['rule_management'] = rule_management_tab.RuleManagementTab(self.notebook, self.rule_manager, self.rules)
        self.tabs['hot_reload'] = hot_reload_tab.HotReloadTab(self.notebook, self.hot_reload_manager, self)
        
        # 强制更新布局
        self.root.update_idletasks()
        self.root.update()
        
        # 设置最小窗口大小
        self.root.minsize(1200, 800)
        
        # 确保窗口正确显示
        self.root.after(100, self._ensure_window_display)
    
    def _ensure_window_display(self):
        """确保窗口正确显示所有组件"""
        try:
            # 强制更新所有待处理的任务
            self.root.update_idletasks()
            
            # 获取当前窗口大小
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            
            # 如果窗口太小，调整到合适大小
            if current_width < 1200 or current_height < 800:
                self.root.geometry("1400x900")
                self.root.update_idletasks()
            
            # 再次更新布局
            self.root.update()
            
            # 确保所有标签页都正确显示
            for tab_name, tab in self.tabs.items():
                if hasattr(tab, 'frame'):
                    tab.frame.update_idletasks()
            
        except Exception as e:
            print(f"窗口显示检查时出错: {e}")
    
    def setup_hot_reload(self):
        """设置热重载"""
        # 创建不跳转的热重载回调
        def reload_callback():
            self.reload_code(auto_switch_tab=False)
        
        self.hot_reload_manager.set_reload_callback(reload_callback)
        self.hot_reload_manager.start_file_monitoring()
    
    def reload_code(self, auto_switch_tab=True):
        """热重载代码"""
        try:
            self.hot_reload_manager.add_reload_log("开始热重载...", "INFO")
            
            # 重新加载核心模块
            self.reload_modules()
            
            # 重新加载规则
            self.load_rules()
            
            # 重新创建标签页
            self.recreate_tabs()
            
            # 强制更新界面
            self.root.update_idletasks()
            self.root.update()
            
            # 根据参数决定是否切换到热重载标签页
            if auto_switch_tab:
                try:
                    if hasattr(self, 'notebook') and self.notebook:
                        # 找到热重载标签页
                        for tab_id in self.notebook.tabs():
                            tab_text = self.notebook.tab(tab_id, "text")
                            if "热重载" in tab_text:
                                self.notebook.select(tab_id)
                                break
                except:
                    pass
            
            self.hot_reload_manager.add_reload_log("热重载完成", "SUCCESS")
            
        except Exception as e:
            self.hot_reload_manager.add_reload_log(f"热重载失败: {e}", "ERROR")
    
    def recreate_tabs(self):
        """重新创建标签页"""
        try:
            # 获取当前选中的标签页
            current_tab = None
            if hasattr(self, 'notebook') and self.notebook:
                try:
                    current_tab = self.notebook.select()
                except:
                    current_tab = None
            
            # 销毁现有标签页
            if hasattr(self, 'notebook') and self.notebook:
                try:
                    # 获取所有标签页ID
                    tab_ids = list(self.notebook.tabs())
                    for tab_id in tab_ids:
                        try:
                            self.notebook.forget(tab_id)
                        except:
                            pass
                except:
                    pass
            
            # 强制更新界面
            if hasattr(self, 'root') and self.root:
                self.root.update_idletasks()
            
            # 重新创建标签页（通过模块引用类，确保热重载后获取最新定义）
            self.tabs['file_processing'] = file_processing_tab.FileProcessingTab(self.notebook, self.rule_manager, self.rules, self)
            self.tabs['rule_testing'] = rule_testing_tab.RuleTestingTab(self.notebook, self.rule_manager, self.rules)
            self.tabs['rule_management'] = rule_management_tab.RuleManagementTab(self.notebook, self.rule_manager, self.rules)
            self.tabs['hot_reload'] = hot_reload_tab.HotReloadTab(self.notebook, self.hot_reload_manager, self)
            
            # 恢复选中的标签页
            if current_tab and hasattr(self, 'notebook') and self.notebook:
                try:
                    self.notebook.select(current_tab)
                except:
                    pass
            
            self.hot_reload_manager.add_reload_log("标签页重新创建完成", "SUCCESS")
            
        except Exception as e:
            self.hot_reload_manager.add_reload_log(f"重新创建标签页失败: {e}", "ERROR")
    
    def reload_modules(self):
        """重新加载模块"""
        import importlib
        
        # 动态收集所有已加载的 libs.* 模块，确保子模块也会被重载
        loaded_lib_modules = [
            name for name in list(sys.modules.keys()) if name.startswith('libs.')
        ]
        
        # 父包优先（名称短的先重载），减少依赖顺序问题
        loaded_lib_modules.sort(key=len)
        
        for module_name in loaded_lib_modules:
            try:
                module_obj = sys.modules.get(module_name)
                if module_obj is not None:
                    importlib.reload(module_obj)
                    self.hot_reload_manager.add_reload_log(f"模块 {module_name} 重载完成", "SUCCESS")
            except Exception as e:
                self.hot_reload_manager.add_reload_log(f"重载模块 {module_name} 失败: {e}", "ERROR")
    
    def run(self):
        """运行GUI"""
        try:
            self.root.mainloop()
        finally:
            # 程序退出时清理资源
            self.hot_reload_manager.stop_file_monitoring()
            self.hot_reload_manager.add_reload_log("程序已退出", "INFO")
