# PPT Master 示例项目索引

> 本文件由 `tools/generate_examples_index.py` 自动生成

> 最后更新: 2025-12-01 22:17:53

## 📊 概览

- **项目总数**: 24 个
- **画布格式**: 2 种
- **SVG 文件**: 288 个

### 格式分布

- **PPT 16:9**: 18 个项目
- **微信公众号头图**: 6 个项目

## 🆕 最近更新

- **ppt169_代码风格_git_behind_scenes** (PPT 16:9) - 未知日期
- **ppt169_公司风格_汽车认证五年战略规划** (PPT 16:9) - 未知日期
- **ppt169_咨询风_汽车认证五年战略规划** (PPT 16:9) - 未知日期
- **ppt169_常规风_MIS企业应用** (PPT 16:9) - 未知日期
- **ppt169_常规风_attachment_theory** (PPT 16:9) - 未知日期

## 📁 项目列表


### PPT 16:9 (1280×720)

- **[ppt169_代码风格_git_behind_scenes](./ppt169_代码风格_git_behind_scenes)** - 未知日期 - 8 页
- **[ppt169_公司风格_汽车认证五年战略规划](./ppt169_公司风格_汽车认证五年战略规划)** - 未知日期 - 14 页
- **[ppt169_咨询风_汽车认证五年战略规划](./ppt169_咨询风_汽车认证五年战略规划)** - 未知日期 - 20 页
- **[ppt169_常规风_MIS企业应用](./ppt169_常规风_MIS企业应用)** - 未知日期 - 12 页
- **[ppt169_常规风_attachment_theory](./ppt169_常规风_attachment_theory)** - 未知日期 - 20 页
- **[ppt169_常规风_医疗器械注册调研报告](./ppt169_常规风_医疗器械注册调研报告)** - 未知日期 - 9 页
- **[ppt169_常规风_恒通银行客户经理积极性管理](./ppt169_常规风_恒通银行客户经理积极性管理)** - 未知日期 - 18 页
- **[ppt169_常规风_政府投资项目申报与管理流程](./ppt169_常规风_政府投资项目申报与管理流程)** - 未知日期 - 20 页
- **[ppt169_常规风_洪九果品案例分析](./ppt169_常规风_洪九果品案例分析)** - 未知日期 - 20 页
- **[ppt169_常规风_科技型软件企业资质知识产权规划](./ppt169_常规风_科技型软件企业资质知识产权规划)** - 未知日期 - 11 页
- **[ppt169_数据型_某县充电桩项目经济评价](./ppt169_数据型_某县充电桩项目经济评价)** - 未知日期 - 12 页
- **[ppt169_数据型_甘孜经济分析](./ppt169_数据型_甘孜经济分析)** - 未知日期 - 6 页
- **[ppt169_论文解读_context_engineering](./ppt169_论文解读_context_engineering)** - 未知日期 - 22 页
- **[ppt169_谷歌风格_gemini_marketing_guide](./ppt169_谷歌风格_gemini_marketing_guide)** - 未知日期 - 10 页
- **[ppt169_谷歌风格_google_annual_report](./ppt169_谷歌风格_google_annual_report)** - 未知日期 - 10 页
- **[ppt169_预留图片图标位置_阿森纳足球俱乐部](./ppt169_预留图片图标位置_阿森纳足球俱乐部)** - 未知日期 - 15 页
- **[ppt169_麦肯锡风格_kimsoong_customer_loyalty](./ppt169_麦肯锡风格_kimsoong_customer_loyalty)** - 未知日期 - 8 页
- **[ppt169_代码风格_debug六步法](./ppt169_代码风格_debug六步法_ppt169_20251128)** - 2025-11-28 - 10 页

### 微信公众号头图 (900×383)

- **[wechat_写给大家看的设计书](./wechat_写给大家看的设计书)** - 未知日期 - 9 页
- **[wechat_常规风_vscode_git](./wechat_常规风_vscode_git)** - 未知日期 - 8 页
- **[wechat_手绘风格_学习方法伪勤奋陷阱](./wechat_手绘风格_学习方法伪勤奋陷阱)** - 未知日期 - 5 页
- **[wechat_科技风_AI代理](./wechat_科技风_AI代理)** - 未知日期 - 6 页
- **[wechat_科技风_霍夫斯泰德文化维度](./wechat_科技风_霍夫斯泰德文化维度)** - 未知日期 - 8 页
- **[wechat_科技风_驱动 IT 基础设施发展的 5 大技术定律](./wechat_科技风_驱动 IT 基础设施发展的 5 大技术定律)** - 未知日期 - 7 页

## 📖 使用说明

### 预览项目

每个项目都包含以下文件：

- `README.md` - 项目说明文档
- `设计规范与内容大纲.md` - 完整设计规范
- `svg_output/` - SVG 输出文件

**方法 1: 使用 HTTP 服务器（推荐）**

```bash
python3 -m http.server --directory examples/<project_name>/svg_output 8000
# 访问 http://localhost:8000
```

**方法 2: 直接打开 SVG**

```bash
open examples/<project_name>/svg_output/slide_01_cover.svg
```

### 创建新项目

参考现有项目结构，或使用项目管理工具：

```bash
python3 tools/project_manager.py init my_project --format ppt169
```

## 🤝 贡献示例项目

欢迎分享你的项目到 examples 目录！

### 项目要求

1. 遵循标准项目结构
2. 包含完整的 README.md 和设计规范
3. SVG 文件符合技术规范
4. 目录命名格式: `{项目名}_{格式}_{YYYYMMDD}`

### 提交流程

1. 在 `examples/` 目录下创建项目
2. 验证项目: `python3 tools/project_manager.py validate examples/<project>`
3. 更新索引: `python3 tools/generate_examples_index.py`
4. 提交 Pull Request

## 📚 相关资源

- [快速开始](../README.md)
- [工作流教程](../docs/workflow_tutorial.md)
- [设计规范](../docs/design_guidelines.md)
- [画布格式](../docs/canvas_formats.md)
- [角色定义](../roles/README.md)
- [图表模板](../templates/charts/README.md)

---

*自动生成于 2025-12-01 22:17:53 by PPT Master*