#!/usr/bin/env python3
"""
Phase 2: 表格页检测
分析OCR结果，检测哪些页面包含表格，并识别跨页表格
"""

import json
import os
import re
from datetime import datetime

from config import (
    RAW_OCR_DIR, PROCESSED_DIR, REPORTS_DIR,
    TABLE_KEYWORDS, TABLE_SHORT_LINE_RATIO,
    TABLE_SHORT_LINE_LENGTH, TABLE_DIGIT_RATIO
)


def load_ocr_results():
    """加载所有OCR结果"""
    results = {}
    pattern = re.compile(r'page_(\d+)\.json')

    for filename in os.listdir(RAW_OCR_DIR):
        match = pattern.match(filename)
        if match:
            page_num = int(match.group(1))
            filepath = os.path.join(RAW_OCR_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                results[page_num] = json.load(f)

    return results


def detect_table_in_page(ocr_result: dict) -> dict:
    """
    检测单页是否包含表格

    Returns:
        {
            "has_table": bool,
            "confidence": float,  # 0-1
            "reasons": [str],
            "table_keywords_found": [str],
        }
    """
    lines = ocr_result.get("line_texts", [])
    if not lines:
        return {"has_table": False, "confidence": 0, "reasons": ["无文本"], "table_keywords_found": []}

    text = "\n".join(lines)
    reasons = []
    score = 0

    # 检查1：表格关键词
    keywords_found = [kw for kw in TABLE_KEYWORDS if kw in text]
    if keywords_found:
        score += 0.4
        reasons.append(f"包含表格关键词: {keywords_found}")

    # 检查2：短行比例（表格单元格通常是短文本）
    short_lines = [l for l in lines if len(l) < TABLE_SHORT_LINE_LENGTH]
    short_ratio = len(short_lines) / len(lines) if lines else 0
    if short_ratio > TABLE_SHORT_LINE_RATIO:
        score += 0.3
        reasons.append(f"短行比例高: {short_ratio:.2f}")

    # 检查3：数字密集度（表格常有数据）
    digit_count = sum(1 for c in text if c.isdigit())
    digit_ratio = digit_count / len(text) if text else 0
    if digit_ratio > TABLE_DIGIT_RATIO:
        score += 0.2
        reasons.append(f"数字密集: {digit_ratio:.2f}")

    # 检查4：规律性的短文本行（如表格行）
    # 连续多行长度相近
    if len(lines) >= 5:
        lengths = [len(l) for l in lines]
        # 检查是否有5行以上长度相近（差异<30%）
        similar_count = 0
        for i in range(len(lengths) - 1):
            if lengths[i] > 0 and abs(lengths[i] - lengths[i+1]) / lengths[i] < 0.3:
                similar_count += 1
        if similar_count >= 4:
            score += 0.1
            reasons.append(f"行长度规律: {similar_count}组相近")

    has_table = score >= 0.4  # 阈值

    return {
        "has_table": has_table,
        "confidence": min(score, 1.0),
        "reasons": reasons,
        "table_keywords_found": keywords_found,
    }


def detect_table_continuation(prev_result: dict, curr_result: dict, next_result: dict = None) -> dict:
    """
    检测表格是否跨页

    Returns:
        {
            "continues_from_prev": bool,  # 从上一页延续
            "continues_to_next": bool,    # 延续到下一页
        }
    """
    curr_lines = curr_result.get("line_texts", [])

    result = {
        "continues_from_prev": False,
        "continues_to_next": False,
    }

    if not curr_lines:
        return result

    # 检查是否从上一页延续（当前页开头没有标题/题号）
    if prev_result:
        first_line = curr_lines[0] if curr_lines else ""
        # 如果第一行不是标题/新题目开始，可能是表格延续
        if not re.match(r'^[\d一二三四五六七八九十]+[\.、]', first_line):
            if not any(kw in first_line for kw in ["《", "》", "真题", "答案"]):
                # 检查上一页最后是否有表格
                prev_detection = detect_table_in_page(prev_result)
                if prev_detection["has_table"]:
                    result["continues_from_prev"] = True

    # 检查是否延续到下一页（当前页末尾没有完整结束）
    if next_result:
        next_lines = next_result.get("line_texts", [])
        if next_lines:
            first_next_line = next_lines[0]
            # 如果下一页开头不是新的标题/题目
            if not re.match(r'^[\d一二三四五六七八九十]+[\.、]', first_next_line):
                if not any(kw in first_next_line for kw in ["《", "》", "真题", "答案"]):
                    result["continues_to_next"] = True

    return result


def group_table_pages(table_pages: list, ocr_results: dict) -> list:
    """
    将表格页分组（处理跨页表格）

    Args:
        table_pages: 包含表格的页码列表
        ocr_results: 所有OCR结果

    Returns:
        [[page1, page2], [page3], ...]  分组后的页码列表
    """
    if not table_pages:
        return []

    table_pages = sorted(table_pages)
    groups = []
    current_group = [table_pages[0]]

    for i in range(1, len(table_pages)):
        prev_page = table_pages[i - 1]
        curr_page = table_pages[i]

        # 如果页码连续，可能是跨页表格
        if curr_page == prev_page + 1:
            # 进一步验证
            prev_result = ocr_results.get(prev_page, {})
            curr_result = ocr_results.get(curr_page, {})
            continuation = detect_table_continuation(prev_result, curr_result)

            if continuation["continues_from_prev"]:
                current_group.append(curr_page)
            else:
                groups.append(current_group)
                current_group = [curr_page]
        else:
            groups.append(current_group)
            current_group = [curr_page]

    groups.append(current_group)
    return groups


def run_table_detection():
    """执行表格检测"""
    print("Phase 2: 表格页检测")
    print("=" * 50)

    # 加载OCR结果
    ocr_results = load_ocr_results()
    print(f"加载了 {len(ocr_results)} 页OCR结果")

    # 检测每页
    table_pages = []
    detection_details = {}

    for page_num in sorted(ocr_results.keys()):
        result = ocr_results[page_num]
        detection = detect_table_in_page(result)
        detection_details[page_num] = detection

        if detection["has_table"]:
            table_pages.append(page_num)
            print(f"  页 {page_num:3d}: 检测到表格 (置信度: {detection['confidence']:.2f})")
            for reason in detection["reasons"]:
                print(f"           {reason}")

    print(f"\n共检测到 {len(table_pages)} 页包含表格")

    # 分组跨页表格
    table_groups = group_table_pages(table_pages, ocr_results)
    print(f"\n表格分组（共 {len(table_groups)} 组）:")
    for i, group in enumerate(table_groups):
        if len(group) == 1:
            print(f"  组{i+1}: 页 {group[0]} (单页)")
        else:
            print(f"  组{i+1}: 页 {group[0]}-{group[-1]} (跨 {len(group)} 页)")

    # 保存结果
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_pages": len(ocr_results),
        "table_pages": table_pages,
        "table_page_count": len(table_pages),
        "table_groups": table_groups,
        "table_group_count": len(table_groups),
        "detection_details": {str(k): v for k, v in detection_details.items() if v["has_table"]},
    }

    output_file = os.path.join(PROCESSED_DIR, "table_detection.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n检测结果已保存: {output_file}")

    # 保存报告
    report_file = os.path.join(REPORTS_DIR, f"phase2_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"报告已保存: {report_file}")

    return output


if __name__ == "__main__":
    run_table_detection()
