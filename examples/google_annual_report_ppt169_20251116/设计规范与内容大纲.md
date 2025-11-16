# Google 2025 年度工作汇报 - 设计规范与内容大纲

## 项目元信息

- **项目名称**：Google 2025 Annual Work Report
- **画布格式**：PPT 16:9 (1280×720)
- **设计风格**：高端咨询风格
- **总页数**：10 页
- **主题色系**：Google 品牌色 + 专业蓝色系

---

## 设计规范（高端咨询风格）

### 视觉风格定位

- **专业性**：体现 Google 技术专业度
- **数据驱动**：强化量化指标与图表可视化
- **简洁克制**：充足留白，突出核心信息
- **品牌一致性**：融入 Google 设计语言

### 色彩规范

**主色系（Google 品牌色）**：

- Google Blue：`#4285F4`（主要标题、关键数据）
- Google Red：`#EA4335`（重要强调）
- Google Yellow：`#FBBC04`（辅助图标）
- Google Green：`#34A853`（成功指标）

**专业配色**：

- 深蓝色：`#1A237E`（标题、核心文本）
- 中灰色：`#5F6368`（正文、说明文字）
- 浅灰色：`#E8EAED`（背景、分割线）
- 纯白：`#FFFFFF`（主背景）

**图表配色**：

- 数据系列 1：`#4285F4`（Google Blue）
- 数据系列 2：`#34A853`（Google Green）
- 数据系列 3：`#FBBC04`（Google Yellow）
- 数据系列 4：`#EA4335`（Google Red）

### 字体规范

**系统 UI 字体栈**：

```
font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif
```

**字号层级**：

- 页面主标题：48px，font-weight: 700
- 一级标题：36px，font-weight: 600
- 二级标题：28px，font-weight: 600
- 正文：20px，font-weight: 400
- 辅助说明：16px，font-weight: 400
- 数据标签：18px，font-weight: 500

### 布局规范

**画布尺寸**：

- viewBox: `0 0 1280 720`
- width/height: `1280px` × `720px`

**安全边距**：

- 左右边距：60px
- 上边距：50px
- 下边距：50px
- 内容安全区：1160px × 620px

**网格系统**：

- 采用 12 列网格
- 列宽：约 85px
- 间距：20px

### 信息可视化原则

**CRAP 原则应用**：

1. **对比（Contrast）**：
   - 数据与背景对比度 ≥ 4.5:1
   - 关键指标使用大字号 + 品牌色突出
2. **重复（Repetition）**：
   - 统一的标题位置与样式
   - 一致的图表风格
   - 固定的页码位置
3. **对齐（Alignment）**：
   - 所有元素遵循网格对齐
   - 文本左对齐为主
   - 图表居中或左对齐
4. **亲密性（Proximity）**：
   - 相关数据分组呈现
   - 标题与内容间距 30-40px
   - 不同模块间距 60-80px

### 图表设计规范

**通用要求**：

- 清晰的数据标签
- 简洁的图例
- 适度的网格线（浅灰色，透明度 0.3）
- 数据点突出显示

**KPI 卡片**：

- 尺寸：约 250×180px
- 圆角：8px
- 阴影：subtle，传递层次感
- 内容：大号数字 + 小号描述

**柱状图/折线图**：

- 轴线颜色：`#E8EAED`
- 标签字号：16px
- 数据点标注清晰

---

## 内容大纲

### Slide 01：封面

**布局**：居中式

**内容要素**：

- 主标题：2025 Annual Work Report
- 副标题：Google Cloud Platform - Infrastructure Optimization
- 姓名：Ming Zhang
- 职位：Senior Software Engineer (L5)
- 日期：December 2025
- 背景：简洁的渐变或纯色，融入 Google 品牌元素

---

### Slide 02：年度概览

**布局**：上标题 + 双栏内容

**内容要素**：

- 标题：2025 Year in Review
- 左栏：整体成就描述（3-4 行简洁文字）
- 右栏：5 个关键数字 KPI 卡片
  - 3 个核心项目
  - 42% 成本降低
  - 99.99% 系统可用性
  - 15+ 技术分享
  - 8 位工程师指导

**视觉化**：KPI 卡片采用 Google 品牌色，带图标装饰

---

### Slide 03：核心项目成果总览

**布局**：标题 + 三栏卡片

**内容要素**：

- 标题：3 Major Projects Delivered
- 三个项目卡片并列：
  1. Smart Resource Scheduler
     - 图标：⚙️ 齿轮
     - 核心指标：资源利用率 +100%
     - 成本节省：$28M
  2. Cross-Region Sync Optimization
     - 图标：🌐 网络
     - 核心指标：延迟 -82%
     - 带宽减少：-63%
  3. Auto-Recovery System
     - 图标：🔄 恢复
     - 核心指标：MTTR -82%
     - 可用性：99.99%

**视觉化**：统一卡片设计，顶部色块区分项目

---

### Slide 04：项目一详解 - 智能资源调度系统

**布局**：左右分栏

**内容要素**：

- 标题：Smart Resource Scheduler
- 左栏（40%）：
  - 项目背景（2-3 行）
  - 技术方案关键点（3-4 个要点）
  - 技术栈：Go + Kubernetes + TensorFlow
