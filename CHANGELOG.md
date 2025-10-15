# 更新日志

本文档记录了项目的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 更改

- **Strategist 角色增强** - Strategist 现在会在初始沟通时主动提供专业建议
  - 页数范围建议：基于源文档内容量和复杂度分析
  - 受众场景判断：基于文档特征预判目标受众和使用场合
  - 风格推荐：根据内容性质和场景推荐最适合的设计风格并说明理由
  - 从"被动提问者"升级为"主动顾问"角色
  - 更新了所有相关文档以反映此变更（README.md, workflow_tutorial.md, CLAUDE.md, roles/Strategist.md, 等）

- **文档结构对齐仓库现状**
  - README: 用示例索引替换过期的 sample_output 引用；补充预览方法与示例清单
  - AGENTS.md/CLAUDE.md/GEMINI.md/CONTRIBUTING.md: 统一为按项目目录组织的 examples 结构
  - docs: 修复工作流教程角色定义链接、更新临时指南（微信公众号配图模版）与快速参考示例链接
  - 新增 `examples/README.md` 与 `projects/README.md` 作为索引与指引

### 计划中

- 交互式配置工具
- Web 界面开发
- 更多图表类型支持
- 动画效果系统
- API 接口设计

## [1.0.0] - 2024-10-11

### 新增

- 初始版本发布
- 四个核心 AI 角色系统
  - Strategist（策略师）- 内容分析与设计规划
  - Executor_General（通用执行师）- 生成通用灵活风格 SVG
  - Executor_Consultant（咨询执行师）- 生成高端咨询风格 SVG
  - Optimizer_CRAP（CRAP 优化师）- 基于 CRAP 原则优化设计
- 双重设计风格支持
  - 通用灵活风格 - 适用于一般商业演示、教育培训
  - 高端咨询风格 - 参考麦肯锡、BCG 等顶尖咨询公司
- 完整的角色定义文档（roles/）
- SVG 生成技术规范
- CRAP 设计原则实现（对比、重复、对齐、亲密性）
- 项目结构组织（roles/、examples/、docs/、projects/）
- MIT 许可证
- Git 忽略规则配置

### 功能特性

- **Strategist 核心能力**：
  - 初始沟通与范围确认（页数、受众、风格）
  - 智能内容解构与重组
  - 完整色彩方案规划（主导色、辅助色、基础色调）
  - 页面序列与布局建议
  - 排版体系定义
  - 根据风格生成不同详细程度的规范（通用完整版 vs 咨询精简版）
- **Executor 核心能力**：
  - 严格遵循设计规范
  - 16:9 比例 SVG 输出（1280×720）
  - 禁用 foreignObject，使用 tspan 手动换行
  - 强制卡片高度规则（单行 530-600px，双行 265-295px）
  - 动态调整视觉平衡
  - 逐页生成机制
  - 迭代修改支持
- **Optimizer 核心能力**：
  - 对齐(Alignment)分析与优化
  - 对比(Contrast)增强
  - 重复(Repetition)统一化
  - 亲密性(Proximity)优化
  - 生成 yh\_前缀的优化文件
- **数据可视化**：
  - KPI 仪表盘
  - 时间轴展示
  - 矩阵图/四象限
  - 表格结构化展示
  - 图标集成（Lucide Icons / Emoji）
- **技术规范**：
  - 画布尺寸 1280×720，viewBox="0 0 1280 720"
  - 底层<rect>定义背景色
  - 系统 UI 字体栈
  - 精确的绝对坐标定位
  - 清晰的代码结构与注释

### 示例项目

- **中国历代政治得失演示文稿**（完整案例）
  - 源文档：`examples/sample_input/中国历代政治得失.md`
  - 设计规范：`examples/sample_output/演示文稿设计规范与内容大纲.md`
  - 9 页高质量 SVG 输出（封面、方法论、汉唐宋明清、趋势、洞察）
  - 采用高端咨询风格
  - 展示历史主题的专业数据可视化
  - 深金色配色方案（#B8860B）
  - 朝代专属色标识系统
  - 时间轴、表格、矩阵等多种布局

### 文档

- 完整的 README.md
- 四个角色定义文档（roles/）
- 角色概览文档（roles/README.md）
- 设计指南（docs/design_guidelines.md）
- 工作流教程（docs/workflow_tutorial.md）
- 贡献指南（CONTRIBUTING.md）
- 许可证文件（LICENSE）
- 更新日志（CHANGELOG.md）

## 版本说明

### 版本号格式：主版本号.次版本号.修订号

- **主版本号**：不兼容的 API 更改
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修正

### 更改类型

- **新增** - 新功能
- **更改** - 现有功能的变更
- **弃用** - 即将移除的功能
- **移除** - 已移除的功能
- **修复** - Bug 修复
- **安全** - 安全相关的更改

---

[未发布]: https://github.com/hugohe3/ppt-master/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/hugohe3/ppt-master/releases/tag/v1.0.0
