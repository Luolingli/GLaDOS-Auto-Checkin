# 📌 GLaDOS  自动签到

一个基于 **GitHub Actions** 的 **GLaDOS 自动签到脚本**。
 **无需服务器、无需编程基础**，每天自动帮你签到。

------

## ✨ 功能说明

- ✅ **每天自动签到**
- 🔁 **已签到自动识别，不会报错**
- 👥 **支持多个账号**
- 📬 **可选签到结果推送（Telegram Bot）**
- 🆓 **完全免费，使用 GitHub Actions**

------

## 📂 项目结构

```
.
├── checkin.py                 # 签到脚本（不用动）
└── .github/workflows/
    └── glados.yml              # GitHub Actions 配置（不用动）
```

------

## 🚀 使用教程

### 第一步：Fork 本项目

1. 点击右上角 **Fork**
2. Fork 到你自己的 GitHub 账号下

👉 后续所有操作都在你 **自己的仓库** 中完成

------

### 第二步：获取 GLaDOS Cookie

1. 打开浏览器，登录：https://glados.cloud
2. 按 **F12** 打开开发者工具
3. 找到：
   - Chrome：`Application` → `Cookies`
   - Firefox：`存储` → `Cookies`
4. 选择 `glados.cloud`
5. **复制完整 Cookie 内容**

示例（示意）：

```
koa:sess=xxxxxx; koa:sess.sig=yyyyyy
```

⚠️ **必须是完整的一整段，不要只复制一半**

------

### 第三步：添加 GitHub Secrets

进入你 Fork 后的仓库：

1. 点击 **Settings**
2. 左侧选择 **Secrets and variables → Actions**
3. 点击 **New repository secret**

#### 添加第一个 Secret（必填）

- **Name**：`COOKIES`
- **Value**：粘贴刚才复制的完整 Cookie

点击 **Save**

------

### （可选）第四步：开启签到结果推送

如果你想每天收到签到通知（可选）：

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 创建机器人，拿到 `TG_BOT_TOKEN`
3. 打开你新建的机器人，先发一条任意消息
4. 访问：`https://api.telegram.org/bot<你的TG_BOT_TOKEN>/getUpdates`
5. 在返回内容中找到你的 `chat.id`（这就是 `TG_CHAT_ID`）
6. 在 GitHub Secrets 中添加下面两个：

- **Name**：`TG_BOT_TOKEN`
- **Value**：你的 Telegram Bot Token

- **Name**：`TG_CHAT_ID`
- **Value**：你的聊天 ID（数字，可能是负数）

不填也没关系，只是不会推送。

------

## 👥 多账号如何添加？

### 推荐规则：

> **多个账号的 Cookie，每行一个**

示例：

```
koa:sess=账号1; koa:sess.sig=账号1签名
koa:sess=账号2; koa:sess.sig=账号2签名
koa:sess=账号3; koa:sess.sig=账号3签名
```

⚠️ 注意事项：

- 每个 cookie 都是完整的一段
- 不要用逗号
- 旧版 `cookie_账号1 & cookie_账号2` 的写法仍然兼容，但更推荐每行一个

------

## ⏰ 自动签到时间说明

项目默认设置为：

```
每天 UTC 04:17 到 08:47 多次兜底运行
```

换算成北京时间：

> 🕛 **每天中午 12:17 到傍晚 16:47 之间自动尝试多次签到**

GitHub Actions 的定时任务可能会有明显延迟，甚至偶尔丢弃单次 cron，所以项目配置了多个兜底时间点。脚本会自动识别当天已签到的返回，不会因为重复运行而报错；真正失败时会让 Actions 变红，并在日志中输出失败原因，方便你判断是否需要更新 Cookie。
