# XHS Extractor

<p align="center">
  <strong>小红书笔记图片提取与批量下载工具</strong><br>
  粘贴笔记分享链接，解析笔记信息、预览图片，并下载单张图片或 ZIP 图片包。
</p>

<p align="center">
  <a href="https://github.com/TeaAndByte/xhs-extractor">GitHub Repository</a>
  ·
  <a href="./DEPLOY.md">部署指南</a>
</p>

---

## ✨ 项目简介

**XHS Extractor** 是一个轻量级的小红书笔记图片提取工具。用户粘贴小红书笔记链接或分享文案后，服务端使用 Playwright 打开笔记页面，读取页面公开加载的笔记数据，提取图片地址；前端负责图片预览、单张下载和 ZIP 批量下载。

项目采用 Python + Flask 提供 API，Playwright 负责浏览器页面解析，原生 HTML/CSS/JavaScript 构建交互界面。无需数据库，登录状态保存在本地文件中。

> 本项目提取的是页面能够访问到的图片资源，不承诺所有笔记都能提取，也不承诺图片一定为原始分辨率或完全无水印。小红书页面结构、登录策略和图片 CDN 可能变化，解析能力需要随平台变化维护。

## 🧩 功能特性

| 功能 | 说明 |
|---|---|
| 分享链接解析 | 支持小红书笔记链接和 xhslink.com 短链接 |
| 分享文案识别 | 可粘贴包含链接的整段分享文案 |
| 笔记信息提取 | 获取可读取的标题、正文、作者和笔记类型 |
| 图片列表提取 | 读取笔记图片地址并去重 |
| 图片预览 | 网格展示提取到的图片 |
| 单张下载 | 下载指定图片 |
| 批量下载 | 将图片打包为 ZIP 文件 |
| 登录状态复用 | 支持本机浏览器登录并保存 Playwright 状态 |
| 图片代理 | 通过受限 CDN 代理改善预览和下载兼容性 |
| 健康检查 | 提供 /api/health 接口，便于部署平台检测 |

## 🖥️ 使用方式

启动服务后访问 http://localhost:5000：

1. 粘贴小红书笔记链接或分享文案。
2. 如果笔记需要登录，先点击「登录小红书」。
3. 点击「提取图片」，等待解析完成。
4. 预览图片，下载单张图片或打包下载全部图片。

## 🚀 本地运行

### 环境要求

- Python 3.10+
- Windows、macOS 或 Linux
- 可访问小红书的网络环境

### 安装

    git clone https://github.com/TeaAndByte/xhs-extractor.git
    cd xhs-extractor
    python -m venv .venv

Windows PowerShell：

    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m playwright install chromium
    python app.py

macOS / Linux：

    source .venv/bin/activate
    pip install -r requirements.txt
    python -m playwright install chromium
    python app.py

浏览器访问：

    http://localhost:5000

首次使用需要登录时，点击页面中的「登录小红书」，在服务所在电脑弹出的浏览器窗口中完成登录，然后关闭登录标签页保存状态。

## 🐳 Docker 部署

构建镜像：

    docker build -t xhs-extractor .

运行容器并挂载登录状态目录：

    docker run -d \
      --name xhs-extractor \
      -p 5000:5000 \
      -v "$(pwd)/user_data:/app/user_data" \
      --restart unless-stopped \
      xhs-extractor

PowerShell 示例：

    docker run -d --name xhs-extractor -p 5000:5000 -v "$PWD/user_data:/app/user_data" --restart unless-stopped xhs-extractor

更多云平台部署说明见 DEPLOY.md。

**注意：** Docker 容器中的可视化登录需要桌面显示环境。普通云服务器通常没有桌面，建议先在本机登录并安全地管理登录状态；云端部署默认应关闭浏览器登录入口。云平台若使用临时磁盘，容器重建后登录状态可能丢失。

