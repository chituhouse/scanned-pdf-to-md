# PDF OCR 题库项目

## 项目说明
将公共营养师三级历年真题PDF转换为结构化题库（JSON/Markdown/Word）。

## 目录结构
```
PDF_image/          # PDF提取的页面图片（371页）
output/
├── raw_ocr/        # 通用OCR原始结果
├── pdf_ocr/        # 智能文档解析结果
├── processed/      # 处理后的JSON
├── validated/      # 交叉验证后的分套题文件
└── *.md/*.docx     # 最终输出文档
scripts/            # Python处理脚本
reports/            # 处理报告
```

## 可用命令

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
