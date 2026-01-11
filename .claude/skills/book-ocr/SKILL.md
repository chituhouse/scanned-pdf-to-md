---
name: book-ocr
description: 扫描书籍OCR转换 - 将扫描书籍图片转换为Markdown，支持图片提取，可输出Word/ePub/PDF等多种格式。当用户需要将扫描书籍转换为电子文档时使用此技能。
---

# 扫描书籍 OCR 转换 Skill

将扫描书籍（JPG/PNG图片）转换为结构化电子文档，支持图片自动提取和多格式输出。

## 适用场景

- 扫描书籍数字化
- 得到/微信读书截图转文档
- 任何图片形式的书籍内容

## 工作流程概览

```
图片输入 → OCR识别 → 图片提取 → Markdown整理 → 格式转换
```

**核心原则**：Markdown 是源文件，所有其他格式都从 Markdown 转换生成。

```
                ┌──→ Word (.docx)
                │
Markdown (源) ──┼──→ ePub
                │
                └──→ PDF
```

---

## Phase 0：启动确认（必须执行）

### 0.1 检测输入

扫描用户指定的图片目录，统计：
- 图片数量
- 图片格式（JPG/PNG）
- 总大小

展示格式：
```markdown
### 0.1 输入检测

| 项目 | 内容 |
|:---|:---|
| 目录 | xxx |
| 图片数量 | xxx 页 |
| 图片格式 | JPG/PNG |
| 总大小 | xx MB |
```

### 0.2 输出格式确认

**必须在执行前向用户确认输出格式**，展示格式清单：

```markdown
### 0.2 输出格式确认

请选择需要的输出格式（输入数字，多选用逗号分隔，如：1,2）：

| 序号 | 格式 | 说明 | 用途 |
|:---|:---|:---|:---|
| 1 | Markdown | 源文件 + images/ 文件夹 | Obsidian / 知识管理 |
| 2 | Word (.docx) | 图片嵌入文档 | 交付客户 / 飞书导入 |
| 3 | ePub | 电子书格式 | 阅读器 / Kindle |
| 4 | PDF | 固定排版 | 打印 / 存档 |

默认：1,2

请输入数字：
```

**用户输入示例**：
- `1` → 仅 Markdown
- `1,2` → Markdown + Word
- `1,2,3` → Markdown + Word + ePub
- `1,2,3,4` 或 `1234` → 全部格式
- 直接回车 → 使用默认（1,2）

**等待用户输入后才能继续**

### 0.3 生成执行计划

根据用户选择的格式，生成详细计划清单。

**重要**：输出格式清单必须准确反映用户的选择，使用序号对应。

```markdown
### 0.3 执行计划

**已选择格式**：1, 2, 3（Markdown + Word + ePub）

#### 输入
| 项目 | 内容 |
|:---|:---|
| 目录 | xxx |
| 图片数量 | xxx 页 |
| 预计图表数量 | 约 xx 张 |

#### 输出格式（根据用户选择展示）
- [x] 1. Markdown + images/
- [x] 2. Word (.docx)
- [x] 3. ePub
- [ ] 4. PDF

#### 输出文件
```
output/book_ocr/书名/
├── 书名.md           ← Obsidian 用
├── 书名.docx         ← 交付客户
├── 书名.epub         ← 电子书阅读器
└── images/
    └── *.png
```

#### 处理步骤
| 阶段 | 任务 | 预计耗时 |
|:---|:---|:---|
| Phase 1 | 双路 OCR | ~xx 分钟 |
| Phase 2 | 图片提取 | ~xx 分钟 |
| Phase 3 | Markdown 整理 | ~xx 分钟 |
| Phase 4 | 格式转换（MD → Word, MD → ePub） | ~x 分钟 |

#### 预计成本
| 项目 | 费用 |
|:---|:---|
| OCR API | ¥xx |
| Claude API | ¥xx |
| 总计 | ¥xx |

**确认执行？** 输入 `y` 开始，输入 `n` 取消或修改
```

**等待用户确认后才能开始 Phase 1**

---

## Phase 1：OCR 识别

### 1.1 双路 OCR

对每页图片执行：
- **通用 OCR**：获取完整文字
- **智能文档解析**：获取段落结构 + 图片位置

```python
# 伪代码
for image in images:
    normal_result = ocr_normal(image)      # 通用OCR
    parsed_result = ocr_pdf(image)         # 智能文档解析
    save_result(normal_result, parsed_result)
```

### 1.2 输出

```
output/book_ocr/书名/
├── raw_normal/       # 通用OCR结果
│   ├── page_001.json
│   └── ...
└── raw_parsed/       # 文档解析结果
    ├── page_001.json
    └── ...
```

---

## Phase 2：图片提取

### 2.1 检测图片位置

从智能文档解析结果中提取 `label: "image"` 的区块，获取坐标：