## ⚙️ 配置项

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| PORT | 5000 | Web 服务监听端口 |
| XHS_DATA_DIR | ./user_data | 登录状态保存目录 |
| XHS_ENABLE_BROWSER_LOGIN | true | 是否允许启动可视化登录浏览器 |
| XHS_MAX_IMAGE_BYTES | 26214400 | 单张图片最大代理大小，默认 25 MiB |
| XHS_BROWSER_TIMEOUT_MS | 45000 | 浏览器导航超时时间 |
| LOG_LEVEL | INFO | 日志级别 |

## 🔌 API

### GET /api/health

返回服务状态、登录入口开关和登录状态文件是否存在。

### POST /api/login

在运行服务的机器上打开可视化浏览器，用户登录后关闭登录标签页以保存登录状态。适用于有桌面环境的本地部署。

### POST /api/analyze

请求：

    {
      "url": "https://www.xiaohongshu.com/explore/..."
    }

成功响应示例：

    {
      "success": true,
      "noteId": "示例笔记 ID",
      "title": "笔记标题",
      "desc": "笔记正文",
      "type": "normal",
      "author": "作者昵称",
      "images": ["https://sns-webpic-qc.xhscdn.com/..."],
      "imageCount": 1,
      "warning": "",
      "sourceUrl": "https://www.xiaohongshu.com/explore/..."
    }

### GET /api/proxy?url=<image_url>

代理小红书图片 CDN 资源。接口只接受配置的图片 CDN 域名，并限制单张图片大小和重定向次数。

## 🗂️ 项目结构

    xhs-extractor/
    ├── app.py                 # Flask API、Playwright 页面解析、图片代理
    ├── public/
    │   ├── index.html         # 页面结构
    │   ├── script.js          # 前端交互、预览和下载
    │   └── style.css          # 页面样式
    ├── tests/
    │   └── test_app.py        # URL 校验和健康检查测试
    ├── user_data/             # 本地登录状态（不提交到 Git）
    ├── requirements.txt       # Python 依赖
    ├── Dockerfile             # Docker 镜像
    ├── .dockerignore
    ├── .gitignore
    ├── README.md
    └── DEPLOY.md

## 🔐 隐私与安全

- 登录状态文件可能包含账号 Cookie 等敏感信息，必须妥善保管；项目已将其目录加入 Git 忽略规则。
- 不要将 user_data/state.json 上传到公开仓库，也不要把它分享给他人。
- 图片代理只允许访问指定的小红书图片 CDN 域名，不是通用 URL 代理。
- 建议仅在可信网络或本机使用，不要将未加访问控制的实例直接暴露到公网。
- 请尊重笔记作者的著作权、平台规则和个人隐私；仅下载自己有权保存和使用的内容，不要批量抓取或未经许可转载。

## ⚠️ 已知限制

1. 小红书页面数据结构可能调整，导致解析失败，需要更新提取逻辑。
2. 短链接、部分笔记或未登录状态可能无法访问。
3. 视频笔记不一定包含可提取的图片列表。
4. 图片 CDN 地址可能带有时效性签名，过期后需要重新提取。
5. 云服务器 IP、网络环境和平台风控可能影响访问；项目不提供验证码或风控绕过。
6. 本地可视化登录依赖桌面环境，普通云容器不一定支持。

## 🛠️ 排错

**提取失败或提示未找到笔记数据**
- 确认链接来自小红书笔记，而不是个人主页或其他页面。
- 先在本机浏览器确认该笔记可以正常打开。
- 尝试完成登录后重新提取。
- 查看服务端日志；平台页面结构变化时需要更新解析代码。

**图片预览失败**
- 重新提取，图片链接可能已过期。
- 检查服务端是否可以访问 xhscdn.com 图片 CDN。
- 检查图片是否超过 XHS_MAX_IMAGE_BYTES 限制。

**云端无法登录**
- 可视化登录需要桌面环境；云端建议关闭 XHS_ENABLE_BROWSER_LOGIN。
- 普通免费容器可能休眠或清空本地文件，无法保证登录状态长期保留。

## 📄 License

当前仓库尚未声明开源许可证。如需允许他人复制、修改和分发，请根据项目实际意愿补充 LICENSE 文件。
