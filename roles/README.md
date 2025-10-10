# AI 角色定义

本文件夹包含 PPT Master 系统的四个核心 AI 角色定义文档。

## 角色概览

| 角色            | 文件                                               | 主要职责             | 输入     | 输出               |
| --------------- | -------------------------------------------------- | -------------------- | -------- | ------------------ |
| **策略师**      | [Strategist.md](./Strategist.md)                   | 内容分析与设计规划   | 源文档   | 设计规范与内容大纲 |
| **通用执行师**  | [Executor_General.md](./Executor_General.md)       | 生成通用灵活风格 SVG | 设计规范 | SVG 代码           |
| **咨询执行师**  | [Executor_Consultant.md](./Executor_Consultant.md) | 生成高端咨询风格 SVG | 设计规范 | SVG 代码           |
| **CRAP 优化师** | [Optimizer_CRAP.md](./Optimizer_CRAP.md)           | 基于 CRAP 原则优化   | SVG 代码 | 优化后的 SVG       |

## 工作流程

```
用户输入文档
    ↓
[Strategist] 策略师
    ↓ 生成《设计规范与内容大纲》
    ↓
[Executor_General / Executor_Consultant] 执行师
    ↓ 逐页生成SVG代码
    ↓
[Optimizer_CRAP] 优化师 (可选)
    ↓ CRAP原则优化
    ↓
最终SVG演示文稿
```

## 角色详解

### 1️⃣ Strategist (策略师)

**何时使用**: 项目开始时

**核心能力**:

- 智能解构源文档内容
- 确定设计风格（通用灵活 vs 高端咨询）
- 制定完整的色彩方案
- 规划页面序列和布局
- 定义排版体系

**关键输出**: 《演示文稿设计规范与内容大纲》

📄 [查看完整定义](./Strategist.md)

---

### 2️⃣ Executor_General (通用执行师)

**何时使用**: 采用通用灵活风格时

**核心能力**:

- 严格遵循 Strategist 的设计规范
- 逐页生成 SVG 代码
- 动态调整视觉平衡
- 支持迭代修改

**技术特点**:

- 画布尺寸: 1280×720 (16:9)
- 禁用 `<foreignObject>`
- 使用 `<tspan>` 手动换行
- 强制卡片高度规则

📄 [查看完整定义](./Executor_General.md)

---

### 3️⃣ Executor_Consultant (咨询执行师)

**何时使用**: 采用高端咨询风格时

**核心能力**:

- 采用麦肯锡、BCG 等顶尖咨询公司风格
- 数据驱动的可视化设计
- KPI 仪表盘和图表优化
- 专业配色方案应用

**设计特点**:

- 简洁、高端、数据驱动
- 使用图表可视化关键信息
- 融入行业标准的设计元素
- 强调专业感和视觉冲击力

📄 [查看完整定义](./Executor_Consultant.md)

---

### 4️⃣ Optimizer_CRAP (CRAP 优化师)

**何时使用**: 需要进一步优化视觉质量时

**核心能力**:

- 基于 CRAP 四大设计原则分析和优化
- 诊断视觉问题
- 重构 SVG 代码
- 提升专业度和清晰度

**四大原则**:

1. **Contrast (对比)** - 创造视觉层次
2. **Repetition (重复)** - 统一视觉风格
3. **Alignment (对齐)** - 建立视觉连接
4. **Proximity (亲密性)** - 组织信息关系

📄 [查看完整定义](./Optimizer_CRAP.md)

---

## 使用建议

### 基本流程

1. 从 **Strategist** 开始，获取设计规范
2. 根据风格选择 **Executor_General** 或 **Executor_Consultant**
3. 逐页生成 SVG
4. （可选）使用 **Optimizer_CRAP** 优化关键页面

### 最佳实践

- ✅ 充分与 Strategist 沟通，确保规范完整
- ✅ 每生成一页都验证效果
- ✅ 保持所有页面风格统一
- ✅ 关键页面使用 Optimizer 提升质量
- ✅ 保存规范文档供后续参考

### 常见场景

**场景 1: 高管汇报**
→ Strategist (选 B 咨询风格) → Executor_Consultant → Optimizer_CRAP

**场景 2: 团队分享**
→ Strategist (选 A 通用风格) → Executor_General

**场景 3: 快速迭代**
→ Strategist → Executor → 修改 → Executor (重新生成)

## 扩展与定制

### 自定义角色

如果需要特定行业的风格（如科技、金融、教育），可以基于现有角色创建变体。

### 角色组合

可以混合使用不同风格的 Executor，例如封面使用咨询风格，内容页使用通用风格。

## 相关文档

- [主 README](../README.md) - 项目整体介绍
- [设计指南](../docs/design_guidelines.md) - 详细设计规范
- [工作流教程](../docs/workflow_tutorial.md) - 实战案例教程
- [贡献指南](../CONTRIBUTING.md) - 如何参与项目

## 反馈与改进

如果你在使用这些角色时有任何建议或发现问题，欢迎：

- 提交 Issue
- 发起 Discussion
- 提交 Pull Request

---

让 AI 角色帮你创造专业的演示文稿！✨
