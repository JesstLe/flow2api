# Google Flow 权益接入

本分支通过正常登录的 `flow.google.com` 页面和 Chrome 扩展接入 Google Flow 权益，不使用 CDP、远程调试端口、浏览器 Profile 克隆或 Cookie 数据库读取。

## 请求链路

```text
New API / OpenAI client
        -> http://127.0.0.1:38000
        -> Flow2API
        -> ws://127.0.0.1:38001/captcha_ws
        -> Chrome extension
        -> logged-in Google Flow page
```

`38000` 用于 OpenAI/Gemini 兼容 API；`38001` 专供本机 Chrome 扩展连接。两个端口指向同一个容器，便于旧客户端继续使用 `38000`，同时让扩展拥有明确的连接端口。

## 启动

```powershell
Copy-Item extension/local-config.example.js extension/local-config.js
# 编辑 extension/local-config.js，填入管理后台 API Key；该文件已被 Git 忽略。
docker compose up -d --build
```

在 Chrome 的扩展管理页加载 `extension` 目录，然后打开并登录目标 Flow 项目。扩展会捕获当前 Flow 页面实际使用的授权，并通过 `flow-fixed` 路由交给后端刷新。

## 验证

健康状态应满足：

```text
backend_running=true
active_tokens=1
available_tokens=1
extension_connected_tokens=1
tokens_expired=0
captcha_method=extension
```

Gemini 格式：

```http
POST /models/gemini-3.1-flash-image-square:generateContent
```

成功响应必须包含：

```text
candidates[].content.parts[].inlineData
```

OpenAI 格式：

```http
POST /v1/chat/completions
```

模型可使用 `gemini-3.1-flash-image-square` 或 `gemini-3.1-flash-image-lite-square`。仅检查 HTTP 200 不足以证明出图成功，还应下载并打开返回图片。

## 重复扩展处理

如果浏览器中同时存在旧扩展和当前扩展，同一路由可能收到多个 WebSocket。后端优先选择明确命名的 `chrome-flow-current`，避免 `chrome-default` 重连时顶掉正在执行任务的连接。

## 敏感信息

- 不提交 `extension/local-config.js`。
- 不在日志、文档或提交中记录 API Key、Google Access Token、Session Token 或 Cookie。
- Token 过期后应通过正常 Flow 页面和扩展刷新。
