# MIS 第12章《强化决策》PPT 项目

## 项目概述

本项目为管理信息系统（MIS）课程第12章"强化决策 (Enhancing Decision Making)"的演示文稿设计与制作。

## 项目信息

- **创建日期**：2025-11-06
- **画布格式**：PPT 16:9（1280×720）
- **设计风格**：高端咨询风格
- **页数**：16页
- **目标受众**：MIS 课程学生、企业管理培训学员

## 内容结构

### 章节导航

1. **12-1** 🤔 决策类型与决策过程
2. **12-2** 👨‍💼 信息系统对管理者的支持
3. **12-3** 📊 商业智能与业务分析
4. **12-4** 👥 不同决策群体的 BI 使用
5. **12-5** 💼 MIS 助力职业发展

### 页面清单

1. 封面
2. 章节导航
3. 决策的商业价值
4. 决策的三种类型
5. 决策过程四阶段
6. 管理者角色
7. 决策制约因素
8. 高速自动化决策
9. 商业智能环境
10. BI 六大分析能力
11. 关键分析技术
12. 决策群体与用户分布
13. MIS/DSS/ESS 系统对比
14. 平衡计分卡方法
15. MIS 与职业发展
16. 结束页

## 设计特色

### 配色方案
- **主色**：McKinsey Blue (#005587)
- **辅助色**：Deloitte Blue (#0076A8)
- **强调色**：橙色 (#E67E22)
- **背景**：纯白 (#FFFFFF)

### 设计原则
- 专业简洁的咨询风格
- 强调信息可视化（流程图、矩阵、层级图）
- 留白充足，视觉呼吸感强
- 文字密度控制在每页 100 字以内

### 核心可视化元素
- 决策类型分类矩阵
- 决策过程流程图
- 商业智能环境架构图
- 平衡计分卡四象限图
- 系统对比表格

## 文件结构

```
mis_chapter12_ppt169_20251106/
├── README.md                      # 本文件
├── 设计规范与内容大纲.md           # 详细设计规范
└── svg_output/                    # SVG 输出目录
    ├── slide_01_cover.svg
    ├── slide_02_navigation.svg
    ├── slide_03_decision_value.svg
    ├── slide_04_decision_types.svg
    ├── slide_05_decision_process.svg
    ├── slide_06_manager_roles.svg
    ├── slide_07_constraints.svg
    ├── slide_08_automation.svg
    ├── slide_09_bi_environment.svg
    ├── slide_10_bi_capabilities.svg
    ├── slide_11_analytics.svg
    ├── slide_12_user_groups.svg
    ├── slide_13_systems_compare.svg
    ├── slide_14_balanced_scorecard.svg
    ├── slide_15_career.svg
    └── slide_16_thankyou.svg
```

## 预览方式

### 方式一：本地 HTTP 服务器（推荐）

```bash
python3 -m http.server --directory svg_output 8000
```

然后在浏览器访问 `http://localhost:8000`

### 方式二：直接打开

在浏览器中直接打开 `svg_output` 目录下的任意 SVG 文件

## 技术规范

- **SVG 规范**：禁止 `<foreignObject>`，使用 `<tspan>` 手动换行
- **viewBox**：`0 0 1280 720`
- **字体**：Microsoft YaHei / Segoe UI
- **边距**：60px 安全边距

## 使用场景

- 课堂教学演示
- 企业管理培训
- 在线课程配套材料
- 学术研讨会分享

## 相关文档

- [设计规范与内容大纲](./设计规范与内容大纲.md)
- [项目仓库主文档](../../README.md)
- [画布格式规范](../../docs/canvas_formats.md)
- [设计指南](../../docs/design_guidelines.md)

---

**项目状态**：✅ 设计规范完成 | ⏳ SVG 生成中  
**更新日期**：2025-11-06

