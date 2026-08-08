# Book-to-Skill · 书到技能

把技术书 / PDF / 白皮书 / 设计规范 / 运营手册蒸馏成可导入的 AI Skill——不是检索原文，而是把书里方法论内化成可复用的工作流。

### 15 秒速览
- **这是什么**：一个「知识技能化」工具——把任意一本书或文档，变成 AI 能直接照着做的专业技能包。
- **给谁用**：开发者、自媒体人、企业培训、个人知识管理——任何想把「专业书里的方法」沉淀成「AI 工作流」的人。
- **解决什么痛点**：传统 RAG 只能让 AI「查得到」原文；本 Skill 让 AI「做得到」——把方法论提炼成决策规则、模板、反模式、心智模型，可移植、可触发、可复用。
- **能产出什么**：《Clean Code》→ 代码审查 Skill；品牌规范 → 自动审图 Skill；投资问答录 → 投研判断 Skill。

## 一句话介绍

**RAG 查得到，Skill 做得到。** 这个 Skill 把任何一本书变成一个「已经替读者消化好的专业知识包」：自动分章、蒸馏成决策规则 / 反模式 / 模板 / 心智模型，再组装成可导入的技能包。

## 安装

```bash
# WorkBuddy / QClaw / OpenClaw 用户
skillhub install book-to-skill

# 或从 ClawHub
clawhub install jiaxinmmhh/book-to-skill
```

## 使用方式

1. **解析脚手架**：给一本书的 PDF，自动切成章节切片（`sections/` + `structure.md`）。
2. **蒸馏知识**：按 `references/distill-guide.md` 的方法论，把「书里说了什么」重写成「怎么做」。
3. **组装 Skill**：生成可导入的 `<name>/SKILL.md` + `references/` 知识包。
4. **校验分发**：本地测试触发词，确认模型会按方法论执行。

## 典型场景

- 把《Clean Code》变成代码审查 Skill
- 把品牌设计规范变成自动审图 Skill
- 把投资问答录变成投资决策判断 Skill
- 把内部运营手册变成新人上岗 SOP Skill

## 依赖

- Python 3.10+
- `pdfplumber`（仅 Step 1 PDF 解析需要）

```bash
pip install pdfplumber
```

## 限制

- 目前仅支持文本型 PDF，图片扫描件需先 OCR。
- 蒸馏质量取决于原书结构和你的后处理投入，不是全自动魔法。

## 作者

- GitHub: [@jiaxinmmhh](https://github.com/jiaxinmmhh)
- 技能主页: https://clawhub.ai/jiaxinmmhh/skills/book-to-skill
