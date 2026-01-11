# PDF-OCR-CrossValidator

> 双源OCR交叉验证流水线 | PDF试题文档智能处理工具

基于Claude Code的PDF试题OCR处理解决方案，采用双OCR源交叉验证策略，显著提升识别准确率。

---

## 特性

- **双源交叉验证**：结合通用OCR和智能文档解析，互补优势
- **自动格式标准化**：统一选项格式、括号类型
- **干扰内容清除**：自动识别并删除水印、页码等干扰
- **逐套验证模式**：确保每套试题质量可控
- **验证报告生成**：透明记录所有修复操作
- **Claude Code Skill**：一键启动交叉验证流程

---

## 适用场景

- 历年真题PDF转结构化题库
- 考试资料数字化
- 大批量试题OCR处理
- 需要高准确率的文档识别场景

---

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-username/PDF-OCR-CrossValidator.git
cd PDF-OCR-CrossValidator

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API

复制配置模板并填入你的火山引擎API密钥：

```bash
cp scripts/config.example.py scripts/config.py
```

编辑 `scripts/config.py`：

```python
VOLC_AK = "your_access_key"
VOLC_SK = "your_secret_key"
```

### 3. 准备数据

将PDF转换为PNG图片，放入 `PDF_image/` 目录：

```
PDF_image/
├── page_01.png
├── page_02.png
└── ...
```

### 4. 执行OCR处理

```bash
# 路径A：通用OCR
python scripts/phase1_batch_ocr.py

# 路径B：智能文档解析
python scripts/phase3_parse_tables.py
```

### 5. 执行交叉验证

在Claude Code中输入：

```
/cross-validate-ocr
```

按提示逐套确认验证结果。

---

## 目录结构

```
PDF-OCR-CrossValidator/
├── .claude/
│   └── skills/
│       └── cross-validate-ocr/
│           └── SKILL.md          # 交叉验证技能定义
├── PDF_image/                     # PDF提取的页面图片
├── output/
│   ├── raw_ocr/                   # 通用OCR原始结果
│   ├── pdf_ocr/                   # 智能文档解析结果
│   └── validated/                 # 验证后的分套题文件
├── scripts/
│   ├── config.example.py          # 配置模板
│   ├── api.py                     # OCR API封装
│   ├── phase1_batch_ocr.py        # 批量OCR处理
│   ├── phase2_detect_tables.py    # 表格检测
│   ├── phase3_parse_tables.py     # 表格解析
│   └── phase5_merge_output.py     # 输出合并
├── docs/
│   └── SOP_OCR交叉验证流水线.md    # 完整SOP文档
├── reports/                       # 处理报告
├── CLAUDE.md                      # Claude Code项目配置
└── README.md
```

---

## 工作原理

### 双源互补策略

```
┌─────────────────┐     ┌─────────────────┐
│   通用OCR        │     │  智能文档解析    │
│                 │     │                 │
│ 优势：           │     │ 优势：           │
│ - 文字完整度高   │     │ - 表格结构识别   │
│ - 题号识别稳定   │     │ - 选项换行准确   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │     交叉验证合并       │
         │                       │
         │ - 对比两个版本        │
         │ - 补齐缺失内容        │
         │ - 清除干扰内容        │
         │ - 统一格式规范        │
         └───────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │     高质量输出         │
         └───────────────────────┘
```

### 验证规则

| 规则 | 说明 |
|:---|:---|
| 不发挥、不编造 | 只使用源文档中已有的内容 |
| 不猜测答案 | 缺失内容标注 `[缺失]` |
| 保留原文 | 只修复格式，不修改文字 |

### 优先级

| 内容类型 | 优先采用 |
|:---|:---|
| 表格 | 文档解析版 |
| 选项文本 | 文档解析版 |
| 题目文本 | 对比取更完整的 |
| 题号 | 纯OCR版 |

---

## 输出格式

### 验证报告

```markdown
# 2025年6月公共营养师三级统考真题

## 验证报告

### 统计
- 总题数：110（单选70 + 多选15 + 案例选择25）
- 修复项：12
- 待确认：0

### 修复记录
1. 第5题：补齐选项D（来源：纯OCR版）
2. 第12题：删除干扰内容"小象教育"

---

## 正文内容
...
```

### 分套文件命名

```
XX_YYYY-MM_类型.md

示例：
01_2025-06_真题.md
02_2025-06_答案.md
```

---

## 自定义配置

### 添加干扰内容

编辑 `.claude/skills/cross-validate-ocr/SKILL.md`：

```markdown
#### 2.4 干扰内容清除
必须删除的干扰内容：
- `小象教育`
- `抖音`
- `你的自定义内容`
```

### 调整格式规范

根据你的试题格式要求，修改Skill文件中的格式规范部分。

---

## 技术栈

- **OCR服务**：火山引擎（通用OCR + 智能文档解析）
- **处理框架**：Claude Code + Custom Skill
- **脚本语言**：Python 3.8+
- **输出格式**：Markdown / JSON / Word

---

## 文档

- [完整SOP文档](docs/SOP_OCR交叉验证流水线.md)
- [Claude Code项目配置](CLAUDE.md)
- [Skill定义](.claude/skills/cross-validate-ocr/SKILL.md)

---

## 许可证

MIT License

---

## 贡献

欢迎提交Issue和Pull Request。

---

## 致谢

- 火山引擎OCR服务
- Claude Code by Anthropic

---

*Made with Claude Code*