- 右栏（60%）：
  - 关键成果数据可视化
  - 柱状图：资源利用率对比（Before 38% vs After 76%）
  - 4 个 KPI 数字：
    - 成本节省：$28M
    - 延迟降低：-35%
    - 覆盖区域：120+
    - 处理能力：50K+ 决策/秒

**视觉化**：对比图表 + 数据卡片

---

### Slide 05：项目二 & 三亮点

**布局**：上下分区

**内容要素**：

- 标题：More Technical Achievements

**上半部分 - 跨区域同步优化**：

- 小标题：Cross-Region Sync Optimization
- 关键成果：
  - 折线图：同步延迟趋势（2.3s → 0.4s）
  - 数据标注：-82% 延迟，-63% 带宽
  - 亮点：专利申请 + SIGCOMM 展示

**下半部分 - 自动化故障恢复**：

- 小标题：Auto-Recovery System
- 关键成果：
  - 对比条形图：MTTR（45min → 8min）
  - 数据标注：自动修复成功率 94%
  - 影响：On-call 负担 -70%

---

### Slide 06：技术成长与创新

**布局**：中心标题 + 四象限

**内容要素**：

- 标题：Technical Growth & Innovation

**四个象限**：

1. **技术深度**（左上）：

   - Cloud Native Architecture
   - Performance Optimization
   - ML in Production
   - Distributed Systems

2. **技术创新**（右上）：

   - 1 专利申请
   - 3 技术博客
   - 2 开源贡献

3. **认证**（左下）：

   - GCP Professional Architect
   - Kubernetes CKAD

4. **影响力**（右下）：
   - 技术分享 15+
   - 文档撰写 17 份
   - Stack Overflow 50+ 回答

**视觉化**：图标 + 数字 + 简短描述

---

### Slide 07：团队协作与影响力

**布局**：标题 + 内容分区

**内容要素**：

- 标题：Team Collaboration & Impact

**内容分区**：

1. **跨团队协作**（顶部横条）：

   - 5 个团队协作图示
   - 网络图展示连接关系

2. **Mentoring**（中部左侧）：

   - 8 位工程师指导
   - 2 位成功晋升
   - 进度条可视化

3. **知识分享**（中部右侧）：

   - 饼图：分享类型占比
     - Tech Talk: 8
     - I/O Sessions: 2
     - Onboarding: 5

4. **社区贡献**（底部）：
   - Stack Overflow、GitHub、GDE 候选人

**视觉化**：网络图 + 进度条 + 饼图

---

### Slide 08：影响力数据看板

**布局**：Dashboard 风格

**内容要素**：

- 标题：Impact Dashboard

**6 个数据卡片（2×3 布局）**：

1. 成本节省：$28M+
2. 性能提升：76% 资源利用率
3. 系统可靠性：99.99% 可用性
4. 知识传播：15+ 技术分享
5. 团队培养：8 位工程师
6. 社区影响：50+ Stack Overflow

**视觉化**：大号数字 + 趋势图标（↑ 向上箭头）

---

### Slide 09：2026 年规划

**布局**：三栏并列

**内容要素**：

- 标题：Looking Forward to 2026

**三栏内容**：

1. **技术方向**：

   - 🤖 AI/ML 深化
   - 🌐 Edge Computing
   - 📊 可观测性升级

2. **职业发展**：

   - 🎯 晋升 Staff Engineer (L6)
   - 📈 扩大技术影响力
   - 🌟 成为领域专家

3. **团队贡献**：
   - 🏆 技术卓越文化
   - 💡 推动创新
   - 🤝 增强协作

**视觉化**：图标 + 关键词 + 简短描述

---

### Slide 10：致谢

**布局**：居中式

**内容要素**：

- 主标题：Thank You
- 感谢语：
  - 感谢 Manager Sarah 的指导
  - 感谢 Tech Lead Kevin 的引领
  - 感谢团队所有成员的支持
- 结尾语：Let's make 2026 even better!
- 装饰元素：Google 品牌色点缀

**视觉化**：简洁、温暖、专业

---

## 技术实施要点

### SVG 生成规则

- ✅ 所有文本使用 `<text>` + `<tspan>` 手动换行
- ❌ 禁止使用 `<foreignObject>`
- ✅ 背景使用 `<rect>` 元素
- ✅ viewBox 与 width/height 保持一致：`0 0 1280 720`

### 图表实施

- 参考 `templates/charts/` 模板库
- KPI 卡片参考 `kpi_cards.svg`
- 柱状图参考 `bar_chart.svg`
- 折线图参考 `line_chart.svg`
- 饼图参考 `donut_chart.svg`

### 文件命名

- slide_01_cover.svg
- slide_02_year_overview.svg
- slide_03_projects_summary.svg
- slide_04_project_smart_scheduler.svg
- slide_05_projects_other.svg
- slide_06_technical_growth.svg
- slide_07_team_collaboration.svg
- slide_08_impact_dashboard.svg
- slide_09_future_plans.svg
- slide_10_thanks.svg

---

## 质量检查清单

- [ ] 所有页面 viewBox 为 `0 0 1280 720`
- [ ] 色彩符合 Google 品牌规范
- [ ] 字体使用系统 UI 字体栈
- [ ] 无 `<foreignObject>` 元素
- [ ] CRAP 原则体现到位
- [ ] 数据准确性校验
- [ ] 视觉层级清晰
- [ ] 留白适度专业

---

_本规范由 Strategist 角色编制，遵循 PPT Master 高端咨询风格标准_
