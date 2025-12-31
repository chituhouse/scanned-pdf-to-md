#!/usr/bin/env python3
"""
Phase 5-6: 交叉验证与合并输出
- 合并通用OCR和智能文档解析的结果
- 对表格页进行交叉验证
- 生成最终的结构化输出
"""

import json
import os
import re
from datetime import datetime

from config import (
    RAW_OCR_DIR, TABLE_OCR_DIR, PROCESSED_DIR, REPORTS_DIR,
    FINAL_OUTPUT_FILE
)


def load_all_ocr_results():
    """加载所有通用OCR结果"""
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


def load_table_results():
    """加载表格解析结果"""
    results = {}
    pattern = re.compile(r'table_group_(\d+)\.json')

    for filename in os.listdir(TABLE_OCR_DIR):
        match = pattern.match(filename)
        if match:
            filepath = os.path.join(TABLE_OCR_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 为每个页码建立映射
                for page_num in data.get("pages", []):
                    results[page_num] = data

    return results


def load_table_detection():
    """加载表格检测结果"""
    detection_file = os.path.join(PROCESSED_DIR, "table_detection.json")
    if os.path.exists(detection_file):
        with open(detection_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"table_pages": [], "detection_details": {}}


def get_real_table_pages(detection: dict) -> set:
    """
    获取真正的表格页（只有包含明确表格指示词的页面）

    明确的表格指示词：见下表、如下表、下表所示、表格、调查记录
    排除仅包含"膳食调查"或"食物频率"的页面（可能只是题目提及）
    """
    real_table_pages = set()

    # 明确的表格指示词
    explicit_table_keywords = ["见下表", "如下表", "下表所示", "表格", "调查记录"]

    details = detection.get("detection_details", {})
    for page_str, detail in details.items():
        keywords = detail.get("table_keywords_found", [])
        # 只有包含明确表格指示词的才算真正的表格页
        if any(kw in keywords for kw in explicit_table_keywords):
            real_table_pages.add(int(page_str))

    return real_table_pages


def validate_table_content(ocr_text: str, table_markdown: str) -> dict:
    """
    交叉验证表格内容

    对比通用OCR的文本和智能文档解析的Markdown，检查一致性
    """
    # 提取关键数字和文字
    ocr_numbers = set(re.findall(r'\d+\.?\d*', ocr_text))
    table_numbers = set(re.findall(r'\d+\.?\d*', table_markdown))

    # 计算数字重合度
    if ocr_numbers and table_numbers:
        common = ocr_numbers & table_numbers
        number_match_ratio = len(common) / max(len(ocr_numbers), len(table_numbers))
    else:
        number_match_ratio = 0

    # 提取中文词汇（简单分词）
    ocr_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}', ocr_text))
    table_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}', table_markdown))

    if ocr_words and table_words:
        common_words = ocr_words & table_words
        word_match_ratio = len(common_words) / max(len(ocr_words), len(table_words))
    else:
        word_match_ratio = 0

    # 综合评分
    consistency_score = (number_match_ratio + word_match_ratio) / 2

    return {
        "consistency_score": consistency_score,
        "number_match_ratio": number_match_ratio,
        "word_match_ratio": word_match_ratio,
        "is_consistent": consistency_score > 0.5,  # 阈值
        "ocr_numbers_count": len(ocr_numbers),
        "table_numbers_count": len(table_numbers),
    }


def extract_markdown_tables(text: str) -> list:
    """
    从智能文档解析结果中提取Markdown表格

    Returns:
        [(start_pos, end_pos, table_markdown), ...]
    """
    tables = []
    lines = text.split('\n')
    table_start = None
    table_lines = []

    for i, line in enumerate(lines):
        # 表格行以 | 开头
        if line.strip().startswith('|'):
            if table_start is None:
                table_start = i
            table_lines.append(line)
        else:
            if table_start is not None and len(table_lines) >= 2:
                # 表格结束，保存
                tables.append({
                    'start_line': table_start,
                    'end_line': i - 1,
                    'markdown': '\n'.join(table_lines)
                })
            table_start = None
            table_lines = []

    # 处理末尾的表格
    if table_start is not None and len(table_lines) >= 2:
        tables.append({
            'start_line': table_start,
            'end_line': len(lines) - 1,
            'markdown': '\n'.join(table_lines)
        })

    return tables


