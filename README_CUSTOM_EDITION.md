# Usage - DeepSeek & Manus Pro 定制增强版

> 本仓库为 [aqua5230/usage](https://github.com/aqua5230/usage) 的专属定制增强版本，由 **Nickzhangyh** 维护。  
> 在官方原版支持 Claude Code、Codex、Antigravity 与 Grok 的基础上，深度扩展了 **DeepSeek 余额** 与 **Manus Pro 积分点数** 实时监控能力，并针对个人高频使用习惯进行了极致交互优化。

---

## 📌 项目说明 (Project Overview)

`Usage (定制增强版)` 是一款优雅常驻于 macOS 菜单栏与悬浮窗的开发者 AI 配额管理神器。它能在屏幕顶端实时展示当前各大主流大模型工具的剩余额度与点数，无需打开任何网页或后台，随时掌控用量消耗。

### 监控平台支持矩阵
| 平台 / 工具 | 监控指标 | 数据源方式 | 菜单栏展示形式 |
| :--- | :--- | :--- | :--- |
| **Claude Code** | 5 小时会话 & 每周额度 | 本地 Session 日志自动解析 | 官方图标 + 剩余百分比（如 `82%`） |
| **Codex** | 5 小时会话 & 每周额度 | 本地 Session JSONL 日志解析 | 官方图标 + 剩余百分比（如 `88%`） |
| **Antigravity (AGY)** | 5 小时会话 & 每周额度 | 官方账号凭据自动同步 | 官方图标 + 剩余百分比 |
| **Grok CLI** | 每周额度 | 本地会话记录解析 | 官方图标 + 剩余百分比 |
| **DeepSeek** ⭐ *定制* | 账户总余额 / 充值 / 赠金 | 官方 API 或 OneAPI/NewAPI 中转接口 | 官方彩色鲸鱼图标 + 整数余额（如 `¥25`） |
| **Manus Pro** ⭐ *定制* | 账户实际可用点数 / 套餐积分 / 赠送积分 | 本地客户端 Session 自动识别 + ConnectRPC 官方接口 | 官方彩色品牌图标 + 纯整数点数（如 `2788`） |

## 📌 版本演进与发布规范 (Version Roadmap)

本自研定制版遵循语义化版本迭代规则：
- **`v1.0`**：自研定制版首发版本（集成了 DeepSeek 余额监控、Manus Pro 积分点数监控、彩色品牌图标与菜单栏纯整数展示）。
- **`v1.1`**：稳定性与容灾增强版本（优化 Manus Token 内存持久化、SQLite 锁快照读取机制与弹性容灾缓存）。
- **`v1.2`**：实时性与自动刷新修复（解决 Codex/ChatGPT 使用中额度停滞不更新问题，解除 15 分钟索引延迟，后台轮询由 300s 提频至 30s，文件防抖缩短至 3s，FSEvents 挂载 CommonModes）。
- **后续迭代规则**：
  - 功能完善、参数调优与缺陷修复按小版本推进：`v1.3`、`v1.4`...
  - 重大功能引入、新服务平台接入或架构重构按大版本跃迁：`v2.0`、`v3.0`...

---

## 🛠️ 修改内容清单 (Modifications & Changelog)

相对于官方原版仓库，本版本增加了以下核心定制开发与底层缺陷修复：

### 1. Manus Pro 模块深度集成
- **零配置本地自动感知**：无需手动寻找复制 Cookie，直接安全读取本机已登录的 `/Applications/Manus Studio.app` 本地 Session 凭据。
- **官方 ConnectRPC 协议对接**：精准调用官方 `user.v1.UserService/GetAvailableCredits` 与 `UserInfo` 接口。
- **与官方客户端 100% 对齐的点数算法**：
  $$\text{实际可用点数} = \text{totalCredits} - \text{refreshCredits} = \text{套餐可用积分} + \text{赠送积分}$$
  准确显示 Pro 用户的实际积分（如 `2,788 点`）。
- **专属悬浮卡片**：展示 `Manus Pro` 徽章、当前点数、套餐积分进度（如 `1788 / 4000`）及赠送积分（如 `1000`）。
- **彩色品牌高清图标**：提取官方应用超高清图标并经过 LANCZOS 滤波渲染为 144×144 菜单栏图标与卡片矢量图标。
- **多语言完整支持**：繁中、简中、英文、日文、韩文全覆盖。

### 2. DeepSeek 余额与中转支持
- **双协议兼容**：支持官方 `/user/balance` 接口及 OneAPI / NewAPI 等第三方中转站的余额换算接口。
- **原生设置面板**：通过 macOS 原生 `NSAlert` 弹窗自由配置 API Key 与自定义 Base URL。
- **彩色专属图标**：定制官方深蓝彩色鲸鱼菜单栏图标。

### 3. 用户体验与显示细节定制（严格偏好）
- **菜单栏纯整数展示**：所有数值（百分比、金额、积分）严格按照纯整数格式呈现，无冗余小数（例如：`82%  88%  2788`）。
- **方案 B（纯剩余模式）**：进度条与数据均按“剩余量”逻辑渲染。
- **卡片自由排序与独立显隐**：支持鼠标拖拽自由调整各服务上下卡片顺序，并可通过右键菜单「隐藏区块」独立关闭不需要的服务。
- **面板离开自动关闭**：鼠标离开弹出窗口 250ms 即自动收起，不遮挡工作区。

### 4. 底层 Bug 修复
- **修复 Codex 自动刷新故障**：解决了官方原版在遇到目录级 FSEvents 变更事件时，因扩展名校验未穿透子目录而导致 Codex 额度消耗后菜单栏不自动刷新的致命缺陷。

---

## 💻 安装环境要求 (Environment Requirements)

- **操作系统**：macOS 12.0 Monterey 或更高版本（支持 Apple Silicon M1/M2/M3/M4 及 Intel 架构）
- **Python 运行时**：Python 3.13（官方打包基线）或 Python 3.11+
- **构建依赖**：
  - `py2app` (用于打包生成独立 .app)
  - `pyobjc` (用于调用 macOS 原生 Cocoa / AppKit 接口)
  - `Pillow` (用于高清图标处理)
- **可选客户端**：
  - 已安装并登录的 `Manus Studio.app`（若需显示 Manus 点数）
  - 已运行的 Claude Code / Codex / Antigravity

---

## 🚀 启动、安装与构建的提示词 (AI Prompt & Commands)

如果你希望在其他机器上通过 AI 助手（如 Cursor / Claude Code / Antigravity）直接构建、安装或维护本项目，可直接复制以下**一键式提示词**发给 AI：

```markdown
请帮我编译并安装本仓库的 Usage (定制增强版) 到我的 macOS 系统中：
1. 检查 Python 3.13 及 py2app 环境。
2. 运行打包命令：python3 setup_app.py py2app
3. 将构建生成的 dist/usage.app 复制到 /Applications/usage.app 目录。
4. 重启应用使修改生效：killall usage 2>/dev/null || true && open /Applications/usage.app
5. 验证顶部菜单栏是否正确显示 Claude, Codex, DeepSeek 以及 Manus 的纯整数额度。
```

### 本地手动编译与调试命令

#### 1. 源码直接运行测试（无需打包）：
```bash
python3 main.py
```

#### 2. 打包为 macOS 独立应用：
```bash
# 安装打包依赖
pip3 install py2app pyobjc Pillow

# 执行构建
python3 setup_app.py py2app

# 安装到系统应用程序
cp -R dist/usage.app /Applications/

# 重启应用
killall usage 2>/dev/null || true
open /Applications/usage.app
```

---

## 📄 开源许可证 (License)

本项目基于 [AGPL-3.0 License](LICENSE) 开源。定制内容遵循原项目的开源许可证协议。
