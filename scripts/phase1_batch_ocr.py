#!/usr/bin/env python3
"""
Phase 1: 批量通用OCR识别
对所有图片进行通用文字识别，保存原始结果
"""

import json
import os
import re
import time
from datetime import datetime

from config import (
    IMAGE_DIR, RAW_OCR_DIR, REPORTS_DIR,
    REQUEST_INTERVAL, WATERMARK_KEYWORDS
)
from api import ocr_normal


def get_image_files():
    """获取所有图片文件，按页码排序"""
    files = []
    pattern = re.compile(r'三级历年真题及解析_(\d+)\.png')

    for filename in os.listdir(IMAGE_DIR):
        match = pattern.match(filename)
        if match:
            page_num = int(match.group(1))
            files.append((page_num, filename))

    # 按页码排序
    files.sort(key=lambda x: x[0])
    return files


def filter_watermark(lines: list) -> list:
    """过滤水印文字"""
    filtered = []
    for line in lines:
        # 检查是否包含水印关键词
        is_watermark = any(kw in line for kw in WATERMARK_KEYWORDS)
        if not is_watermark:
            filtered.append(line)
    return filtered


def process_single_image(page_num: int, filename: str) -> dict:
    """处理单张图片"""
    image_path = os.path.join(IMAGE_DIR, filename)

    # 调用OCR
    result = ocr_normal(image_path)

    # 构建输出
    output = {
        "page_num": page_num,
        "filename": filename,
        "success": result["success"],
        "timestamp": datetime.now().isoformat(),
    }

    if result["success"]:
        # 过滤水印
        raw_lines = result["line_texts"]
        filtered_lines = filter_watermark(raw_lines)

        output["raw_line_count"] = len(raw_lines)
        output["filtered_line_count"] = len(filtered_lines)
        output["line_texts"] = filtered_lines
        output["line_texts_raw"] = raw_lines  # 保留原始数据用于验证
        output["line_probs"] = result["line_probs"]
    else:
        output["error"] = result.get("error", "未知错误")
        output["line_texts"] = []

    return output


def run_batch_ocr(start_page: int = None, end_page: int = None, dry_run: bool = False):
    """
    批量OCR处理

    Args:
        start_page: 起始页码（包含），None表示从头开始
        end_page: 结束页码（包含），None表示到最后
        dry_run: 仅显示计划，不实际执行
    """
    # 获取文件列表
    all_files = get_image_files()
    print(f"共找到 {len(all_files)} 个图片文件")

    # 筛选范围
    files_to_process = []
    for page_num, filename in all_files:
        if start_page and page_num < start_page:
            continue
        if end_page and page_num > end_page:
            continue
        files_to_process.append((page_num, filename))

    print(f"本次处理 {len(files_to_process)} 个文件 (页码 {files_to_process[0][0]} - {files_to_process[-1][0]})")

    if dry_run:
        print("\n[Dry Run] 仅显示计划，不实际执行")
        for page_num, filename in files_to_process[:10]:
            print(f"  将处理: {filename}")
        if len(files_to_process) > 10:
            print(f"  ... 还有 {len(files_to_process) - 10} 个文件")
        return

    # 检查已处理的文件（支持断点续传）
    processed_pages = set()
    for f in os.listdir(RAW_OCR_DIR):
        if f.startswith("page_") and f.endswith(".json"):
            try:
                page_num = int(f[5:-5])
                processed_pages.add(page_num)
            except ValueError:
                pass

    # 过滤掉已处理的
    files_to_process = [(p, f) for p, f in files_to_process if p not in processed_pages]
    if processed_pages:
        print(f"跳过已处理的 {len(processed_pages)} 个文件")
    print(f"实际需要处理 {len(files_to_process)} 个文件")

    if not files_to_process:
        print("没有需要处理的文件")
        return

    # 开始处理
    success_count = 0
    fail_count = 0
    start_time = time.time()

    for i, (page_num, filename) in enumerate(files_to_process):
        # 进度显示
        progress = (i + 1) / len(files_to_process) * 100
        elapsed = time.time() - start_time
        if i > 0:
            eta = elapsed / i * (len(files_to_process) - i)
            eta_str = f"{eta/60:.1f}分钟"
        else:
            eta_str = "计算中..."

        print(f"[{progress:5.1f}%] 处理 {filename} (剩余时间: {eta_str})", end="", flush=True)

        # 处理
        result = process_single_image(page_num, filename)

        # 保存结果
        output_file = os.path.join(RAW_OCR_DIR, f"page_{page_num:03d}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if result["success"]:
            success_count += 1
            print(f" -> 成功 ({result['filtered_line_count']}行)")
        else:
            fail_count += 1
            print(f" -> 失败: {result.get('error', '未知')}")

        # QPS控制
        time.sleep(REQUEST_INTERVAL)

    # 统计
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  总耗时: {total_time/60:.1f} 分钟")
    print(f"  平均: {total_time/len(files_to_process):.2f} 秒/张")

    # 保存报告
    report = {
        "phase": "Phase1_BatchOCR",
        "timestamp": datetime.now().isoformat(),
        "total_files": len(files_to_process),
        "success_count": success_count,
        "fail_count": fail_count,
        "total_time_seconds": total_time,
        "start_page": files_to_process[0][0] if files_to_process else None,
        "end_page": files_to_process[-1][0] if files_to_process else None,
    }

    report_file = os.path.join(REPORTS_DIR, f"phase1_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告已保存: {report_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1: 批量通用OCR识别")
    parser.add_argument("--start", type=int, help="起始页码")
    parser.add_argument("--end", type=int, help="结束页码")
    parser.add_argument("--dry-run", action="store_true", help="仅显示计划")

    args = parser.parse_args()

    run_batch_ocr(
        start_page=args.start,
        end_page=args.end,
        dry_run=args.dry_run
    )