def merge_page_content(page_num: int, ocr_result: dict, table_result: dict = None,
                       is_table_page: bool = False) -> dict:
    """
    合并单页内容

    混合策略：
    - 表格部分：使用智能文档解析的Markdown表格
    - 非表格部分（选择题等）：使用通用OCR的文本
    """
    content = {
        "page_num": page_num,
        "is_table_page": is_table_page,
        "source": "ocr_normal",  # 默认来源
    }

    ocr_lines = ocr_result.get("line_texts", [])
    ocr_text = "\n".join(ocr_lines)

    if is_table_page and table_result:
        # 混合策略：提取表格，其余用通用OCR
        table_markdown = table_result.get("merged_markdown", "")
        tables = extract_markdown_tables(table_markdown)

        if tables:
            content["source"] = "hybrid"  # 混合来源

            # 识别OCR中的表格区域并替换
            merged_parts = []
            table_inserted = False
            in_table_data = False
            table_markers = ["见下表", "如下表", "下表所示"]

            # 表格数据特征
            table_data_patterns = [
                '食物名称', '是否食用', '平均每次', '次/日', '次/周', '次/月', '次/年',
                '根据表格', '表某社区', '调查记录'
            ]

            for i, line in enumerate(ocr_lines):
                line_stripped = line.strip()

                # 检测表格区域开始
                if any(marker in line for marker in table_markers) and not table_inserted:
                    merged_parts.append(line)
                    # 插入Markdown表格
                    merged_parts.append("\n" + tables[0]['markdown'] + "\n")
                    table_inserted = True
                    in_table_data = True
                    continue

                # 表格已插入后，跳过所有表格相关数据直到遇到题号
                if table_inserted and in_table_data:
                    # 检测真正的题号（通常 > 20，因为表格行号是1-14）
                    # 题号特征：数字较大 + 包含【或有明确题目特征
                    q_match = re.match(r'^(\d+)[\.\、]', line_stripped)
                    if q_match:
                        q_num = int(q_match.group(1))
                        # 题号通常 > 20，且常包含【多选题】【单选题】等
                        is_real_question = (
                            q_num > 20 or  # 题号大于20
                            '【' in line_stripped or  # 包含题型标记
                            len(line_stripped) > 30  # 行较长，像是题目
                        )
                        if is_real_question:
                            in_table_data = False
                            merged_parts.append(line)
                            continue

                    # 表格数据行特征（跳过）
                    # 包括：表格关键词、短行、纯数字行、表格行号+食物名
                    is_table_data = (
                        any(p in line for p in table_data_patterns) or
                        len(line_stripped) < 15 or  # 短行更可能是表格碎片
                        re.match(r'^[\d\.\s两个克g半]+$', line_stripped) or
                        re.match(r'^[A-D][\.\、\s]*$', line_stripped) or  # 孤立选项字母
                        re.match(r'^\d{1,2}[\.\、][\u4e00-\u9fa5]{1,6}$', line_stripped)  # 表格行号+食物名
                    )

                    if is_table_data:
                        continue  # 跳过表格数据碎片

                merged_parts.append(line)

            content["markdown"] = "\n".join(merged_parts)
        else:
            # 没有提取到表格，直接用通用OCR
            content["markdown"] = ocr_text

        content["text"] = ocr_lines  # 保留原始OCR文本
    else:
        # 普通页：使用通用OCR结果
        content["text"] = ocr_result.get("line_texts", [])
        content["markdown"] = "\n".join(ocr_result.get("line_texts", []))

    return content


def extract_exam_structure(pages_content: list) -> list:
    """
    从页面内容中提取考试结构

    识别年份、题型等信息
    """
    exams = []
    current_exam = None
    current_section = None

    # 年份标题模式
    exam_pattern = re.compile(r'(20\d{2})\s*年\s*(\d+)\s*月.*?(?:公共营养师|统考|真题)')
    section_pattern = re.compile(r'([一二三四五六七八九十]+)[、\.]\s*(单项选择题|多项选择题|判断题|简答题|案例)')

    for page in pages_content:
        text = "\n".join(page.get("text", [])) if page.get("text") else page.get("markdown", "")

        # 检测新考试
        exam_match = exam_pattern.search(text)
        if exam_match:
            if current_exam:
                exams.append(current_exam)

            year = exam_match.group(1)
            month = exam_match.group(2)
            current_exam = {
                "exam_id": f"{year}-{month.zfill(2)}",
                "title": exam_match.group(0),
                "start_page": page["page_num"],
                "sections": [],
                "pages": [page["page_num"]],
            }
            current_section = None
            continue

        # 检测题型
        section_match = section_pattern.search(text)
        if section_match and current_exam:
            section_type = section_match.group(2)
            current_section = {
                "type": section_type,
                "start_page": page["page_num"],
                "pages": [page["page_num"]],
            }
            current_exam["sections"].append(current_section)

        # 累加页码
        if current_exam:
            if page["page_num"] not in current_exam["pages"]:
                current_exam["pages"].append(page["page_num"])
            if current_section and page["page_num"] not in current_section["pages"]:
                current_section["pages"].append(page["page_num"])

    if current_exam:
        exams.append(current_exam)

    return exams


