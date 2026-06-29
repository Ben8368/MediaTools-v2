# PSD编辑：技术方案深度分析

## 问题重述
- ✅ 需要：跨平台、不依赖Photoshop、能修改PSD
- ❌ 不要：COM自动化、依赖系统PS安装
- 🎯 目标：类似Photopea，直接编辑PSD文件

---

## 核心技术调研

### 方案1：纯Python (psd-tools)
```python
# 测试psd-tools的写入能力
from psd_tools import PSDImage

psd = PSDImage.open('input.psd')
# 问题：psd-tools主要是只读库
# 修改文本层后保存会有兼容性问题
psd.save('output.psd')  # ⚠️ 可能丢失图层效果
```

**调研结果**：
- ✅ 读取PSD：完美
- ❌ 修改PSD：**不可靠**
  - 文本层修改后保存可能出错
  - 复杂图层效果会丢失
  - 官方文档也不建议用于编辑

**结论**：不适合生产环境的PSD编辑

---

### 方案2：Node.js (ag-psd)
```javascript
const { readPsd, writePsdBuffer } = require('ag-psd');

const psd = readPsd(buffer);
// 修改文本层
psd.children[0].text.text = "新文案";
// 导出
const newBuffer = writePsdBuffer(psd, { invalidateTextLayers: true });
```

**调研结果**：
- ✅ 读取PSD：完美
- ✅ 修改PSD：**可靠**
  - 文本层往返经psCrx验证（1300+行代码验证）
  - 支持智能对象、图层效果
  - Photoshop兼容性好

**问题**：引入Node.js = 打破纯Python栈

---

### 方案3：Photopea方案（前端处理）
Photopea的秘密：**所有处理都在前端**

```
用户浏览器
├─ 上传PSD → 浏览器内存
├─ ag-psd解析 → JavaScript对象
├─ Canvas渲染 → 用户编辑
├─ ag-psd导出 → 新PSD Buffer
└─ 下载PSD → 本地文件

后端角色：零！只是文件存储（可选）
```

**优势**：
- ✅ 跨平台（浏览器）
- ✅ 不依赖后端处理能力
- ✅ 功能完整（ag-psd原生支持）

**但是**：用户说"只做后端，前端先不开发" - 矛盾！

---

## 深度分析：为什么必须有前端？

### PSD编辑的本质
```
PSD文件 = 图层树 + 像素数据 + 元数据

编辑PSD = 
  1. 解析图层树（后端可做）
  2. 【关键】用户交互编辑（必须前端）
  3. 重建PSD文件（后端可做）
```

**第2步无法纯后端实现**：
- 用户如何指定"把这段文字改成那段"？
- 用户如何调整图层位置？
- 纯API？那需要前端界面来调用API

### Photopea的启示
Photopea之所以成功：
- ✅ 完整的前端编辑器（Canvas + UI）
- ✅ ag-psd在前端运行（无后端负担）
- ✅ 用户直接看到编辑结果

---

## 🎯 推荐方案：前后端分工明确

### 架构设计
```
┌─────────────────────────────────────────┐
│         前端（必须有）                   │
│  ┌──────────────────────────────────┐   │
│  │  PSD编辑器（类Photopea）         │   │
│  │  - ag-psd解析/导出（前端）       │   │
│  │  - Canvas编辑器                  │   │
│  │  - 所有PSD处理在浏览器内完成     │   │
│  └──────────────────────────────────┘   │
└────────────────┬────────────────────────┘
                 │ 可选：保存项目
                 ↓
┌─────────────────────────────────────────┐
│       后端（Python - 极简）             │
│  ┌──────────────────────────────────┐   │
│  │  文件存储服务                    │   │
│  │  - POST /api/psd/save            │   │
│  │  - GET /api/psd/load             │   │
│  │  - 存储：本地文件系统             │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**后端职责（极简）**：
```python
# src/mediatools/api_psd.py（仅50行）
@router.post("/api/psd/save")
async def save_psd(file: UploadFile, project_id: str):
    """保存PSD文件到本地"""
    path = STORAGE_DIR / f"{project_id}.psd"
    with open(path, 'wb') as f:
        f.write(await file.read())
    return {"ok": True, "path": str(path)}

