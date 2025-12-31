#!/usr/bin/env python3
"""
合并最终文档脚本
将所有标准化后的文件合并为一个完整文档
"""

import os
from pathlib import Path
from datetime import datetime

def merge_files():
    base_dir = Path('/Users/yunchang/Documents/GitHub/PDF_OCR_json')
    final_dir = base_dir / 'output' / 'final'
    output_file = base_dir / 'output' / '公共营养师三级历年真题_最终版.md'

    # 获取所有验证文件（排除报告文件）
    files = sorted([f for f in final_dir.glob('*.md') if not f.name.startswith('standardization')])

    print(f"找到 {len(files)} 个文件待合并")

    # 合并内容
    merged_content = []

    # 添加文档头
    merged_content.append("# 公共营养师三级历年真题汇编（验证版）\n")
    merged_content.append(f"\n> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    merged_content.append("> 内容来源：OCR识别版与文档解析版交叉验证\n")
    merged_content.append("> 格式标准：题号、选项、答案格式统一\n")
    merged_content.append("\n---\n")

    # 添加目录
    merged_content.append("\n## 目录\n\n")
    for i, file_path in enumerate(files, 1):
        # 从文件名提取信息
        name = file_path.stem  # 如 01_2025-06_真题
        parts = name.split('_')
        if len(parts) >= 3:
            year_month = parts[1]  # 2025-06
            doc_type = parts[2]     # 真题 or 答案
            year = year_month.split('-')[0]
            month = year_month.split('-')[1]
            merged_content.append(f"{i}. [{year}年{month}月{doc_type}](#{name})\n")
        else:
            merged_content.append(f"{i}. [{name}](#{name})\n")

    merged_content.append("\n---\n\n")

    # 合并每个文件的内容
    for file_path in files:
        print(f"处理: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 添加文件锚点
        anchor = file_path.stem
        merged_content.append(f'<a name="{anchor}"></a>\n\n')

        # 添加内容
        merged_content.append(content)
        merged_content.append("\n\n---\n\n")

    # 写入合并文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(merged_content))

    print(f"\n合并完成！输出文件: {output_file}")
    print(f"文件大小: {output_file.stat().st_size / 1024:.1f} KB")

    return output_file


if __name__ == '__main__':
    merge_files()
