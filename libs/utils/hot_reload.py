#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载工具模块
负责代码热重载和文件监控功能
"""

import sys
import importlib
import time
from pathlib import Path
from typing import List, Callable, Optional

# 可选依赖
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("警告: watchdog库未安装，热重载功能将被禁用")
    # 创建一个空的基类作为替代
    class FileSystemEventHandler:
        """空的基类，用于替代watchdog的FileSystemEventHandler"""
        pass

from libs.config import RELOAD_COOLDOWN, MAX_RELOAD_LOG_ENTRIES


class CodeReloadHandler(FileSystemEventHandler):
    """代码热重载处理器"""
    
    def __init__(self, reload_callback: Callable):
        self.reload_callback = reload_callback
        self.last_reload_time = 0
        self.reload_cooldown = RELOAD_COOLDOWN
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory or not event.src_path.endswith('.py'):
            return
        
        current_time = time.time()
        if current_time - self.last_reload_time < self.reload_cooldown:
            return
        
        self.last_reload_time = current_time
        self.reload_callback()
    
    def on_created(self, event):
        """文件创建事件处理"""
        self.on_modified(event)


class HotReloadManager:
    """热重载管理器"""
    
    def __init__(self):
        self.file_observer: Optional[Observer] = None
        self.reload_enabled = True
        self.reload_log: List[str] = []
        self.reload_callback: Optional[Callable] = None
    
    def set_reload_callback(self, callback: Callable):
        """设置重载回调函数"""
        self.reload_callback = callback
    
    def start_file_monitoring(self):
        """启动文件监控"""
        if not self.reload_enabled or not self.reload_callback:
            return
        
        if not WATCHDOG_AVAILABLE:
            self.add_reload_log("watchdog库未安装，热重载功能不可用", "WARNING")
            return
        
        try:
            # 获取当前脚本所在目录
            current_dir = Path(__file__).parent.parent.absolute()
            
            # 创建文件监控器
            self.file_observer = Observer()
            handler = CodeReloadHandler(self.reload_callback)
            self.file_observer.schedule(handler, str(current_dir), recursive=True)
            
            # 启动监控
            self.file_observer.start()
            
            # 记录启动日志
            self.add_reload_log("文件监控已启动", "INFO")
            
        except Exception as e:
            self.add_reload_log(f"启动文件监控失败: {e}", "ERROR")
    
    def stop_file_monitoring(self):
        """停止文件监控"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None
            self.add_reload_log("文件监控已停止", "INFO")
    
    def add_reload_log(self, message: str, level: str = "INFO"):
        """添加重载日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.reload_log.append(log_entry)
        
        # 保持日志数量在合理范围内
        if len(self.reload_log) > MAX_RELOAD_LOG_ENTRIES:
            self.reload_log = self.reload_log[-MAX_RELOAD_LOG_ENTRIES:]
        
        print(log_entry)  # 同时输出到控制台
    
    def clear_reload_log(self):
        """清空重载日志"""
        self.reload_log.clear()
        self.add_reload_log("日志已清空", "INFO")
    
    def toggle_reload(self, enabled: bool):
        """切换热重载状态"""
        self.reload_enabled = enabled
        if enabled:
            self.start_file_monitoring()
            self.add_reload_log("热重载已启用", "INFO")
        else:
            self.stop_file_monitoring()
            self.add_reload_log("热重载已禁用", "INFO")
    
    def manual_reload(self, module_name: str = None):
        """手动触发重载"""
        self.add_reload_log("手动触发重载", "INFO")
        
        if module_name and module_name != "__main__":
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    self.add_reload_log(f"模块 {module_name} 重载完成", "SUCCESS")
                else:
                    self.add_reload_log(f"模块 {module_name} 不存在", "ERROR")
            except Exception as e:
                self.add_reload_log(f"重载模块 {module_name} 失败: {e}", "ERROR")
        else:
            self.add_reload_log("跳过主模块重载", "INFO")
