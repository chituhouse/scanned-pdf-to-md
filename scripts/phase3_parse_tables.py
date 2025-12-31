#!/usr/bin/env python3
"""
Phase 3-4: 智能文档解析（表格页）
对检测到的表格页使用智能文档解析API，获取Markdown格式的表格
"""

import json
import os
import time
from datetime import datetime

from config import (
    IMAGE_DIR, TABLE_OCR_DIR, PROCESSED_DIR, REPORTS_DIR,
    REQUEST_INTERVAL
)
from api import ocr_pdf


def load_table_detection():
    """加载表格检测结果"""
    detection_file = os.path.join(PROCESSED_DIR, "table_detection.json")
    if not os.path.exists(detection_file):
        print(f"错误: 未找到表格检测结果 {detection_file}")
        print("请先运行 Phase 2: python phase2_detect_tables.py")
        return None

    with open(detection_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_image_path(page_num: int) -> str:
    """获取页码对应的图片路径"""
    filename = f"三级历年真题及解析_{page_num:02d}.png"
    path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(path):
        return path

    # 尝试不带前导零的格式
    filename = f"三级历年真题及解析_{page_num}.png"
    path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(path):
        return path

    return None


def process_table_group(group: list) -> dict:
    """
    处理一组表格页（可能是跨页表格）

    Args:
        group: 页码列表 [page1, page2, ...]

    Returns:
        {
            "pages": [page1, page2],
            "success": bool,
            "markdown_parts": [md1, md2],  # 每页的markdown
            "merged_markdown": str,  # 合并后的markdown
            "raw_responses": [...]
        }
    """
    result = {
        "pages": group,
        "success": True,
        "markdown_parts": [],
        "raw_responses": [],
        "errors": [],
    }

    for page_num in group:
        image_path = get_image_path(page_num)
        if not image_path:
            result["success"] = False
            result["errors"].append(f"页 {page_num}: 图片不存在")
            result["markdown_parts"].append("")
            continue

        # 调用智能文档解析
        ocr_result = ocr_pdf(image_path, table_mode="markdown")

        if ocr_result["success"]:
            result["markdown_parts"].append(ocr_result["markdown"])
            result["raw_responses"].append(ocr_result["raw_response"])
        else:
            result["success"] = False
            result["errors"].append(f"页 {page_num}: {ocr_result.get('error', '未知错误')}")
            result["markdown_parts"].append("")
            result["raw_responses"].append(ocr_result.get("raw_response"))

        # QPS控制
        time.sleep(REQUEST_INTERVAL)

    # 合并markdown（对于跨页表格）
    result["merged_markdown"] = "\n\n".join(filter(None, result["markdown_parts"]))

    return result


def run_table_parsing():
    """执行表格页解析"""
    print("Phase 3-4: 智能文档解析（表格页）")
    print("=" * 50)

    # 加载表格检测结果
    detection = load_table_detection()
    if not detection:
        return

    table_groups = detection.get("table_groups", [])
    if not table_groups:
        print("没有检测到表格页，无需处理")
        return

    print(f"共有 {len(table_groups)} 组表格需要处理")
    for i, group in enumerate(table_groups):
        print(f"  组{i+1}: 页 {group}")

    # 检查已处理的
    processed_groups = set()
    for f in os.listdir(TABLE_OCR_DIR):
        if f.startswith("table_group_") and f.endswith(".json"):
            processed_groups.add(f)

    # 开始处理
    results = []
    success_count = 0
    fail_count = 0
    start_time = time.time()

    for i, group in enumerate(table_groups):
        group_id = f"table_group_{i+1:03d}"
        output_file = os.path.join(TABLE_OCR_DIR, f"{group_id}.json")

        # 检查是否已处理
        if os.path.exists(output_file):
            print(f"[{i+1}/{len(table_groups)}] 组 {group} 已处理，跳过")
            with open(output_file, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
            continue

        print(f"[{i+1}/{len(table_groups)}] 处理组 {group}...", end="", flush=True)

        # 处理
        result = process_table_group(group)
        result["group_id"] = group_id
        result["timestamp"] = datetime.now().isoformat()

        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 同时保存markdown文件
        md_file = os.path.join(TABLE_OCR_DIR, f"{group_id}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- 表格组 {group_id}, 页码: {group} -->\n\n")
            f.write(result["merged_markdown"])

        results.append(result)

        if result["success"]:
            success_count += 1
            print(f" -> 成功")
        else:
            fail_count += 1
            print(f" -> 失败: {result['errors']}")

    # 统计
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  总耗时: {total_time:.1f} 秒")

    # 生成汇总
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_groups": len(table_groups),
        "success_count": success_count,
        "fail_count": fail_count,
        "total_time_seconds": total_time,
        "groups": [
            {
                "group_id": r["group_id"],
                "pages": r["pages"],
                "success": r["success"],
                "errors": r.get("errors", []),
            }
            for r in results
        ]
    }

    summary_file = os.path.join(PROCESSED_DIR, "table_parsing_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n汇总已保存: {summary_file}")

    # 保存报告
    report_file = os.path.join(REPORTS_DIR, f"phase3_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"报告已保存: {report_file}")

    return summary


if __name__ == "__main__":
    run_table_parsing()
