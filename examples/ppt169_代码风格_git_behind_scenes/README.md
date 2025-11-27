# Git 幕后探秘：哈希与对象

## 项目信息

- **项目名称**: Git 幕后探秘：哈希与对象
- **创建日期**: 2025-11-07
- **格式**: PPT 16:9 (1280×720)
- **风格**: 通用灵活风格
- **总页数**: 8 页

## 内容概述

本演示文稿深入讲解 Git 的底层数据模型，揭示 Git 作为键值数据库的工作原理，重点介绍：

### 核心主题

1. **Git 对象数据库**: 理解 `.git/objects/` 目录的结构
2. **SHA-1 哈希机制**: 40 位十六进制字符串如何作为对象的唯一标识
3. **三种核心对象**:
   - **Blob**: 存储文件内容
   - **Tree**: 表示目录结构
   - **Commit**: 代表项目快照
4. **对象链接关系**: Commit → Tree → Blobs/Trees 的引用链条
5. **管道命令**: `git hash-object` 和 `git cat-file` 的使用
6. **实践应用**: 故障排查、数据恢复、工具构建
7. **常见问题**: 文件去重、历史追溯等原理解答

## 目标受众

- 技术开发者（初中级）
- 计算机专业学生
- 希望深入理解 Git 原理的用户

## 使用场景

- 技术分享会
- 培训课程
- 自学资料

## 文件结构

```
git_behind_scenes_ppt169_20251107/
├── README.md                           # 本文件
├── 设计规范与内容大纲.md                # 设计规范文档
├── preview.html                        # 在线预览页面
└── svg_output/                         # SVG 幻灯片
    ├── slide_01_cover.svg              # 封面
    ├── slide_02_core_concepts.svg      # 核心概念总览
    ├── slide_03_sha1_hashing.svg       # SHA-1 哈希机制
    ├── slide_04_three_objects.svg      # 三种对象类型详解
    ├── slide_05_object_links.svg       # 对象链接关系
    ├── slide_06_plumbing_commands.svg  # 底层探索命令
    ├── slide_07_best_practices.svg     # 实践应用与最佳实践
    └── slide_08_faq.svg                # 常见问题解答
```

## 预览方式

### 方式一：使用预览页面（推荐）

在浏览器中打开 `preview.html`：

```bash
# Windows
start preview.html

# macOS
open preview.html

# Linux
xdg-open preview.html
```

预览页面支持：

- ⬅️ ➡️ 方向键导航
- 空格键前进
- F 键全屏模式
- 响应式布局

### 方式二：使用 HTTP 服务器

```bash
# Python 3
python -m http.server --directory svg_output 8000

# 然后在浏览器访问
# http://localhost:8000
```

### 方式三：直接打开 SVG

在浏览器中直接打开任意 SVG 文件查看单页内容。

## 设计特色

### 色彩编码系统

- **Commit 对象**: 黄色 (#f59e0b)
- **Tree 对象**: 绿色 (#10b981)
- **Blob 对象**: 紫色 (#8b5cf6)
- **主题蓝**: (#2563eb)

### 视觉元素

- 流程图展示对象关系
- 代码示例使用深色背景
- 图标与色彩编码相结合
- 清晰的层次结构

### 布局特点

- 标题栏使用浅灰背景
- 卡片式内容组织
- 充足的留白和间距
- 16:9 标准比例

## 技术规范

- **画布尺寸**: 1280×720 (viewBox: 0 0 1280 720)
- **字体系统**: 系统 UI 字体栈
- **代码字体**: Cascadia Code, Fira Code, Consolas
- **禁止**: `<foreignObject>` 元素
- **换行方式**: 使用 `<tspan>` 手动换行

## 学习要点

本演示文稿帮助理解：

1. ✅ Git 是基于内容寻址的文件系统
2. ✅ SHA-1 哈希如何确保数据完整性
3. ✅ 对象模型如何构建版本历史
4. ✅ 为什么相同内容只存储一次
5. ✅ 如何通过 Commit 哈希追溯完整快照

## 适用范围

### 适合

- 深入学习 Git 原理
- 理解版本控制系统设计
- 故障排查和数据恢复
- 构建 Git 相关工具

### 不适合

- Git 日常使用入门
- 快速上手指南
- 基础命令教学

## 最佳实践建议

1. **重在理解概念**: 无需记住所有管道命令
2. **建立心智模型**: Git = 基于内容寻址的文件系统
3. **从根本理解**: 高层命令（commit、merge）的底层原理
4. **安全第一**: 不要手动修改 `.git` 目录

## 扩展阅读

- [Pro Git Book - Chapter 10: Git Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Git Object Model Documentation](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- [Understanding Git Data Model](https://www.atlassian.com/git/tutorials/git-internals)

## 版权信息

本项目遵循 PPT Master 项目规范生成。

---

**提示**: 这些知识是"锦上添花"，初学者应该先掌握日常高频命令（add、commit、push、merge 等），再深入底层原理。
