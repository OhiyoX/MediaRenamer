#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体文件重命名工具配置文件
包含所有常量定义和配置项
"""

# 文件路径配置
DEFAULT_RULES_DIR = "rules"
BACKUP_DIR_NAME = "backup"
RENAME_LOG_NAME = "rename_log.json"  # 重命名记录文件名

# 支持的视频文件扩展名
SUPPORTED_VIDEO_EXTENSIONS = {
    '.mkv', '.mp4', '.avi', '.mov', '.wmv', 
    '.flv', '.webm', '.m4v', '.mpg', '.mpeg',
    '.3gp', '.ogv', '.ts', '.m2ts'
}

# 支持的字幕文件扩展名
SUPPORTED_SUBTITLE_EXTENSIONS = {
    '.srt', '.ass', '.ssa', '.sub', '.idx',
    '.vtt', '.ttml', '.dfxp', '.smi', '.sami'
}

# 所有支持的媒体文件扩展名（视频+字幕）
SUPPORTED_MEDIA_EXTENSIONS = SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_SUBTITLE_EXTENSIONS

# 热重载配置
RELOAD_COOLDOWN = 1.0  # 热重载冷却时间（秒）
MAX_RELOAD_LOG_ENTRIES = 50  # 最大重载日志条目数

# 父文件夹识别配置
ENABLE_PARENT_FOLDER_RECOGNITION = True  # 是否启用从父文件夹识别剧名和季数
PARENT_FOLDER_RECOGNITION_CONFIG = {
    'enable_series_recognition': True,  # 是否启用剧名识别
    'enable_season_recognition': True,  # 是否启用季数识别
    'enable_custom_season': True,  # 是否启用自定义季数设置
    'default_season': '01',  # 默认季数
    'season_patterns': [  # 季数识别模式
        r'S(\d+)',  # S01, S02
        r'Season\s*(\d+)',  # Season 1, Season 2
        r'第(\d+)季',  # 第1季, 第2季
    ]
}

# GUI配置
WINDOW_TITLE = "媒体文件智能重命名工具"
WINDOW_SIZE = "1600x1000"
TREEVIEW_COLUMN_WIDTH = 200

# 默认规则配置
DEFAULT_RULES = [
    {
        'name': '标准剧集格式',
        'pattern': r'\[([^\]]+)\]\s*(\d+)\s*(.+?)(?:\s*\[|\s*\(|$)',
        'groups': {'series': 1, 'episode': 2, 'title': 3},
        'output_format': '{series} S01E{episode:0>2} - {title}'
    },
    {
        'name': '电影格式',
        'pattern': r'(.+?)\s*\((\d{4})\)(?:\s*-\s*(.+?))?(?:\s*\[|\s*\(|$)',
        'groups': {'title': 1, 'year': 2, 'quality': 3},
        'output_format': '{title} ({year}) - {quality}'
    },
    {
        'name': '纪录片格式',
        'pattern': r'(.+?)\s*-\s*第(\d+)集\s*(.+?)(?:\s*\[|\s*\(|$)',
        'groups': {'series': 1, 'episode': 2, 'title': 3},
        'output_format': '{series} S01E{episode:0>2} - {title}'
    },
    {
        'name': '简单数字格式',
        'pattern': r'(.+?)\s*(\d+)(?:\s*-\s*(.+?))?(?:\s*\[|\s*\(|$)',
        'groups': {'series': 1, 'episode': 2, 'title': 3},
        'output_format': '{series} S01E{episode:0>2} - {title}'
    },
    {
        'name': '带季数剧集格式',
        'pattern': r'\[([^\]]+)\]\s*S(\d+)E(\d+)\s*(.+?)(?:\s*\[|\s*\(|$)',
        'groups': {'series': 1, 'season': 2, 'episode': 3, 'title': 4},
        'output_format': '{series} S{season:0>2}E{episode:0>2} - {title}'
    }
]

# 日志级别
LOG_LEVELS = {
    'INFO': 'INFO',
    'WARNING': 'WARNING', 
    'ERROR': 'ERROR',
    'SUCCESS': 'SUCCESS'
}

# 测试默认值
TEST_DEFAULT_FILENAME = ""
TEST_DEFAULT_REGEX = ""
TEST_DEFAULT_GROUPS = '{"series": 1, "episode": 2, "title": 3}'
TEST_DEFAULT_FORMAT = '{series} S01E{episode:0>2} - {title}'
