# 部署指南

本项目依赖 Playwright Chromium。建议优先选择本机运行；云端部署需要考虑平台风控、容器磁盘持久化和无桌面环境等限制。

## 1. 本机运行（推荐）

按 README 的「本地运行」章节安装 Python 依赖和 Chromium，然后执行：

    python app.py

浏览器访问 http://localhost:5000。本机有桌面环境，可以使用页面中的登录按钮完成登录。

## 2. Docker 本机部署

构建：

    docker build -t xhs-extractor .

运行并持久化登录目录：

    docker run -d --name xhs-extractor -p 5000:5000 -v "$(pwd)/user_data:/app/user_data" --restart unless-stopped xhs-extractor

容器中的浏览器登录需要图形显示环境。普通 Docker 后台容器通常没有桌面，不能直接使用可视化登录按钮；建议在本机环境完成登录，或者在云端关闭登录入口。

## 3. Render / Railway 等云平台

可使用支持 Docker 的 Web Service 部署：

1. 将仓库连接到部署平台。
2. 选择 Dockerfile 构建。
3. 配置服务端口为平台提供的 PORT 环境变量（应用已读取该变量）。
4. 健康检查路径设置为 /api/health（如果平台支持）。
5. 设置环境变量：

    XHS_ENABLE_BROWSER_LOGIN=false
    XHS_DATA_DIR=/app/user_data

6. 如果需要跨容器重启保留登录状态，必须配置持久化磁盘并挂载到 /app/user_data。

**重要限制：**

- 免费实例可能休眠、重启或使用临时文件系统；不能保证登录状态持久化。
- 云服务器出口 IP 可能受到平台风控影响，出现访问失败或验证码。
- 云端无桌面环境时，/api/login 会被禁用；不要把登录 Cookie 直接写进公开仓库或镜像。
- 不要把没有身份验证的服务直接公开给所有人使用。当前项目适合个人可信环境，不是多用户 SaaS 服务。

## 4. 常用配置

| 变量 | 默认值 | 说明 |
|---|---|---|
| PORT | 5000 | 服务监听端口 |
| XHS_DATA_DIR | ./user_data | 登录状态目录 |
| XHS_ENABLE_BROWSER_LOGIN | true | 是否启用本机可视化登录 |
| XHS_MAX_IMAGE_BYTES | 26214400 | 图片代理最大字节数 |
| XHS_BROWSER_TIMEOUT_MS | 45000 | 浏览器超时时间 |

## 5. 验证服务

    curl http://localhost:5000/api/health

预期返回包含 "success": true 的 JSON。

## 6. 登录状态备份

登录状态文件位于 user_data/state.json。它可能包含有效 Cookie，请按密码级别保护：

- 不要提交到 Git。
- 不要放在公开网盘或公开对象存储。
- 不要在多人之间共享。
- 如果怀疑泄露，请在小红书侧退出相关登录会话并重新登录。
