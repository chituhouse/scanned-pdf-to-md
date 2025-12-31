#!/usr/bin/env python3
"""
格式标准化脚本
统一OCR验证文件的格式，确保前后一致
"""

import re
import os
from pathlib import Path

# 干扰内容模式
INTERFERENCE_PATTERNS = [
    r'小象教育',
    r'小鱼教育',
    r'小东教育',
    r'小家教育',
    r'小蒙教育',
    r'小爱教育',
    r'小徐教育',
    r'小敦教育',
    r'小蔡教育',
    r'小熊教育',
    r'小米教育',
    r'i象教育',
    r'象教育',
    r'教育$',  # 行尾单独的"教育"
    r'抖音',
    r'douyin',
    r'www\.',
    r'http',
    r'^\d+$',  # 单独的数字行（页码）
]

def standardize_format(content: str) -> tuple[str, list[str]]:
    """
    标准化文档格式
    返回: (标准化后的内容, 修改记录列表)
    """
    changes = []
    lines = content.split('\n')
    new_lines = []

    for i, line in enumerate(lines, 1):
        original_line = line

        # 规则1: 题号格式 - 数字.xxx → 数字. xxx
        # 匹配行首的数字+点，后面不是空格的情况
        if re.match(r'^\d+\.(?!\s)', line):
            line = re.sub(r'^(\d+)\.(?!\s)', r'\1. ', line)
            if line != original_line:
                changes.append(f"行{i}: 题号添加空格")

        # 规则2: 选项格式 - A.xxx → A. xxx
        # 匹配行首的A/B/C/D+点，后面不是空格的情况
        if re.match(r'^[A-D]\.(?!\s)', line):
            line = re.sub(r'^([A-D])\.(?!\s)', r'\1. ', line)
            if line != original_line:
                changes.append(f"行{i}: 选项添加空格")

        # 规则3: 答案格式 - 数字.【答案】→ 数字. 【答案】
        if re.match(r'^\d+\.【', line):
            line = re.sub(r'^(\d+)\.【', r'\1. 【', line)
            if line != original_line:
                changes.append(f"行{i}: 答案格式修复")

        # 规则4: 清理干扰内容
        skip_line = False
        for pattern in INTERFERENCE_PATTERNS:
            if re.search(pattern, line):
                # 如果整行就是干扰内容，跳过
                if re.match(rf'^{pattern}$', line.strip()) or re.match(r'^\d+$', line.strip()):
                    skip_line = True
                    changes.append(f"行{i}: 删除干扰内容 '{line.strip()}'")
                    break
                else:
                    # 部分匹配，删除匹配部分
                    new_line = re.sub(pattern, '', line)
                    if new_line != line:
                        changes.append(f"行{i}: 清除干扰内容 '{pattern}'")
                        line = new_line

        if not skip_line:
            new_lines.append(line)

    return '\n'.join(new_lines), changes


def process_file(input_path: Path, output_path: Path) -> dict:
    """
    处理单个文件
    返回: 处理报告
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    standardized_content, changes = standardize_format(content)

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(standardized_content)

    return {
        'file': input_path.name,
        'changes_count': len(changes),
        'changes': changes
    }


def main():
    base_dir = Path('/Users/yunchang/Documents/GitHub/PDF_OCR_json')
    validated_dir = base_dir / 'output' / 'validated'
    final_dir = base_dir / 'output' / 'final'

    # 创建输出目录
    final_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有验证文件
    files = sorted(validated_dir.glob('*.md'))

    reports = []
    total_changes = 0

    print("=" * 60)
    print("格式标准化处理开始")
    print("=" * 60)

    for file_path in files:
        output_path = final_dir / file_path.name
        report = process_file(file_path, output_path)
        reports.append(report)
        total_changes += report['changes_count']

        status = f"修改 {report['changes_count']} 处" if report['changes_count'] > 0 else "无需修改"
        print(f"[{'修复' if report['changes_count'] > 0 else '完成'}] {report['file']}: {status}")

    print("=" * 60)
    print(f"处理完成: 共 {len(files)} 个文件, {total_changes} 处修改")
    print("=" * 60)

    # 生成详细报告
    report_path = final_dir / 'standardization_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 格式标准化报告\n\n")
        f.write(f"## 处理统计\n\n")
        f.write(f"- 处理文件数: {len(files)}\n")
        f.write(f"- 总修改数: {total_changes}\n\n")
        f.write("## 详细修改记录\n\n")

        for report in reports:
            if report['changes_count'] > 0:
                f.write(f"### {report['file']}\n\n")
                f.write(f"修改数: {report['changes_count']}\n\n")
                for change in report['changes'][:20]:  # 最多显示20条
                    f.write(f"- {change}\n")
                if len(report['changes']) > 20:
                    f.write(f"- ... 还有 {len(report['changes']) - 20} 条\n")
                f.write("\n")

    print(f"\n详细报告已保存到: {report_path}")

    return reports


if __name__ == '__main__':
    main()
