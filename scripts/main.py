#!/usr/bin/env python3
"""
OCR题库生成项目 - 主执行脚本
公共营养师三级历年真题 OCR识别与结构化

使用方法:
    python main.py              # 执行所有阶段
    python main.py --phase 1    # 只执行Phase 1
    python main.py --phase 1-3  # 执行Phase 1到3
    python main.py --dry-run    # 仅显示计划
"""

import argparse
import sys
import os

# 确保能导入同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """打印项目横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║           OCR 题库生成项目 - 公共营养师三级真题                 ║
║                      火山引擎 OCR API                         ║
╠══════════════════════════════════════════════════════════════╣
║  Phase 1: 批量通用OCR识别                                     ║
║  Phase 2: 表格页检测                                          ║
║  Phase 3: 智能文档解析（表格页）                               ║
║  Phase 4: 交叉验证                                            ║
║  Phase 5: 合并输出                                            ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_phase1(dry_run=False, start_page=None, end_page=None):
    """运行Phase 1: 批量通用OCR"""
    print("\n" + "=" * 60)
    print("Phase 1: 批量通用OCR识别")
    print("=" * 60)

    from phase1_batch_ocr import run_batch_ocr
    run_batch_ocr(start_page=start_page, end_page=end_page, dry_run=dry_run)


def run_phase2():
    """运行Phase 2: 表格检测"""
    print("\n" + "=" * 60)
    print("Phase 2: 表格页检测")
    print("=" * 60)

    from phase2_detect_tables import run_table_detection
    run_table_detection()


def run_phase3():
    """运行Phase 3-4: 智能文档解析"""
    print("\n" + "=" * 60)
    print("Phase 3-4: 智能文档解析（表格页）")
    print("=" * 60)

    from phase3_parse_tables import run_table_parsing
    run_table_parsing()


def run_phase5():
    """运行Phase 5-6: 合并输出"""
    print("\n" + "=" * 60)
    print("Phase 5-6: 交叉验证与合并输出")
    print("=" * 60)

    from phase5_merge_output import run_merge_output
    run_merge_output()


def parse_phase_range(phase_str):
    """解析阶段范围，如 "1-3" -> [1,2,3]"""
    if "-" in phase_str:
        start, end = phase_str.split("-")
        return list(range(int(start), int(end) + 1))
    else:
        return [int(phase_str)]


def main():
    parser = argparse.ArgumentParser(
        description="OCR题库生成项目 - 主执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 执行所有阶段
  python main.py --phase 1          # 只执行Phase 1
  python main.py --phase 1-3        # 执行Phase 1到3
  python main.py --phase 1 --dry-run # Phase 1 仅显示计划
  python main.py --phase 1 --start 1 --end 50  # Phase 1 处理页1-50
        """
    )

    parser.add_argument(
        "--phase", "-p",
        type=str,
        help="执行指定阶段，如 '1' 或 '1-3'，不指定则执行所有阶段"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示计划，不实际执行（仅对Phase 1有效）"
    )
    parser.add_argument(
        "--start",
        type=int,
        help="起始页码（仅对Phase 1有效）"
    )
    parser.add_argument(
        "--end",
        type=int,
        help="结束页码（仅对Phase 1有效）"
    )

    args = parser.parse_args()

    print_banner()

    # 确定要执行的阶段
    if args.phase:
        phases = parse_phase_range(args.phase)
    else:
        phases = [1, 2, 3, 5]  # 默认执行所有阶段

    print(f"将执行阶段: {phases}")

    # 执行各阶段
    for phase in phases:
        if phase == 1:
            run_phase1(
                dry_run=args.dry_run,
                start_page=args.start,
                end_page=args.end
            )
        elif phase == 2:
            run_phase2()
        elif phase in [3, 4]:
            if 3 in phases or 4 in phases:
                run_phase3()
                # 标记已执行，避免重复
                if 4 in phases:
                    phases.remove(4)
        elif phase in [5, 6]:
            if 5 in phases or 6 in phases:
                run_phase5()
                if 6 in phases:
                    phases.remove(6)
        else:
            print(f"未知阶段: {phase}")

    print("\n" + "=" * 60)
    print("执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
