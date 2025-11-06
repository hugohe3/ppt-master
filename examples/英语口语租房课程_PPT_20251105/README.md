# 英语口语租房课程 - Unit 03 Renting an Apartment

**项目创建日期**：2025-11-05  
**画布格式**：PPT 16:9 (1280×720)  
**设计风格**：通用灵活风格  
**总页数**：13 页

---

## 📚 课程概述

本课程是基于美式英语实用口语教材制作的 PPT 学习材料，聚焦于"租赁公寓"主题。内容涵盖租房相关的核心词汇、必备表达、情景对话以及俚语文化，适合中级水平的英语学习者，尤其是有留学或移民美国计划的人群。

---

## 🎯 学习目标

1. **掌握 40+ 租房核心词汇**：分类术语、公寓条件、房屋构成、住宅类型
2. **熟练运用租房必备表达**：问租金、问租期、问押金、问规定
3. **理解并应用真实情景对话**：租房咨询、找室友的实际交流
4. **了解美国租房相关俚语与文化**：pad, crib, hood 等街头口语

---

## 📄 内容结构

### Slide 01 - 封面
- 课程标题：Unit 03 Renting an Apartment
- 中文副标题：租赁公寓 - 美式英语实用口语

### Slide 02 - 课程介绍
- 课程背景说明
- 学习目标（4项）
- 内容模块预览

### Slide 03 - 词汇模块：租房与找室友基础术语
- classified ads, real estate, landlord, tenant, lease, apartment for rent, roommate wanted, apartment hunting

### Slide 04 - 词汇模块：公寓的条件和环境
- one-year lease, nice view, 2B 2bath, newly remodeled, washer-dryer in unit, great amenities, fully furnished 等

### Slide 05 - 词汇模块：公寓内部构成
- foyer, den, hall, basement, ceiling, nursery, attic, breakfast nook, fireplace
- 配平面图示意

### Slide 06 - 词汇模块：房子外面
- porch, patio, balcony, roof, garden, chimney, exit, security system, parking space
- 配房屋外观示意图

### Slide 07 - 词汇模块：美国住宅类型
- house, townhouse, apartment, studio apartment, loft-style apartment, duplex, condominium

### Slide 08 - 必备表达：问租金与费用
- How much is the rent?
- Is there a security deposit?
- Are utilities included?

### Slide 09 - 必备表达：问租期与规定
- How long is the lease?
- Are pets allowed?
- 更多常用问题

### Slide 10 - 情景对话 1：租房咨询
- 完整对话（7轮）：电话咨询公寓出租情况
- 英文原文 + 中文翻译

### Slide 11 - 情景对话 2：找室友
- 完整对话（6轮）：询问室友招募情况
- 英文原文 + 中文翻译

### Slide 12 - 俚语学习：Street Talk
- pad（房间，公寓）
- a place to crash（生活的地方）
- crib（家，房子）
- hood（邻里，社区）
- slumlord（恶劣房东）⚠️

### Slide 13 - 课程总结
- 核心知识回顾（4项）
- 实用建议 Tips（3条）
- 延伸学习资源
- 鼓励语：Practice makes perfect!

---

## 🎨 设计特色

### 色彩方案
- **主色**：森林绿 #2E7D32（成长与学习）
- **辅助色**：天蓝 #1976D2、活力橙 #F57C00、优雅紫 #5E35B1
- **中性色**：深灰 #424242、次要文字 #757575
- **背景色**：浅灰 #F5F5F5、纯白卡片 #FFFFFF

### 布局特点
- **卡片式设计**：信息模块化，层次清晰
- **双语对照**：英文术语 + 中文翻译同时呈现
- **视觉辅助**：房屋平面图、外观示意图、对话气泡
- **CRAP 设计原则**：对比、重复、对齐、亲密性

---

## 🖥️ 预览方式

### 方式一：使用内置预览页面（推荐）
```bash
# 在浏览器中直接打开
open preview.html
```

预览页面功能：
- 📱 响应式网格布局
- 🔍 点击任意幻灯片查看大图
- ⌨️ 键盘导航（←/→ 切换，Esc 退出）
- 📊 幻灯片计数器

### 方式二：使用 HTTP 服务器
```bash
# 在项目根目录运行
python3 -m http.server 8000

# 浏览器访问
http://localhost:8000/preview.html
```

### 方式三：查看单个 SVG
```bash
# 直接在浏览器打开任意 SVG 文件
open svg_output/slide_01_cover.svg
```

---

## 📂 文件结构

```
英语口语租房课程_PPT_20251105/
├── README.md                     # 本文件
├── 设计规范与内容大纲.md          # 策略师输出的设计规范
├── preview.html                  # 预览页面
└── svg_output/                   # SVG 幻灯片输出
    ├── slide_01_cover.svg
    ├── slide_02_introduction.svg
    ├── slide_03_vocab_basics.svg
    ├── slide_04_vocab_conditions.svg
    ├── slide_05_vocab_interior.svg
    ├── slide_06_vocab_exterior.svg
    ├── slide_07_vocab_housing_types.svg
    ├── slide_08_expressions_rent.svg
    ├── slide_09_expressions_rules.svg
    ├── slide_10_dialogue1_rent.svg
    ├── slide_11_dialogue2_roommate.svg
    ├── slide_12_slang.svg
    └── slide_13_summary.svg
```

---

## 🔧 技术规范

- **SVG 标准**：符合 W3C SVG 1.1 规范
- **viewBox**：0 0 1280 720
- **文本换行**：使用 `<tspan>` 手动换行（禁止 `<foreignObject>`）
- **字体栈**：系统 UI 字体（跨平台兼容）
- **阴影效果**：使用 `<filter>` + `<feGaussianBlur>`
- **渐变**：使用 `<linearGradient>` 实现

---

## 💡 使用建议

1. **个人学习**：按顺序浏览幻灯片，重点记忆词汇与表达
2. **课堂教学**：投影演示，结合情景对话进行角色扮演
3. **复习巩固**：使用预览页面随机抽查词汇
4. **实战应用**：访问 Zillow、Apartments.com 等网站查看真实租房广告

---

## 📝 延伸学习资源

- **租房网站**：[Zillow](https://www.zillow.com)、[Apartments.com](https://www.apartments.com)
- **美剧推荐**：Friends（老友记）、How I Met Your Mother（老爸老妈浪漫史）中有大量租房场景
- **YouTube 频道**：搜索 "apartment hunting tips" 观看真实租房 vlog

---

## 🎓 制作信息

- **策略师**：AI Assistant（策略规划与内容大纲）
- **执行者**：AI Assistant（通用灵活风格 SVG 生成）
- **制作日期**：2025年11月5日
- **制作框架**：PPT Master - AI 驱动的多格式 SVG 内容生成系统

---

## 📌 注意事项

1. **浏览器兼容性**：推荐使用 Chrome、Firefox、Safari 最新版本
2. **文字渲染**：部分浏览器可能对中文字体渲染略有差异，属正常现象
3. **移动端查看**：预览页面已适配移动设备，但建议使用电脑查看以获得最佳体验

---

**学习愉快！Practice makes perfect! 🎉**