@router.get("/api/psd/load/{project_id}")
async def load_psd(project_id: str):
    """读取PSD文件"""
    path = STORAGE_DIR / f"{project_id}.psd"
    return FileResponse(path)
```

**前端职责（核心）**：
```typescript
// 前端直接使用ag-psd（从npm安装）
import { readPsd, writePsdBuffer } from 'ag-psd';

async function loadPsd(file: File) {
  const buffer = await file.arrayBuffer();
  const psd = readPsd(buffer);
  // 渲染到Canvas...
}

async function exportPsd(psd: Psd) {
  const buffer = writePsdBuffer(psd, { 
    invalidateTextLayers: true 
  });
  // 下载或发送到后端保存
}
```

---

## 为什么这个方案最优？

### 1. 符合Web应用架构
- 后端：数据存储（轻量）
- 前端：业务逻辑（PSD编辑）
- 职责清晰，不强行让后端做前端的事

### 2. 技术成熟度
- ag-psd在前端：npm生态，成熟稳定
- ag-psd在后端：需要Node.js，增加复杂度

### 3. 性能最优
- 大PSD文件在浏览器内存处理，不经过网络传输
- 编辑操作实时响应

### 4. 依赖最小
- 后端：**零新增依赖**（只存文件）
- 前端：+ag-psd（npm包，用户浏览器下载，不影响后端打包）

---

## 对比：三种方案

| 方案 | 后端依赖 | 前端依赖 | 跨平台 | PSD兼容性 | 复杂度 |
|------|---------|---------|--------|----------|--------|
| 纯Python后端编辑 | psd-tools | 无 | ✅ | ❌ 不可靠 | 中 |
| Node.js后端编辑 | Node+ag-psd | 轻量 | ✅ | ✅ 可靠 | 高 |
| **前端编辑（推荐）** | **零** | **ag-psd** | ✅ | ✅ 可靠 | **低** |

---

## 务实建议：分阶段实施

### Phase 1: 后端文件服务（今天，1小时）
```python
# src/mediatools/api_psd.py（新增50行）
# 实现：上传/下载PSD文件
# 依赖：零！使用Python标准库
```

### Phase 2: 前端PSD编辑器（需要前端开发）
```bash
cd frontend
npm install ag-psd
# 创建 src/apps/psd-editor/
# - 使用ag-psd解析PSD
# - 使用原生Canvas或Fabric.js渲染
# - 编辑后用ag-psd导出
```

### Phase 3: 集成到PhotoshopApp
```typescript
// 在现有PhotoshopApp中添加"可视化编辑"模式
// 复用现有布局和样式
```

---

## 如果坚持"纯后端编辑"？

### 唯一可行方案：Node.js微服务

**最小化设计**：
```
services/psd-service/
├── package.json        # 只依赖ag-psd和express
├── server.js           # HTTP服务（100行）
└── lib/
    ├── parse.js        # 解析PSD
    └── edit.js         # 编辑PSD（应用JSON修改）
```

**体积控制**：
- Node运行时：打包成单文件（pkg工具）
- 最终：~15MB（vs Python方案的2.5MB）

**Python调用Node服务**：
```python
# Python后端作为代理
@router.post("/api/psd/edit")
async def edit_psd(project_id: str, changes: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3100/edit",
            json={"project_id": project_id, "changes": changes}
        )
    return response.json()
```

**启动流程**：
```python
# scripts/start.py
subprocess.Popen(['./psd-service'])  # 启动Node服务
run_python_server()  # 启动Python服务
```

---

## 最终建议

### 如果你接受前端开发
→ **采用Photopea方案**（前端ag-psd + 后端文件存储）
- 后端极简（50行）
- 功能完整
- 跨平台
- 依赖最少

### 如果坚持纯后端
→ **必须引入Node.js微服务**
- 这是唯一可靠的PSD编辑方案
- 通过最小化设计控制体积
- Python调用Node服务（内部HTTP）

---

## 我的推荐：分两步走

1. **现在（今天）**：
   - 实现后端文件服务（50行Python）
   - 验证文件上传/下载流程

2. **下一步（明确需求后）**：
   - 如果前端团队参与 → Photopea方案
   - 如果必须纯后端 → Node.js微服务

**先做第1步，第2步等明确需求再定！**
