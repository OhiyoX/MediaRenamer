#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体文件智能重命名工具启动脚本
使用libs目录的模块化版本
"""

import sys
import os
from pathlib import Path

# 添加libs目录到Python路径
current_dir = Path(__file__).parent.absolute()
libs_dir = current_dir / "libs"
sys.path.insert(0, str(libs_dir))

# 导入并运行主程序
try:
    from gui.main_window import MainWindow
    
    def main():
        """
        主函数 - 启动媒体文件重命名工具
        
        创建并运行MainWindow应用程序实例
        """
        app = MainWindow()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保libs目录下所有模块文件都存在")
    input("按回车键退出...")
except Exception as e:
    print(f"运行错误: {e}")
    input("按回车键退出...")
