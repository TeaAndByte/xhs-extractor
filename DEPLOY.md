# 部署指南 (Deployment Guide)

> [!WARNING]
> **为什么不推荐 Vercel?**
> Vercel 是针对静态网站和轻量级 Serverless 函数设计的，对由于文件大小有严格限制 (50MB)。
> 本项目依赖 **Playwright (Chrome 浏览器内核)**，光浏览器文件就超过 100MB，无法直接部署在 Vercel 免费版上。

推荐使用 **Render** 或 **Railway**，它们支持 Docker 容器，可以完美运行本项目，且都有免费额度。

以下是 **Render.com** (类似 Vercel 的体验) 的部署步骤：

## 第一步：上传代码到 GitHub
1.  在 GitHub 上新建一个仓库 (Repository)，例如叫 `xhs-extractor`。
2.  将你电脑上的所有文件上传到该仓库。
    *   如果你熟悉 Git，在项目目录下运行：
        ```bash
        git init
        git add .
        git commit -m "Initial commit"
        git branch -M main
        git remote add origin https://github.com/你的用户名/xhs-extractor.git
        git push -u origin main
        ```
    *   或者直接用网页版 GitHub 上传文件。

## 第二步：在 Render 上部署
1.  注册/登录 [Render.com](https://render.com/)。
2.  点击右上角 **"New +"** -> 选择 **"Web Service"**。
3.  点击 **"Build and deploy from a Git repository"**。
4.  连接你的 GitHub 账号，并选择刚才创建的 `xhs-extractor` 仓库。
5.  **配置参数** (Render 会自动检测，但请确认)：
    *   **Name**: `xhs-extractor` (随便填)
    *   **Region**: Singapore (新加坡) 或其他靠近的节点
    *   **Runtime**: **Docker** (这一步最重要，不要选 Python，要选 **Docker**)
    *   **Instance Type**: Free (免费版)
6.  点击底部的 **"Create Web Service"**。

## 第三步：等待构建
*   Render 会自动读取项目中的 `Dockerfile` 开始构建。
*   第一次构建需要下载浏览器内核，可能需要几分钟。
*   当看到 logs 显示 `Running on http://0.0.0.0:5000` 时，表示部署成功。

## 第四步：访问
Render 会给你一个网址 (例如 `https://xhs-extractor.onrender.com`)，点击即可使用！

---

## 补充：关于登录功能
由于云端服务器的 IP 数据中心 IP，可能会被小红书标记为“风险 IP”，导致无法登录或提取（出现 403）。
*   **免费版 Docker 部署**通常无法保留“登录状态” (因为文件系统是临时的)。
*   如果需要稳定使用，建议就在**本地运行** (电脑开着，手机局域网访问)，这是最稳定且免费的方案。
