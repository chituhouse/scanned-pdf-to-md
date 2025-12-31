#!/usr/bin/env python3
"""
项目配置文件模板
OCR题库生成项目 - 火山引擎API配置

使用说明：
1. 复制此文件为 config.py
2. 填入你的火山引擎API密钥
3. 根据需要调整其他配置
"""

import os

# ==================== API凭证 ====================
# 火山引擎 Access Key（请替换为你的密钥）
AK = "your_access_key_here"
SK = "your_secret_key_here"

# ==================== API配置 ====================
API_HOST = "visual.volcengineapi.com"
API_REGION = "cn-north-1"
API_SERVICE = "cv"

# 通用文字识别API
OCR_NORMAL_ACTION = "OCRNormal"
OCR_NORMAL_VERSION = "2020-08-26"

# 智能文档解析API
OCR_PDF_ACTION = "OCRPdf"
OCR_PDF_VERSION = "2021-08-23"

# ==================== 路径配置 ====================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 输入路径
IMAGE_DIR = os.path.join(PROJECT_ROOT, "PDF_image")

# 输出路径
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
RAW_OCR_DIR = os.path.join(OUTPUT_DIR, "raw_ocr")        # 通用OCR原始结果
TABLE_OCR_DIR = os.path.join(OUTPUT_DIR, "table_ocr")    # 表格页智能解析结果
PROCESSED_DIR = os.path.join(OUTPUT_DIR, "processed")    # 处理后的结果

# 报告路径
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

# ==================== 处理配置 ====================
# 并发控制
MAX_QPS = 8  # 最大QPS（留2个余量，API限制10）
REQUEST_INTERVAL = 1.0 / MAX_QPS  # 请求间隔（秒）

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 重试延迟（秒）

# 超时配置
REQUEST_TIMEOUT = 120  # 请求超时（秒）

# ==================== 水印过滤配置 ====================
# 根据你的PDF源文件中的水印内容自定义
WATERMARK_KEYWORDS = [
    "小象教育",
    "小象",
    # 添加更多水印关键词...
]

# ==================== 表格检测配置 ====================
TABLE_KEYWORDS = [
    "见下表",
    "如下表",
    "下表所示",
    "表格",
    "调查记录",
    "膳食调查",
    "食物频率",
]

# 表格检测阈值
TABLE_SHORT_LINE_RATIO = 0.35  # 短行比例阈值
TABLE_SHORT_LINE_LENGTH = 12   # 短行长度定义
TABLE_DIGIT_RATIO = 0.08       # 数字比例阈值

# ==================== 输出配置 ====================
# 最终JSON输出文件
FINAL_OUTPUT_FILE = os.path.join(PROCESSED_DIR, "questions_final.json")

# 确保目录存在
for dir_path in [RAW_OCR_DIR, TABLE_OCR_DIR, PROCESSED_DIR, REPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
