# MediaTools v2 - 下载工作台使用指南

## 🚀 快速开始

### 1. 一键启动后端和前端

```bash
python scripts/start.py
```

默认会启动：

- API: `http://127.0.0.1:7860`
- 前端: `http://127.0.0.1:5173`

如需只启动后端：

```bash
python scripts/start.py --backend-only
```

### 2. 手动启动后端 API 服务器

```bash
# 使用默认端口 7860
python -m mediatools serve

# 或指定其他端口
python -m mediatools serve --port 8000
```

服务器启动后会显示：
```
Starting MediaTools API server on http://127.0.0.1:7860
Press Ctrl+C to stop the server
```

### 3. 手动启动前端开发服务器

打开新的终端窗口：

```bash
cd frontend
npm run dev
```

前端会在 `http://localhost:5173` 启动。

### 4. 访问下载工作台

浏览器打开 http://localhost:5173

点击左侧导航栏的"下载"图标即可进入下载工作台。

---

## 📦 功能特性

### 当前支持的功能

✅ **任务提交**
- 支持单个或多个 URL（每行一个）
- 自动检测视频平台
- 可选下载字幕（人工 + 自动字幕）
- 自定义输出目录

✅ **任务列表**
- 实时任务状态（每 2 秒自动刷新）
- 任务进度显示
- 按状态分类（全部/下载中/已完成/失败）
- 搜索功能
- 任务持久化、取消、删除、清空记录

✅ **下载配置**
- 默认 H264+AAC+MP4 格式
- 自动下载原语言字幕并转换为 SRT
- 自动清理 YouTube rolling 重复字幕
- 友好文件命名（语言-作者-标题-平台.ext）

### 暂未实现的功能

⏳ **计划中**（v2 后续版本）
- 重试失败任务
- 批量操作
- WebSocket/SSE 实时推送

❌ **已移除**（Legacy 功能）
- AI 字幕分析
- 视频切片导出
- Photoshop 自动化
- After Effects 集成
- 文件管理器

---

## 🎨 界面说明

### 左侧边栏
- **全部**：显示所有任务
- **下载中**：正在进行的任务
- **已完成**：成功完成的任务
- **失败**：出错的任务

### 中间主区域
- **添加任务**：点击 `+` 按钮打开表单
- **任务列表**：显示所有任务及状态
- **搜索栏**：按标题、URL 搜索任务

### 右侧（暂未实现）
- 将来会显示工具状态（ffmpeg、yt-dlp）

---

## 📝 使用示例

### 示例 1：下载单个 YouTube 视频（带字幕）

1. 点击 `+` 添加任务
2. 输入 URL：
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
3. 平台选择"自动检测"
4. 字幕选择"下载字幕"
5. 点击"确认添加"

结果：
- 视频：`downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.mp4`
- 字幕：`downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.srt`

### 示例 2：批量下载多个视频

1. 点击 `+` 添加任务
2. 输入多个 URL（每行一个）：
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   https://www.youtube.com/watch?v=jNQXAC9IVRw
   https://www.youtube.com/watch?v=L_jWHffIx5E
   ```
3. 确认添加

会创建一个批量任务，串行下载所有 URL。

### 示例 3：只下载字幕（不下载视频）

当前前端暂不支持，可通过 CLI 实现：

```bash
python -m mediatools fetch "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --output-dir downloads --subtitles-only --sub-langs original --convert-subs srt
```

---

## 🔧 配置

### 后端配置

配置文件位置：
- **Windows**: `%LOCALAPPDATA%\mediatools\config.json`
- **macOS**: `~/Library/Application Support/mediatools/config.json`
- **Linux**: `~/.config/mediatools/config.json`

示例配置：
```json
{
  "max_concurrent_downloads": 2
}
```

### 前端配置

前端使用 Vite proxy 自动转发 API 请求到 `localhost:7860`。

如需修改端口，编辑 `frontend/vite.config.ts`：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:YOUR_PORT',
      changeOrigin: true,
    },
  },
}
```

---

## 🐛 故障排除

### 问题 1：前端无法连接后端

**症状**：任务列表为空，提交任务失败

**原因**：后端 API 服务器未启动

**解决**：
```bash
python -m mediatools serve
```

### 问题 2：端口被占用

**症状**：
```
Error: Port 7860 is already in use
```

**解决**：
```bash
# 使用其他端口
python -m mediatools serve --port 8000

# 然后修改 frontend/vite.config.ts 中的 proxy target
```

### 问题 3：任务提交后看不到进度

**症状**：任务提交成功但列表中没有显示

**原因**：当前任务存储在内存中，轮询可能有延迟

**解决**：
1. 等待 2-3 秒（自动刷新间隔）
2. 检查后端日志是否有错误
3. 刷新浏览器页面

### 问题 4：下载失败

**症状**：任务状态显示 "failed"

**常见原因**：
- yt-dlp 未安装或不在 PATH
- 网络问题
- 需要登录的视频（需要 cookies）

**解决**：
```bash
# 检查 yt-dlp
python -m mediatools doctor

# 使用浏览器 cookies
python -m mediatools fetch "URL" --output-dir downloads --cookies-from-browser chrome
```

---

##  API 端点

v2 当前实现的 API 端点：

### `GET /api/doctor`
返回工具状态（ffmpeg、ffprobe、yt-dlp）

### `POST /api/fetch/plan`
验证下载参数（dry-run）

### `POST /api/fetch/tasks`
提交下载任务

**请求体示例**：
```json
{
  "urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
  "output_dir": "downloads",
  "write_subs": true,
  "write_auto_subs": true,
  "sub_langs": "original",
  "convert_subs": "srt",
  "preset": "mp4",
  "max_concurrent": 1
}
```

**响应示例**：
```json
{
  "task_id": "fetch-1719302400-abc123",
  "status": "pending",
  "url_count": 1
}
```

### `GET /api/fetch/tasks`
获取任务列表

**响应示例**：
```json
[
  {
    "id": "fetch-1719302400-abc123",
    "title": "Never Gonna Give You Up",
    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "status": "completed",
    "progress": 1.0,
    "stage": "completed",
    "output_files": [
      "downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.mp4",
      "downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.srt"
    ]
  }
]
```

---

## 🚧 已知限制

1. **任务不持久化**：服务器重启后任务列表清空
2. **无法取消任务**：一旦提交无法中途停止
3. **单线程下载**：`max_concurrent` 当前固定为 1
4. **内存存储**：大量任务可能占用内存

这些限制将在后续版本中改进。

---

## 📚 相关文档

- [项目 README](../README.md) - 完整项目介绍
- [CLI 使用文档](../README.md#首批-mvp-cli) - 命令行用法
- [API 契约](UI_API_CONTRACT.md) - 完整 API 规范
- [优化计划](../OPTIMIZATION_PLAN.md) - 后续开发路线图

---

## 💡 开发技巧

### 调试后端

启动服务器时会输出日志：
```bash
python -m mediatools serve
# 观察 [api] 前缀的日志输出
```

### 调试前端

浏览器开发者工具 → Network 标签 → 查看 API 请求

### 手动测试 API

```bash
# 测试 doctor 端点
curl http://localhost:7860/api/doctor

# 提交任务
curl -X POST http://localhost:7860/api/fetch/tasks \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],"output_dir":"downloads","preset":"mp4"}'

# 查询任务
curl http://localhost:7860/api/fetch/tasks
```

---

**版本**：v2 MVP  
**更新日期**：2026-06-25
