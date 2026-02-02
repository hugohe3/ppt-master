---
description: 根据已有项目文件或参考模板生成一份新的 PPT 布局模板
---

# 创建新模板 Workflow

> 📖 **调用角色**：[Template_Designer](../roles/Template_Designer.md)

为**全局模板库**生成一套完整的 PPT 布局模板。

## 流程概览

```
收集信息 → 创建目录 → 调用 Template_Designer → 验证完整性
```

---

## 步骤 1：收集模板信息

向用户确认以下信息：

| 信息项 | 必填 | 说明 |
|--------|------|------|
| 新模板名称 | ✅ | 英文标识符，如 `my_company` |
| 模板中文名称 | ✅ | 用于文档描述 |
| 参考来源 | ⬜ | 现有项目或模板路径（可选） |
| 主题色 | ⬜ | 主导色 HEX 值（如有参考可自动提取） |
| 设计风格 | ⬜ | 简短描述适用场景和设计调性 |

**如有参考来源**，先分析其结构：

// turbo
```bash
ls -la "<参考来源路径>"
```

---

## 步骤 2：创建模板目录

// turbo
```bash
mkdir -p "templates/layouts/<新模板名称>"
```

> ⚠️ **输出位置**：全局模板输出到 `templates/layouts/`，项目模板输出到 `projects/<项目>/templates/`

---

## 步骤 3：调用 Template_Designer 角色

**切换到 Template_Designer 角色**，按照角色定义生成：

1. **design_spec.md** — 设计规范文档
2. **4 个核心模板** — 封面、章节、内容、结束页
3. **目录页（可选）** — 02_toc.svg

> 📖 **角色详情**：参见 [Template_Designer.md](../roles/Template_Designer.md)

---

## 步骤 4：验证模板完整性

// turbo
```bash
ls -la "templates/layouts/<新模板名称>"
```

**检查清单**：

- [ ] `design_spec.md` 包含完整设计规范
- [ ] 4 个核心模板齐全
- [ ] SVG viewBox 正确（`0 0 1280 720`）
- [ ] 占位符格式一致（`{{PLACEHOLDER}}`）

---

## 步骤 5：输出确认

```markdown
## ✅ 模板创建完成

**模板名称**: <新模板名称>（<中文名称>）
**模板路径**: `templates/layouts/<新模板名称>/`

### 包含文件

| 文件 | 状态 |
|------|------|
| `design_spec.md` | ✅ 完成 |
| `01_cover.svg` | ✅ 完成 |
| `02_chapter.svg` | ✅ 完成 |
| `03_content.svg` | ✅ 完成 |
| `04_ending.svg` | ✅ 完成 |
| `02_toc.svg` | ⬜ 可选 |
```

---

## 配色方案快速参考

| 风格 | 主导色 | 适用场景 |
|------|--------|----------|
| 科技蓝 | `#004098` | 认证、测评 |
| 麦肯锡 | `#005587` | 战略咨询 |
| 政府蓝 | `#003366` | 政府项目 |
| 商务灰 | `#2C3E50` | 通用商务 |

---

## 注意事项

1. **SVG 技术约束**：参见 [Template_Designer.md](../roles/Template_Designer.md) 技术约束章节
2. **配色一致性**：所有 SVG 文件使用相同配色
3. **占位符规范**：使用 `{{}}` 格式

> 📖 **详细规范**：参见 [Template_Designer.md](../roles/Template_Designer.md)