def run_merge_output():
    """执行合并输出"""
    print("Phase 5-6: 交叉验证与合并输出")
    print("=" * 50)

    # 加载数据
    ocr_results = load_all_ocr_results()
    table_results = load_table_results()
    table_detection = load_table_detection()

    # 获取真正的表格页（只有明确包含表格指示词的）
    real_table_pages = get_real_table_pages(table_detection)
    all_detected_table_pages = set(table_detection.get("table_pages", []))

    print(f"加载了 {len(ocr_results)} 页OCR结果")
    print(f"加载了 {len(table_results)} 页表格解析结果")
    print(f"检测到的表格页: {len(all_detected_table_pages)} 页")
    print(f"真正的表格页（含明确指示词）: {len(real_table_pages)} 页")

    # 合并每页内容
    pages_content = []
    validation_warnings = []

    for page_num in sorted(ocr_results.keys()):
        ocr_result = ocr_results[page_num]
        # 只对真正的表格页使用智能文档解析结果
        is_table_page = page_num in real_table_pages
        table_result = table_results.get(page_num) if is_table_page else None

        content = merge_page_content(
            page_num, ocr_result, table_result, is_table_page
        )
        pages_content.append(content)

        if content.get("warning"):
            validation_warnings.append({
                "page": page_num,
                "warning": content["warning"],
                "validation": content.get("validation"),
            })

    print(f"\n合并了 {len(pages_content)} 页内容")

    if validation_warnings:
        print(f"\n发现 {len(validation_warnings)} 个验证警告:")
        for w in validation_warnings[:5]:
            print(f"  页 {w['page']}: {w['warning']}")
        if len(validation_warnings) > 5:
            print(f"  ... 还有 {len(validation_warnings) - 5} 个")

    # 提取考试结构
    exams = extract_exam_structure(pages_content)
    print(f"\n识别到 {len(exams)} 套考试:")
    for exam in exams:
        print(f"  {exam['exam_id']}: {exam['title'][:30]}... (页 {exam['start_page']}-{exam['pages'][-1]})")

    # 生成最终输出
    output = {
        "metadata": {
            "source": "公共营养师三级历年真题",
            "total_pages": len(pages_content),
            "table_pages": len(real_table_pages),
            "detected_table_pages": len(all_detected_table_pages),
            "exam_count": len(exams),
            "created_at": datetime.now().isoformat(),
            "ocr_api": "火山引擎",
        },
        "exams": exams,
        "pages": pages_content,
        "validation_warnings": validation_warnings,
    }

    # 保存最终输出
    with open(FINAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n最终输出已保存: {FINAL_OUTPUT_FILE}")

    # 生成合并后的Markdown文件
    merged_md_file = os.path.join(PROCESSED_DIR, "merged_content.md")
    with open(merged_md_file, 'w', encoding='utf-8') as f:
        for page in pages_content:
            f.write(f"\n\n<!-- ===== 第 {page['page_num']} 页 ===== -->\n\n")
            if page.get("is_table_page"):
                f.write(f"[表格页]\n\n")
            f.write(page.get("markdown", ""))
    print(f"合并Markdown已保存: {merged_md_file}")

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_pages": len(pages_content),
        "table_pages": len(real_table_pages),
        "detected_table_pages": len(all_detected_table_pages),
        "exam_count": len(exams),
        "validation_warning_count": len(validation_warnings),
        "exams_summary": [
            {"exam_id": e["exam_id"], "page_range": f"{e['start_page']}-{e['pages'][-1]}"}
            for e in exams
        ],
    }

    report_file = os.path.join(REPORTS_DIR, f"phase5_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告已保存: {report_file}")

    return output


if __name__ == "__main__":
    run_merge_output()
