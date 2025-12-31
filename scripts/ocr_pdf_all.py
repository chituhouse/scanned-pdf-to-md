#!/usr/bin/env python3
"""
使用智能文档解析API处理所有页面
生成纯文档解析版Markdown
"""

import os
import re
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    IMAGE_DIR, OUTPUT_DIR, MAX_QPS, WATERMARK_KEYWORDS
)
from api import ocr_pdf

# 输出目录
PDF_OCR_DIR = os.path.join(OUTPUT_DIR, "pdf_ocr")
os.makedirs(PDF_OCR_DIR, exist_ok=True)

# 输出文件
OUTPUT_MD = os.path.join(OUTPUT_DIR, "公共营养师三级历年真题_文档解析版.md")


def get_all_images():
    """获取所有页面图片"""
    pattern = re.compile(r'三级历年真题及解析_(\d+)\.png')
    images = []

    for filename in os.listdir(IMAGE_DIR):
        match = pattern.match(filename)
        if match:
            page_num = int(match.group(1))
            images.append((page_num, os.path.join(IMAGE_DIR, filename)))

    return sorted(images, key=lambda x: x[0])


def filter_watermark(text):
    """过滤水印"""
    lines = text.split('\n')
    filtered = []
    for line in lines:
        if not any(kw in line for kw in WATERMARK_KEYWORDS):
            filtered.append(line)
    return '\n'.join(filtered)


def process_page(page_num, image_path):
    """处理单页"""
    cache_file = os.path.join(PDF_OCR_DIR, f"page_{page_num}.json")

    # 检查缓存
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 调用API
    result = ocr_pdf(image_path)

    if result['success']:
        markdown = filter_watermark(result['markdown'])
        data = {
            'page_num': page_num,
            'success': True,
            'markdown': markdown,
            'has_table': result['has_table']
        }
    else:
        data = {
            'page_num': page_num,
            'success': False,
            'error': result.get('error', '未知错误'),
            'markdown': ''
        }

    # 保存缓存
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def main():
    print("智能文档解析 - 全量处理")
    print("=" * 50)

    images = get_all_images()
    print(f"共 {len(images)} 页待处理")

    # 检查已处理的页数
    processed = len([f for f in os.listdir(PDF_OCR_DIR) if f.endswith('.json')])
    print(f"已缓存 {processed} 页")

    results = []
    success_count = 0
    fail_count = 0

    start_time = time.time()

    # 逐页处理（控制QPS）
    for i, (page_num, image_path) in enumerate(images):
        result = process_page(page_num, image_path)
        results.append(result)

        if result['success']:
            success_count += 1
        else:
            fail_count += 1
            print(f"  页 {page_num} 失败: {result.get('error')}")

        # 进度显示
        if (i + 1) % 20 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(images) - i - 1) / rate if rate > 0 else 0
            print(f"  进度: {i+1}/{len(images)} ({100*(i+1)/len(images):.1f}%) "
                  f"- 成功:{success_count} 失败:{fail_count} "
                  f"- 剩余约 {remaining/60:.1f} 分钟")

        # QPS控制
        time.sleep(1.0 / MAX_QPS)

    elapsed = time.time() - start_time
    print(f"\n处理完成: {success_count} 成功, {fail_count} 失败")
    print(f"耗时: {elapsed/60:.1f} 分钟")

    # 按页码排序
    results.sort(key=lambda x: x['page_num'])

    # 生成Markdown
    print("\n生成Markdown文档...")
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("# 公共营养师三级历年真题及答案解析\n\n")
        f.write(f"> **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
        f.write("> **数据来源**：火山引擎智能文档解析  \n\n")
        f.write("---\n\n")

        for result in results:
            page_num = result['page_num']
            f.write(f"<!-- 第 {page_num} 页 -->\n\n")

            if result['success']:
                f.write(result['markdown'])
            else:
                f.write(f"[识别失败: {result.get('error', '未知错误')}]\n")

            f.write("\n\n")

    file_size = os.path.getsize(OUTPUT_MD) / 1024
    print(f"\n已生成: {OUTPUT_MD}")
    print(f"文件大小: {file_size:.1f} KB")


if __name__ == "__main__":
    main()
