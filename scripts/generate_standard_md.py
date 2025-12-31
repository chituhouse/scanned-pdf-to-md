#!/usr/bin/env python3
"""
生成标准格式的Markdown文档
"""

import json
import re
import os
from datetime import datetime

# 路径配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_FILE = os.path.join(PROJECT_DIR, "output/processed/questions_final.json")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "output/公共营养师三级历年真题.md")


def clean_text(text: str) -> str:
    """清理文本"""
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)


def format_question_block(text: str) -> str:
    """格式化题目块"""
    lines = text.split('\n')
    formatted = []
    in_question = False
    question_buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            if question_buffer:
                formatted.append(' '.join(question_buffer))
                question_buffer = []
            formatted.append('')
            continue

        # 选项行
        option_match = re.match(r'^([A-D])[\.、:\s]+(.+)$', line)
        if option_match:
            if question_buffer:
                formatted.append(' '.join(question_buffer))
                question_buffer = []
            formatted.append(f"- **{option_match.group(1)}.** {option_match.group(2)}")
            continue

        # 题号开头
        q_match = re.match(r'^(\d+)[\.、,\s]+(.+)$', line)
        if q_match:
            if question_buffer:
                formatted.append(' '.join(question_buffer))
                question_buffer = []
            formatted.append('')
            formatted.append(f"**{q_match.group(1)}. {q_match.group(2)}**")
            in_question = True
            continue

        # 多选/单选标记
        if '【多选题】' in line or '【单选题】' in line:
            if question_buffer:
                formatted.append(' '.join(question_buffer))
                question_buffer = []
            formatted.append('')
            formatted.append(f"**{line}**")
            continue

        # 续行（题目可能跨行）
        if in_question and not line.startswith(('A', 'B', 'C', 'D', '一', '二', '三')):
            question_buffer.append(line)
        else:
            if question_buffer:
                formatted.append(' '.join(question_buffer))
                question_buffer = []
            formatted.append(line)

    if question_buffer:
        formatted.append(' '.join(question_buffer))

    return '\n'.join(formatted)


def is_toc_page(text: str) -> bool:
    """判断是否为目录页"""
    if '目录' in text[:50]:
        return True
    # 检测是否有多个页码模式（如 "真题 21"）
    page_refs = re.findall(r'真题(?:答案)?\s*\d{2,3}', text)
    return len(page_refs) > 5


def is_answer_section(text: str) -> bool:
    """判断是否为答案部分"""
    first_100 = text[:150]
    return '答案' in first_100 or '解析' in first_100


def get_section_type(text: str) -> str:
    """获取题型"""
    if re.search(r'[一二三四五六七八九十][、\.]\s*单项选择题', text):
        return "single"
    if re.search(r'[一二三四五六七八九十][、\.]\s*多项选择题', text):
        return "multiple"
    if re.search(r'[一二三四五六七八九十][、\.]\s*判断题', text):
        return "judge"
    if '技能' in text[:100] or '案例' in text[:100]:
        return "case"
    return None


def generate_standard_md():
    """生成标准格式Markdown"""
    print("读取数据...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pages = {p['page_num']: p for p in data['pages']}
    exams = data['exams']

    print(f"共 {len(pages)} 页，{len(exams)} 套考试")

    md_parts = []

    # 标题
    md_parts.append("# 公共营养师三级历年真题及答案解析\n\n")
    md_parts.append(f"> **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
    md_parts.append(f"> **数据来源**：火山引擎OCR识别  \n")
    md_parts.append(f"> **总页数**：{len(pages)} 页  \n\n")

    # 整理考试数据
    exam_list = []
    for exam in exams:
        start_page = exam['start_page']
        first_page = pages.get(start_page, {})
        content = first_page.get('markdown', '') or '\n'.join(first_page.get('text', []))

        # 跳过目录页
        if is_toc_page(content):
            continue

        year, month = exam['exam_id'].split('-')
        is_answer = is_answer_section(content)

        exam_list.append({
            'exam_id': exam['exam_id'],
            'year': year,
            'month': month,
            'is_answer': is_answer,
            'start_page': start_page,
            'end_page': exam['pages'][-1],
            'pages': exam['pages'],
            'title': f"{year}年{int(month)}月" + ("答案解析" if is_answer else "统考真题")
        })

    # 按年月排序
    exam_list.sort(key=lambda x: (x['year'], x['month'], x['is_answer']), reverse=True)

    # 生成目录
    md_parts.append("## 目录\n\n")
    md_parts.append("| 序号 | 内容 | 页码范围 |\n")
    md_parts.append("|:---:|:---|:---:|\n")

    for i, exam in enumerate(exam_list, 1):
        anchor = f"{exam['exam_id']}-{'ans' if exam['is_answer'] else 'exam'}"
        md_parts.append(f"| {i} | [{exam['title']}](#{anchor}) | 第{exam['start_page']}-{exam['end_page']}页 |\n")

    md_parts.append("\n---\n\n")

    # 正文内容
    for exam in exam_list:
        anchor = f"{exam['exam_id']}-{'ans' if exam['is_answer'] else 'exam'}"
        full_title = f"{exam['year']}年{int(exam['month'])}月公共营养师三级" + \
                     ("统考真题答案解析" if exam['is_answer'] else "统考真题")

        md_parts.append(f"## {full_title} {{#{anchor}}}\n\n")

        current_section = None

        for page_num in exam['pages']:
            page = pages.get(page_num, {})
            content = page.get('markdown', '') or '\n'.join(page.get('text', []))

            if not content.strip():
                continue

            # 跳过目录页内容
            if is_toc_page(content):
                continue

            # 检测题型变化
            section = get_section_type(content)
            if section and section != current_section:
                current_section = section
                section_names = {
                    "single": "单项选择题",
                    "multiple": "多项选择题",
                    "judge": "判断题",
                    "case": "案例分析题"
                }
                md_parts.append(f"\n### {section_names.get(section, section)}\n\n")

            # 表格页保持原样
            if page.get('is_table_page'):
                md_parts.append(content + "\n\n")
            else:
                # 格式化普通内容
                formatted = format_question_block(content)
                md_parts.append(formatted + "\n")

        md_parts.append("\n---\n\n")

    # 合并并清理
    final_md = ''.join(md_parts)
    final_md = re.sub(r'\n{4,}', '\n\n\n', final_md)
    final_md = re.sub(r'(\n-{3,}\n){2,}', '\n---\n\n', final_md)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_md)

    print(f"\n标准Markdown已生成: {OUTPUT_FILE}")
    print(f"文件大小: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")
    print(f"包含 {len(exam_list)} 套考试/答案")


if __name__ == "__main__":
    generate_standard_md()