```json
{
  "label": "image",
  "box": {"x0": 105, "y0": 450, "x1": 675, "y1": 798},
  "image_id": "fig_xxx"
}
```

### 2.2 裁剪图片

使用 Pillow 从原图裁剪：

```python
from PIL import Image

img = Image.open(page_image)
cropped = img.crop((box['x0'], box['y0'], box['x1'], box['y1']))
cropped.save(f'images/{image_id}.png')
```

### 2.3 输出

```
output/book_ocr/书名/images/
├── fig_0-1.png
├── fig_0-2.png
├── fig_2-29.png
└── ...
```

---

## Phase 3：Markdown 整理

### 3.1 交叉验证

对比两路 OCR 结果，取长补短：

| 内容类型 | 优先采用 | 原因 |
|:---|:---|:---|
| 段落结构 | 文档解析版 | 换行更准确 |
| 专有名词 | 对比两版 | 都可能出错 |
| 脚注上标 | 通用OCR | 文档解析会丢失 |
| 图片位置 | 文档解析版 | 有精确坐标 |

### 3.2 章节整理

- 识别章节标题（根据目录页）
- 添加 Markdown 标题层级（#, ##, ###）
- 整理段落，去除行末碎片换行

### 3.3 图片引用

在正文中插入图片引用：

```markdown
腾讯的一篇论文有一个特别有趣的发现（图2-29）。

![图2-29](images/fig_2-29.png)

这并不是因为错误答案想得深...
```

### 3.4 脚注整理

```markdown
萨顿是强化学习之父[^1]。

[^1]: Temporal Difference Learning，一种重要的强化学习算法。
```

### 3.5 输出

```
output/book_ocr/书名/
├── 书名.md           # 完整 Markdown（源文件）
└── images/           # 图片文件夹
```

---

## Phase 4：格式转换

**核心原则**：所有格式都从 Markdown 源文件转换，不是互相转换。

### 4.1 转换流程

```
                    ┌──→ pandoc → Word (.docx)
                    │
Markdown (源文件) ──┼──→ pandoc → ePub
                    │
                    └──→ pandoc → PDF
```

### 4.2 转换命令

根据用户选择的格式执行对应命令：

```bash
# MD → Word（用户选择了 2）
pandoc 书名.md -o 书名.docx

# MD → ePub（用户选择了 3）
pandoc 书名.md -o 书名.epub --metadata title="书名"

# MD → PDF（用户选择了 4）
pandoc 书名.md -o 书名.pdf --pdf-engine=xelatex -V CJKmainfont="PingFang SC"
```

### 4.3 最终输出

根据用户选择，输出对应的文件：

```
output/book_ocr/书名/
├── 书名.md           # 源文件（选择 1 时输出）
├── 书名.docx         # Word（选择 2 时输出）
├── 书名.epub         # ePub（选择 3 时输出）
├── 书名.pdf          # PDF（选择 4 时输出）
└── images/
    └── *.png
```

---

## 铁律（必须遵守）

1. **执行前必须确认格式**：展示数字选择清单，等待用户输入数字
2. **执行前必须确认计划**：展示详细计划，等待用户输入 y/n
3. **格式清单必须准确**：根据用户输入的数字展示对应的格式，不能混乱
4. **不发挥、不编造**：只使用 OCR 识别出的内容
5. **缺失标注**：无法识别的内容标注 `[OCR无法识别]`
6. **图片保留**：所有图表必须提取并引用，不能丢弃
7. **Markdown 为源**：所有其他格式从 MD 转换，不是互相转换

---

## 质量检查点

### Phase 1 完成后
- 报告 OCR 成功率
- 列出识别失败的页面

### Phase 2 完成后
- 报告提取的图片数量
- 抽样展示 3 张图片确认质量

### Phase 3 完成后
- 报告总字数、章节数、图片数
- 展示目录结构供确认

### Phase 4 完成后
- 确认所有用户选择的格式文件已生成
- 报告每个文件的大小

---

## 调用示例

用户输入：`/book-ocr`

执行流程：
1. 询问图片目录路径（或从参数获取）
2. 扫描目录，展示统计信息
3. **展示格式数字清单，等待用户输入数字**
4. **展示执行计划，等待用户输入 y/n**
5. 用户确认后执行 Phase 1-4
6. 输出最终文件

---

## 依赖工具

| 工具 | 用途 | 安装 |
|:---|:---|:---|
| 火山引擎 OCR | 文字识别 | API 配置 |
| Pillow | 图片裁剪 | `pip install pillow` |
| Pandoc | 格式转换 | `brew install pandoc` |
| python-docx | Word 处理 | `pip install python-docx` |

---

## 注意事项

- 大文件（500页+）建议分批处理
- 复杂数学公式可能需要截图保留
- 手写内容 OCR 效果较差，建议标注
- 输出前建议人工抽检 10% 内容
