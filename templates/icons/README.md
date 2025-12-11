# SVG 图标库

本目录提供 **640+ 个高质量 SVG 图标**，可直接嵌入到 PPT Master 生成的 SVG 文件中。

> 📦 **图标来源**：[SVG Repo](https://www.svgrepo.com/) - 免费开源 SVG 图标库

- **完整索引**：[FULL_INDEX.md](./FULL_INDEX.md)（按需查阅）
- **JSON 索引**：[icons_index.json](./icons_index.json)（程序化查询）

---

## 使用方式

### 方法一：占位符引用 + 后期嵌入（推荐）

**生成时**使用简单的占位符语法：

```xml
<use data-icon="rocket" x="100" y="200" width="48" height="48" fill="#0076A8"/>
<use data-icon="chart-bar" x="200" y="200" width="48" height="48" fill="#FF6B35"/>
```

**属性说明**：
- `data-icon` - 图标名称（对应文件名，不含 .svg）
- `x`, `y` - 位置
- `width`, `height` - 大小（基础 16px，设 48 即放大 3 倍）
- `fill` - 颜色

**完成后**运行工具一次性替换：

```bash
python3 tools/embed_icons.py svg_output/*.svg
```

### 方法二：直接复制嵌入

```xml
<g transform="translate(100, 200) scale(3)" fill="#0076A8">
  <!-- 从 rocket.svg 复制 path 内容 -->
  <path d="M10 16L12 14V10L13.6569 8.34314..."/>
</g>
```

**常用尺寸**：`scale(2)`=32px, `scale(3)`=48px, `scale(4)`=64px

---

## 常用图标速查

| 分类 | 图标 |
|------|------|
| 数据图表 | `chart-bar` `chart-line` `chart-pie` `arrow-trend-up` `database` |
| 状态反馈 | `circle-checkmark` `circle-x` `triangle-exclamation` `circle-info` |
| 用户组织 | `user` `users` `building` `group` |
| 导航箭头 | `arrow-up` `arrow-down` `arrow-left` `arrow-right` |
| 商务金融 | `dollar` `wallet` `briefcase` `shopping-cart` |
| 工具操作 | `cog` `pencil` `magnifying-glass` `trash` |
| 时间日程 | `clock` `calendar` `stopwatch` |
| 文件文档 | `file` `folder` `clipboard` `copy` |
| 目标安全 | `target` `flag` `shield` `lock-closed` |
| 创意灵感 | `lightbulb` `rocket` `sparkles` `star` |

---

## 设计规范

| 参数 | 值 |
|------|-----|
| viewBox | `0 0 16 16` |
| 基础尺寸 | 16 × 16 px |
| 风格 | 填充（Solid） |

---

**图标数量**：640+ | **完整列表**：[FULL_INDEX.md](./FULL_INDEX.md)
