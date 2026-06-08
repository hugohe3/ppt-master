# PyPI 发布配置指南

发布到 PyPI 后，用户可直接通过 `uvx ppt-master <command>` 运行，无需手动安装。

## 初次配置

### 1. PyPI 信任发布

1. 登录 https://pypi.org/manage/account/publishing/
2. 点击 **Add a new pending publisher**
3. 填写：
   - **PyPI Project Name**: `ppt-master`
   - **Owner**: `elvisw`
   - **Repository name**: `ppt-master`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: 留空

### 2. 触发发布

推送 `v*` 标签即自动构建并发布：

```bash
git tag v0.1.0 && git push origin v0.1.0
```

## 本地发布（首次/调试）

```bash
uv build
uv publish --token <your-pypi-token>
```

或使用 Test PyPI 先行验证：

```bash
uv build
uv publish --publish-url https://test.pypi.org/legacy/ --token <your-testpypi-token>
```
