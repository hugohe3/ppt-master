# AI 角色定义

本文件夹包含 PPT Master 系统的核心 AI 角色定义文档。

> 📖 **完整工作流程和使用指南**：请参阅 [AGENTS.md](../AGENTS.md)

## 角色速查表

| 角色 | 文件 | 职责 | 触发条件 |
|------|------|------|----------|
| **策略师** | [Strategist.md](./Strategist.md) | 八项确认 + 设计规范 | 项目启动时（必须） |
| **模板设计师** | [Template_Designer.md](./Template_Designer.md) | 生成页面模板 | 使用 `/create-template` 工作流 |
| **图片生成师** | [Image_Generator.md](./Image_Generator.md) | AI 图片生成 | 图片方式含「C) AI 生成」 |
| **通用执行师** | [Executor_General.md](./Executor_General.md) | 通用灵活风格 SVG | 选择「A) 通用灵活」 |
| **咨询执行师** | [Executor_Consultant.md](./Executor_Consultant.md) | 一般咨询风格 SVG | 选择「B) 一般咨询」 |
| **顶级咨询执行师** | [Executor_Consultant_Top.md](./Executor_Consultant_Top.md) | MBB 级咨询风格 SVG | 选择「C) 顶级咨询」 |
| **CRAP 优化师** | [Optimizer_CRAP.md](./Optimizer_CRAP.md) | 视觉质量优化 | 用户要求优化（可选） |

## 支持的画布格式

- **演示文稿**: PPT 16:9 (1280×720)、PPT 4:3 (1024×768)
- **社交媒体**: 小红书 (1242×1660)、朋友圈 (1080×1080)、Story (1080×1920)
- **营销物料**: 公众号头图 (900×383)、横版/竖版海报

详见 [画布格式规范](../docs/canvas_formats.md)

## 执行师选择速查

| PPT 类型 | 推荐角色 |
|----------|----------|
| 商业咨询/财务分析 | Executor_Consultant_Top |
| 工作汇报/政府报告 | Executor_Consultant |
| 招商推介/品牌宣传 | Executor_General（图文风格） |
| 培训课件/团队分享 | Executor_General |

## 相关文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](../AGENTS.md) | 完整工作流程、角色切换协议、技术约束 |
| [设计指南](../docs/design_guidelines.md) | 配色、字体、布局详细规范 |
| [工作流教程](../docs/workflow_tutorial.md) | 实战案例 |
| [快速参考](../docs/quick_reference.md) | 速查手册 |
