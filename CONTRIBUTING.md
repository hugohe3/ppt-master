# 贡献指南

感谢你考虑为 PPT Master 项目做出贡献！本指南将帮助你了解如何参与项目开发。

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺让参与项目和社区的每个人都能获得无骚扰的体验。

### 我们的标准

积极行为包括：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 issue 并包含以下信息：

1. **清晰的标题** - 简明扼要地描述问题
2. **重现步骤** - 详细说明如何重现问题
3. **预期行为** - 描述你期望发生什么
4. **实际行为** - 描述实际发生了什么
5. **环境信息** - 操作系统、浏览器等
6. **截图** - 如果适用，添加截图帮助解释问题

示例：

```
标题：卡片高度计算在多行布局中不正确

重现步骤：
1. 使用Strategist规划两行布局
2. 指定每行265px高度
3. 使用Executor_General生成SVG

预期：每行卡片高度应为265px
实际：第二行卡片高度为280px

环境：Windows 11, Chrome 120
```

### 功能建议

我们欢迎新功能建议！请创建一个 issue 并包含：

1. **功能描述** - 清楚描述你建议的功能
2. **使用场景** - 解释为什么这个功能有用
3. **可能的实现** - 如果有想法，描述如何实现
4. **替代方案** - 考虑过的其他解决方案

### 提交代码

#### 开发流程

1. **Fork 仓库**

   ```bash
   # 在GitHub上点击Fork按钮
   ```

2. **克隆你的 Fork**

   ```bash
   git clone https://github.com/your-username/ppt-master.git
   cd ppt-master
   ```

3. **创建特性分支**

   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行更改**

   - 保持提交信息清晰明了
   - 遵循项目的代码风格
   - 添加必要的文档

5. **提交更改**

   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

6. **推送到 GitHub**

   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 前往 GitHub 上的原始仓库
   - 点击"New Pull Request"
   - 选择你的分支
   - 填写 PR 描述

#### 提交信息规范

我们使用常规提交格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响代码功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例:**

```
feat(Strategist): add custom color scheme validation

Add validation logic to ensure user-provided color schemes
follow accessibility guidelines and proper contrast ratios.

Closes #123
```

### Pull Request 指南

#### PR 检查清单

在提交 PR 之前，请确保：

- [ ] 代码遵循项目风格
- [ ] 更新了相关文档
- [ ] 添加了示例（如果适用）
- [ ] PR 标题清晰描述了更改
- [ ] PR 描述详细说明了更改内容和原因
- [ ] 关联了相关的 issue（如果有）

#### PR 描述模板

```markdown
## 更改类型

- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 其他（请说明）

## 更改描述

简要描述这个 PR 做了什么。

## 相关 Issue

关闭 #issue_number

## 测试说明

描述如何测试这些更改。

## 截图（如果适用）

添加相关截图。

## 其他说明

任何其他相关信息。
```

## 贡献方向

### 高优先级

1. **示例项目**

   - 添加更多不同主题和风格的示例项目
   - 创建不同行业的演示文稿案例（商业、教育、科技等）
   - 提供完整的工作流程记录

2. **设计模板**

   - 开发新的行业特定模板
   - 扩展图表和可视化组件库
   - 创建可重用的设计元素集

3. **文档改进**
   - 添加更详细的使用教程
   - 创建视频演示和截图
   - 改进 docs/ 目录中的指南文档
   - 添加多语言支持

### 中优先级

1. **工具开发**

   - SVG 预览和编辑工具
   - 配色方案生成器
   - 布局计算器和验证工具

2. **角色优化**
   - 增强现有角色的能力
   - 优化角色间协作流程
   - 添加更多设计风格选项

### 欢迎的贡献

- 📝 修正拼写和语法错误
- 🐛 报告和修复 bug
- 💡 分享使用心得和技巧
- 🎨 贡献设计资源和模板
- 🌍 翻译文档
- 📁 分享你创建的演示文稿项目到 examples/
- ⭐ 给项目加星和推广
- 📖 改进角色定义和工作流程文档

## 开发环境设置

### 推荐工具

1. **代码编辑器**

   - VS Code（推荐）
   - Sublime Text
   - 任何支持 Markdown 的编辑器

2. **SVG 查看器**

   - 现代浏览器（Chrome, Firefox, Safari）
   - Inkscape
   - Adobe Illustrator

3. **版本控制**
   - Git 2.0+
   - GitHub CLI（可选）

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/hugohe3/ppt-master.git

# 进入目录
cd ppt-master

# 查看项目结构
ls -R

# 查看角色定义文件
cd roles
ls

# 查看示例项目
cd ../examples
ls -R

# 在浏览器中查看SVG输出
# 打开 examples/sample_output/ 目录下的 SVG 文件
```

## 项目组织

### 示例项目结构

当你贡献新的示例项目时，请遵循以下结构：

```
examples/
├── sample_input/              # 源文档
│   └── your_topic.md         # 你的输入文档
└── sample_output/            # 生成结果
    ├── design_spec.md        # 设计规范文档
    ├── slide_01.svg          # SVG幻灯片
    ├── slide_02.svg
    └── ...
```

### 用户项目工作区

`projects/` 目录是为用户保留的工作区，用于存放个人项目。贡献示例项目时请使用 `examples/` 目录。

## 代码风格

### Markdown 文档

- 使用标题层级组织内容（#, ##, ###）
- 代码块使用三个反引号包裹并指定语言
- 列表项保持一致的缩进
- 链接使用描述性文本
- 保持行长度在 80-100 字符以内（中文除外）

### 角色定义

- 保持结构清晰和一致
- 使用明确的标题和子标题
- 提供具体的示例
- 包含必要的约束和规范

### SVG 代码

- 使用有意义的 id 和 class 名称
- 添加注释说明主要组件
- 保持代码格式化和缩进
- 避免重复代码，考虑使用`<defs>`和`<use>`

## 审查流程

1. **自动检查** - 代码风格和基本规范
2. **维护者审查** - 功能和设计审查
3. **社区反馈** - 收集使用者意见
4. **合并** - 通过审查后合并到主分支

### 审查时间

- 小型 PR（文档修正等）：1-3 天
- 中型 PR（功能增强）：3-7 天
- 大型 PR（新功能）：1-2 周

## 社区

### 讨论

- 使用 GitHub Issues 进行问题讨论
- 使用 GitHub Discussions 进行想法交流
- 在 PR 中进行代码相关讨论

### 获取帮助

如果你需要帮助：

1. 查看现有的 Issues 和 Discussions
2. 阅读项目文档
3. 创建新的 Issue 说明你的问题
4. 在 PR 中请求审查意见

## 致谢

所有贡献者都将在项目中得到认可！

### 贡献者名单

感谢所有为这个项目做出贡献的人！

<!-- 这里将自动列出贡献者 -->

## 许可

通过贡献代码，你同意你的贡献将在 MIT 许可证下授权。

---

再次感谢你的贡献！🎉
