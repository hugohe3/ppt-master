# Projects 目录说明

## 目录用途

`projects/` 目录用于存放**进行中的工作项目**（Work-in-Progress），这些项目可能处于以下状态：

- 🚧 正在开发中
- ✏️ 需要频繁修改
- 🧪 实验性质的尝试
- 📝 半成品或草稿

## 为什么不纳入 Git 版本控制？

为了保持主仓库的整洁和高效，`projects/` 目录的内容**不会提交到 Git**：

1. **避免仓库膨胀**：频繁修改、移动、删除文件会导致 Git 历史膨胀
2. **保持灵活性**：您可以随意实验、重组项目结构，无需担心提交历史
3. **减少噪音**：半成品内容不会污染仓库的提交历史
4. **提高性能**：减少 Git 需要跟踪的文件数量

## 数据同步建议

虽然 `projects/` 不在 Git 版本控制中，但您仍然可以在多台设备间同步：

### 推荐方案：云同步服务

- **macOS 用户**：使用 iCloud Drive 自动同步整个工作目录
- **跨平台**：Dropbox、坚果云、OneDrive、Google Drive
- **企业用户**：企业网盘或 NAS

### 配置方法

只需将整个 `ppt-master` 目录放在云同步文件夹中：

```
~/Library/Mobile Documents/com~apple~CloudDocs/ppt-master/  # iCloud
~/Dropbox/ppt-master/                                        # Dropbox
~/坚果云/ppt-master/                                          # 坚果云
```

云同步服务会自动同步 `projects/` 目录，无需额外配置。

## 工作流程

### 1. 创建新项目

在 `projects/` 中创建新项目目录：

```bash
mkdir -p projects/my_new_project_ppt169_20251117
```

### 2. 开发迭代

在项目目录中自由工作，所有修改都只在本地（和云同步）：

- 创建、修改、删除文件
- 调整目录结构
- 实验不同的设计方案

### 3. 完成项目

当项目完成并达到发布质量后，将其移动到 `examples/` 目录：

```bash
# 移动整个项目目录
mv projects/my_new_project_ppt169_20251117 examples/

# 提交到 Git
cd examples
git add my_new_project_ppt169_20251117/
git commit -m "feat: 新增 XXX 项目示例"
```

### 4. 清理旧项目

定期清理不再需要的旧项目：

```bash
# 删除已完成或不需要的项目
rm -rf projects/old_project_ppt169_20251101
```

## 目录结构建议

可以根据需要组织子目录：

```
projects/
├── active/              # 正在进行的项目
├── review/             # 待审查的项目
├── archive/            # 归档的旧项目
│   ├── 2025-11/
│   └── 2025-10/
└── README.md           # 本文件
```

## 与 examples/ 目录的区别

| 特性 | projects/ | examples/ |
|------|-----------|-----------|
| **用途** | 进行中的工作项目 | 已完成的精品示例 |
| **版本控制** | ❌ 不提交 Git | ✅ 提交 Git |
| **质量要求** | 草稿、半成品 | 高质量、可发布 |
| **修改频率** | 频繁修改 | 基本稳定 |
| **同步方式** | 云同步服务 | Git 同步 |

## 常见问题

### Q: 如果我需要版本控制 projects 中的某个重要项目怎么办？

A: 有两个选择：
1. 将该项目提前移到 `examples/` 目录
2. 为特定项目创建独立的 Git 仓库

### Q: 云同步和 Git 会冲突吗？

A: 不会。`projects/` 已在 `.gitignore` 中排除，Git 完全忽略它，不会与云同步冲突。

### Q: 误删了 projects 中的文件怎么办？

A: 如果使用云同步服务（如 iCloud、Dropbox），通常可以从云服务的回收站或版本历史中恢复。

## 相关文档

- **角色定义**：[AGENTS.md](../AGENTS.md)
- **工作流教程**：[docs/workflow_tutorial.md](../docs/workflow_tutorial.md)
- **示例项目**：[examples/](../examples/)

