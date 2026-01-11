# PDF OCR 项目

## 项目说明
将扫描PDF/书籍图片转换为结构化电子文档，支持多种输出格式。

## 目录结构
```
PDF_image/          # 原有题库图片（371页）
人比 AI 凶/         # 扫描书籍图片（418页）
output/
├── raw_ocr/        # 通用OCR原始结果
├── pdf_ocr/        # 智能文档解析结果
├── book_ocr/       # 书籍OCR输出
├── processed/      # 处理后的JSON
├── validated/      # 交叉验证后的分套题文件
└── *.md/*.docx     # 最终输出文档
scripts/            # Python处理脚本
reports/            # 处理报告
```

## 可用命令

### /book-ocr
扫描书籍OCR转换：将扫描书籍图片转换为Markdown，支持图片提取，可输出Word/ePub/PDF等多种格式。

**特性：**
- 双路OCR交叉验证（通用OCR + 智能文档解析）
- 自动提取书中图表
- 多格式输出（Markdown/Word/ePub/PDF）

**工作流程：**
1. 确认输出格式（执行前必须确认）
2. 确认执行计划（执行前必须确认）
3. OCR识别 + 图片提取
4. Markdown整理
5. 格式转换

**使用方法：**
```
/book-ocr
```
然后按提示指定图片目录，选择输出格式。

---

### /cross-validate-ocr
OCR交叉验证：对比纯OCR版和文档解析版MD文档，逐套题验证，补齐缺失内容，清除干扰内容。

**输入文件：**
- `output/公共营养师三级历年真题_纯OCR版.md`
- `output/公共营养师三级历年真题_文档解析版.md`

**输出文件：**
- `output/validated/` 目录下的分套题文件
- `output/公共营养师三级历年真题_验证版.md`

**使用方法：**
直接输入 `/cross-validate-ocr` 启动交叉验证流程。

## API配置
- 火山引擎OCR API
- AK/SK 配置在 `scripts/config.py`

## 注意事项
- OCR结果可能包含水印残留（小象教育、抖音等），需过滤
- 表格页使用智能文档解析效果更好
- 交叉验证时严格遵循原文，不发挥不编造
