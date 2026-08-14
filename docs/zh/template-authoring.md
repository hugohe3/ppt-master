# 模板制作与校验

[English](./template-authoring.md) | [中文](./zh/template-authoring.md)

自定义 `.pptx` 模板受支持，但不存在适用于所有工作流的统一占位符约定。PPT Master 有两条 PPTX 路线。请先选择路线，再使用对应的只读报告验证文件。

> 本仓库不提供 `python -m ppt_master` CLI。请使用下面的脚本入口，或使用聊天驱动的 Skill 工作流。

## 选择路线

| 路线 | 适用场景 | `.pptx` 的含义 | 校验工具 |
|---|---|---|---|
| Fill Native PPTX | 替换现有 deck 或 slide library 中的内容 | 分析并复用已有幻灯片形状 | `pptx_intake.py` |
| Create Template → Generate | 将 PPTX 导入为可复用模板工作区 | 导入 manifest 描述检测到的插槽 | `pptx_template_import.py --manifest-only` |

两条路线不共享统一占位符 schema。通用的 `check-template` 命令会掩盖这一差异。

## Fill Native PPTX 清单

1. 保留你希望被填充的形状。即使不是真正的 PowerPoint 占位符，样式化普通文本框也可以成为可填充插槽。
2. 每块内容尽量只有一个明显的主文本框。
3. 如果希望表格和图表作为数据对象处理，请保留原生对象。
4. 如果需要演讲者备注，请使用普通的备注文本框。
5. 生成前运行只读 intake 报告：

```bash
python3 skills/ppt-master/scripts/pptx_intake.py your.pptx
```

如果预期的标题、正文、表格、图表或备注区域没有出现在报告中，就不要指望生成过程能稳定定位它。

## Create Template → Generate 清单

1. 明确每张幻灯片/版式对应哪类页面。
2. 标题和正文尽量使用真正的 PowerPoint 占位符。
3. 如果正文区域只是样式化文本框，请检查 manifest，确认它是否被识别为可用插槽。
4. 表格和图表保留原生对象，或使用清晰表达意图的占位区域。
5. 只生成 manifest，不执行完整导入：

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py your.pptx --manifest-only
```

manifest 是模板路线检测结果的依据。不要仅凭形状名称推断行为。

## 推荐版式习惯

| 内容 | 实用习惯 |
|---|---|
| 标题 | 使用真正的标题占位符，或单个顶层标题文本框 |
| 正文/项目符号 | 使用真正的正文占位符，或一个明确的主文本框 |
| 图表 | 保留原生图表对象；不要把图表压成图片 |
| 表格 | 保留原生表格对象；不要把表格转成文本框 |
| 演讲者备注 | 使用普通备注页文本框 |
| 装饰性标签 | 与内容区域分离；为形状命名以便调试 |

## 问题排查

| 现象 | 首先检查 |
|---|---|
| 内容落入意外形状 | 对照可见文本框与 intake/manifest 报告 |
| 项目符号出现在默认/回退幻灯片上 | 在 Create Template 中，预期正文插槽未被识别；改用正文占位符或简化文本框 |
| 备注缺失 | 确认源幻灯片有备注文本框，且报告中可见 |
| 图表/表格未被复用 | 确认它是原生图表/表格，而不是图片或组合矢量 |
| 两条路线行为不同 | 确认当前使用的路线；它们不共享同一占位符 schema |

## 相关内容

- [FAQ](./faq.md)
- [模板使用指南](./templates-guide.md)
- [模板体系架构](./templates-architecture.md)
