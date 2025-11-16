# AWS as LEGO 教程

## 项目信息

- **项目名称**：AWS as LEGO: Building Blocks for Cloud
- **创建日期**：2025-11-16
- **画布格式**：PPT 16:9 (1280×720)
- **设计风格**：通用灵活风格
- **总页数**：13 页

## 内容概览

这是一套基于 AWS 云服务的系统化教程演示文稿，通过「LEGO 积木」的比喻，将复杂的云服务概念可视化呈现。

### 主要章节

1. **AWS 核心概念** (第 1-3 页)
   - 封面
   - 学习路线目录
   - AWS 是什么？

2. **构建在线商店** (第 4-9 页)
   - 案例场景介绍
   - EC2 & VPC（核心服务器）
   - S3（图片存储）
   - RDS（数据库管理）
   - IAM（权限控制）
   - Route 53 & CloudWatch（域名与监控）

3. **扩展与优化** (第 10-12 页)
   - Auto Scaling & ELB（流量扩展）
   - SQS & Lambda（异步处理）
   - CloudFront & 容器化（全球加速与部署）

4. **总结与展望** (第 13 页)
   - 核心服务回顾
   - 趣味服务介绍
   - 结尾语

## 设计特色

- **视觉比喻**：使用 LEGO 积木风格的图形元素，降低技术概念的学习门槛
- **对比展示**：通过「问题-解决方案」的卡片对比，突出 AWS 服务的价值
- **流程可视化**：使用箭头、连接线展示服务间的交互关系
- **全球视角**：CloudFront 部分使用地球图标展示全球节点分布
- **配色系统**：
  - AWS 品牌橙 (#FF9900) 为主色
  - 科技蓝 (#4A90E2) 辅助
  - 成功绿 (#27AE60) 表示解决方案
  - 警告红 (#E74C3C) 表示问题

## 使用方式

### 预览幻灯片

```bash
# 方式一：在浏览器中打开预览页面（推荐）
open projects/aws_lego_tutorial_ppt169_20251116/preview.html

# 方式二：使用 HTTP 服务器
python3 -m http.server --directory projects/aws_lego_tutorial_ppt169_20251116/svg_output 8000
# 访问 http://localhost:8000

# 方式三：直接打开单个 SVG
open projects/aws_lego_tutorial_ppt169_20251116/svg_output/slide_01_cover.svg
```

### 转换为其他格式

如需转换为 PNG 或 PDF，可使用浏览器打开 SVG 后：
- **PNG**：浏览器截图或使用 Inkscape 等工具
- **PDF**：浏览器打印功能 → 保存为 PDF

## 技术规范

- **SVG 版本**：符合 W3C SVG 1.1 标准
- **文本处理**：使用 `<tspan>` 手动换行（无 `<foreignObject>`）
- **字体**：系统 UI 字体栈（跨平台兼容）
- **响应式**：固定 viewBox，支持任意缩放

## 适用场景

- 企业技术培训
- 大学云计算课程
- 技术分享会/沙龙
- 在线教学材料
- 内部知识传递

## 版权说明

本项目基于 PPT Master 框架生成，遵循仓库许可协议。AWS 及相关服务名称为 Amazon Web Services, Inc. 的商标。

---

**生成工具**：PPT Master AI 协作系统  
**策略师 + 执行者（通用风格）**  
**项目路径**：`projects/aws_lego_tutorial_ppt169_20251116/`
