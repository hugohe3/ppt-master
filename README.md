# PPT Master - AI 驱动的 SVG 演示文稿生成系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hugohe3/ppt-master.svg)](https://github.com/hugohe3/ppt-master/stargazers)

一个基于 AI 的智能演示文稿生成系统，通过四个专业角色协作，将源文档转化为高质量的 SVG 幻灯片。

## 📋 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [四大角色](#四大角色)
- [快速开始](#快速开始)
- [工作流程](#工作流程)
- [设计风格](#设计风格)
- [技术规范](#技术规范)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 项目简介

PPT Master 是一个创新的 AI 辅助演示文稿制作系统，通过四个专业 AI 角色的协作，实现从内容策划到视觉优化的完整工作流。系统支持生成符合顶尖咨询公司（如麦肯锡、波士顿咨询）标准的商业演示文稿。

## 核心特性

✨ **智能内容解构** - 自动分析源文档并重组为清晰的页面序列
🎨 **双重设计风格** - 支持"通用灵活风格"和"高端咨询风格"
📊 **数据可视化** - 内置图表、时间轴、KPI 展示等专业组件
🎯 **CRAP 设计原则** - 遵循对比、重复、对齐、亲密性四大核心原则
🖼️ **纯 SVG 输出** - 16:9 比例的高质量矢量图形，无需第三方依赖
🔄 **迭代优化** - 支持逐页生成和反馈修改

## 系统架构

```
用户输入文档
    ↓
[Strategist] 策略师 - 内容规划与设计规范
    ↓
[Executor_General / Executor_Consultant] 执行师 - SVG代码生成
    ↓
[Optimizer_CRAP] 优化师 - 视觉优化
    ↓
最终SVG演示文稿
```

## 四大角色

### 1️⃣ Strategist (策略师)

**职责**: 内容分析与设计规划**输出**: 《演示文稿设计规范与内容大纲》

- 智能解构源文档
- 确定视觉主题和色彩方案
- 规划页面序列和布局
- 制定排版体系

📄 [查看完整角色定义](./roles/Strategist.md)

### 2️⃣ Executor_General (通用执行师)

**职责**: 生成通用灵活风格的 SVG 代码**输出**: 单页 SVG 代码

- 严格遵循设计规范
- 逐页生成 SVG
- 动态调整视觉平衡
- 支持迭代修改

📄 [查看完整角色定义](./roles/Executor_General.md)

### 3️⃣ Executor_Consultant (咨询风格执行师)

**职责**: 生成高端咨询风格的 SVG 代码**输出**: 商业级演示文稿页面

- 采用顶尖咨询公司设计风格
- 数据驱动的可视化
- KPI 和图表优化
- 专业配色方案

📄 [查看完整角色定义](./roles/Executor_Consultant.md)

### 4️⃣ Optimizer_CRAP (CRAP 优化师)

**职责**: 基于 CRAP 原则优化设计**输出**: 优化后的 SVG 代码

- **对齐 (Alignment)**: 创建视觉连接线
- **对比 (Contrast)**: 突出视觉层次
- **重复 (Repetition)**: 统一视觉风格
- **亲密性 (Proximity)**: 组织信息关系

📄 [查看完整角色定义](./roles/Optimizer_CRAP.md)

## 快速开始

### 基本工作流

1. **准备源文档**准备好你的内容文档（文本、数据、要点等）
2. **选择风格**与 Strategist 确认：A) 通用灵活风格 或 B) 高端咨询风格
3. **获取规划**Strategist 生成《设计规范与内容大纲》并确认
4. **逐页生成**使用相应的 Executor 角色生成每一页 SVG
5. **优化润色**（可选）使用 Optimizer_CRAP 进行 CRAP 原则优化
6. **导出使用**
   将 SVG 文件导出或嵌入到你的演示环境中

### 示例对话流程

```
用户: 我有一份市场分析报告需要制作成演示文稿
Strategist: 请问本次设计我们采用 A) 通用灵活风格 还是 B) 高端咨询风格？
用户: B) 高端咨询风格
Strategist: [生成完整的设计规范与内容大纲...]
用户: 请生成第1页
Executor_Consultant: [生成第1页SVG代码...]
用户: 请优化这一页的视觉效果
Optimizer_CRAP: [分析并输出优化后的SVG代码...]
```

💡 **提示**: 查看 `examples/sample_output/` 目录下的实际案例，了解完整的项目实施过程和最终效果。

## 设计风格

### 通用灵活风格

- 适用场景：一般商业演示、教育培训、团队汇报
- 设计特点：灵活布局、色彩丰富、易于定制
- 内容结构：清晰的逻辑层次和视觉引导

### 高端咨询风格

- 适用场景：战略报告、董事会演示、客户提案
- 设计特点：简洁专业、数据驱动、强调洞察
- 参考标准：麦肯锡、BCG 等顶尖咨询公司
- 典型元素：矩阵图、时间轴、KPI 仪表盘、数据图表

## 技术规范

### SVG 参数

- **画布尺寸**: 1280×720 (16:9)
- **ViewBox**: `0 0 1280 720`
- **背景**: 使用 `<rect>`元素定义
- **文本**: 禁用 `<foreignObject>`，使用 `<tspan>`手动换行
- **字体**: 优先使用系统 UI 字体栈

### 布局规范

#### 通用灵活风格

- **边距**: 40-60px
- **卡片高度** (强制规则):
  - 单行内容: 530-600px
  - 两行内容: 265-295px (每行)
- **间距**: 20-30px

#### 高端咨询风格

- 遵循咨询行业最佳实践
- 强调留白和视觉呼吸感
- 数据图表占据主要视觉区域

### 配色方案

#### 咨询风格主导色

- 德勤蓝: `#0076A8`
- 麦肯锡蓝: `#005587`
- BCG 深蓝: `#003F6C`

#### 通用配色原则

- 提供主导色、辅助色和基础色调
- 支持亮色/深色主题
- 使用 HEX 颜色值

## 项目结构

```
ppt-master/
├── README.md                   # 项目说明文档
├── LICENSE                     # 许可证文件
├── .gitignore                 # Git忽略规则
├── CONTRIBUTING.md            # 贡献指南
├── CHANGELOG.md               # 更新日志
├── roles/                     # AI 角色定义
│   ├── README.md              # 角色概览
│   ├── Strategist.md          # 策略师角色定义
│   ├── Executor_General.md    # 通用执行师角色定义
│   ├── Executor_Consultant.md # 咨询执行师角色定义
│   └── Optimizer_CRAP.md      # CRAP优化师角色定义
├── examples/                  # 示例文件夹
│   ├── sample_input/          # 输入文档示例
│   │   └── 中国历代政治得失.md  # 中国政治史源文档
│   └── sample_output/         # 生成的SVG示例
│       ├── README.md          # 示例说明
│       ├── 演示文稿设计规范与内容大纲.md  # 完整设计规范
│       ├── yh_slide_01_cover.svg         # 封面页
│       ├── yh_slide_02_methodology.svg   # 方法论页
│       ├── yh_slide_03_han.svg           # 汉朝分析
│       ├── yh_slide_04_tang.svg          # 唐朝分析
│       ├── yh_slide_05_song.svg          # 宋朝分析
│       ├── yh_slide_06_ming.svg          # 明朝分析
│       ├── yh_slide_07_qing.svg          # 清朝分析
│       ├── yh_slide_08_trends.svg        # 趋势总结
│       └── yh_slide_09_insights.svg      # 洞察结论
├── docs/                      # 额外文档
│   ├── design_guidelines.md   # 详细设计指南
│   └── workflow_tutorial.md   # 工作流教程
└── projects/                  # 用户项目工作区（用于存放你的项目）
```

## 最佳实践

### 内容准备

1. **清晰的逻辑结构** - 确保源文档有明确的章节和要点
2. **数据准备充分** - 提供具体的数字和数据支持
3. **视觉元素建议** - 预先考虑图表类型和布局需求

### 设计过程

1. **充分沟通** - 与 Strategist 确认所有设计参数
2. **逐页验证** - 每生成一页都要检查效果
3. **适时优化** - 关键页面使用 Optimizer_CRAP 提升质量
4. **保持一致** - 确保全套幻灯片风格统一

### 输出管理

1. **文件命名** - 使用清晰的命名规则（如：`slide_01_cover.svg`）
2. **版本控制** - 保存每次迭代的版本
3. **格式转换** - 根据需要转换为 PNG 或 PDF
4. **项目组织** - 将每个演示项目放在 `projects/` 目录下，包含设计规范和 SVG 输出

## 示例案例

本仓库包含了一个完整的实际应用案例，展示从输入到输出的完整工作流程：

### 🏛️ 中国历代政治得失演示文稿

一个历史主题的专业演示文稿项目，展示了系统的完整能力。

- **源文档**: `examples/sample_input/中国历代政治得失.md`
- **设计规范**: `examples/sample_output/演示文稿设计规范与内容大纲.md`
- **生成页面**: 9 页完整的 SVG 演示文稿
- **风格**: 高端咨询风格
- **特点**:
  - 时间轴展示历史脉络
  - 数据可视化呈现关键信息
  - 专业的麦肯锡蓝配色方案
  - CRAP 设计原则优化

### 📂 查看示例

所有示例文件都在 `examples/` 目录下：

1. **输入文档**: `examples/sample_input/` - 查看如何准备源文档
2. **输出结果**: `examples/sample_output/` - 查看生成的 SVG 文件和设计规范

### � 开始你的项目

参考示例结构，在 `projects/` 目录下创建你自己的演示文稿项目：

```
projects/
└── your_project_name/
    ├── source_document.md          # 你的源文档
    ├── design_specification.md     # Strategist生成的设计规范
    └── svg_output/                 # 生成的SVG文件
        ├── slide_01.svg
        ├── slide_02.svg
        └── ...
```

## 常见问题

<details>
<summary><b>Q: 生成的SVG文件如何使用？</b></summary>

A: SVG 文件可以：

- 直接在浏览器中打开查看
- 嵌入到 HTML 页面中
- 使用设计工具（如 Figma、Adobe Illustrator）编辑
- 转换为 PNG/PDF 格式用于传统演示软件

</details>

<details>
<summary><b>Q: 两种执行师有什么区别？</b></summary>

A:

- **Executor_General**: 适用于通用场景，提供灵活的布局和丰富的视觉选择
- **Executor_Consultant**: 专注于商业咨询风格，强调数据可视化和专业性

</details>

<details>
<summary><b>Q: 必须使用Optimizer_CRAP吗？</b></summary>

A: 不是必须的。如果 Executor 生成的 SVG 已经满足需求，可以跳过优化步骤。Optimizer 主要用于进一步提升关键页面的视觉质量。

</details>

<details>
<summary><b>Q: 可以自定义配色方案吗？</b></summary>

A: 可以！在与 Strategist 沟通时，明确提出你的品牌色或偏好配色，Strategist 会据此调整设计规范。

</details>

## 贡献指南

我们欢迎各种形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献方向

- 🎨 新增设计风格模板
- 📊 扩展图表类型和可视化组件
- 📝 完善文档和教程
- 🐛 报告 bug 和问题
- 💡 提出新功能建议
- 🌍 多语言支持
- 📁 分享你的项目案例到 `examples/` 目录

## 路线图

- [x] 建立完整的角色体系和工作流
- [x] 实现通用和咨询两种设计风格
- [x] 完成多个实际项目案例
- [ ] 添加更多行业领域的示例演示文稿
- [ ] 开发交互式配置工具
- [ ] 扩展图表库和可视化组件
- [ ] 支持动画效果和交互性
- [ ] Web 界面开发
- [ ] API 接口设计
- [ ] 自动化批量生成工具

## 致谢

- 设计灵感来源于麦肯锡、波士顿咨询等顶尖咨询公司
- CRAP 设计原则由 Robin Williams 提出
- 图标资源来自 [Lucide Icons](https://lucide.dev/)

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- GitHub: [@hugohe3](https://github.com/hugohe3)
- 项目链接: [https://github.com/hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

Made with ❤️ by Hugo He
