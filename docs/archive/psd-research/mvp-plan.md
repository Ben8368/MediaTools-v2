# PSD编辑工作台 MVP 开发计划

## 目标
2天内完成核心功能验证，证明技术可行性

---

## MVP范围（最小可用功能）

### ✅ 必须实现
1. **PSD上传与解析**
   - 上传PSD文件
   - Node服务解析为JSON
   - 前端显示图层列表

2. **Canvas可视化**
   - Fabric.js渲染文本层
   - 渲染图片层
   - 拖拽移动图层

3. **文本编辑**
   - 双击文本层进入编辑模式
   - 修改文字内容
   - 修改字体和大小

4. **导出PSD**
   - 将编辑后的JSON发送到Node服务
   - 重建PSD文件
   - 下载到本地

### ❌ 暂不实现（后续迭代）
- 一键翻译（API已有，接入简单）
- 一键改尺寸
- 智能对象展开
- 图层样式（阴影、描边等）
- Undo/Redo

---

## 技术栈

### Node.js PSD服务
```bash
npm install express multer ag-psd sharp cors
```

**核心文件**：
- `services/psd-service/server.js` - HTTP服务
- `services/psd-service/lib/parse.js` - PSD→JSON
- `services/psd-service/lib/export.js` - JSON→PSD

### Python后端
```python
# src/mediatools/api_psd.py
# 仅作为代理层，转发到Node服务
```

### React前端
```bash
cd frontend
npm install fabric
```

**核心组件**：
- `apps/PsdEditorApp.tsx` - 主界面
- `apps/psd-editor/EditorCanvas.tsx` - Canvas画布
- `apps/psd-editor/LayerPanel.tsx` - 图层面板
- `apps/psd-editor/PropertyPanel.tsx` - 属性面板

---

## 开发步骤

### Day 1: 后端服务

#### 上午（4小时）：Node.js PSD服务
```bash
# 1. 创建项目
mkdir -p services/psd-service
cd services/psd-service
npm init -y

# 2. 安装依赖
npm install express multer ag-psd sharp cors

# 3. 实现核心功能
# - POST /parse - 上传PSD，返回JSON
# - POST /export - 接收JSON，返回PSD Buffer
# - GET /layer/:id/preview - 返回图层预览图

# 4. 测试
# 用Postman上传测试PSD，验证返回的JSON结构
```

**关键代码**：
```javascript
// server.js
const express = require('express');
const multer = require('multer');
const { parsePsd } = require('./lib/parse');
const { exportPsd } = require('./lib/export');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.post('/parse', upload.single('file'), async (req, res) => {
  const buffer = fs.readFileSync(req.file.path);
  const json = await parsePsd(buffer);
  res.json(json);
});

app.post('/export', express.json(), async (req, res) => {
  const psdBuffer = await exportPsd(req.body);
  res.setHeader('Content-Type', 'application/octet-stream');
  res.send(psdBuffer);
});

app.listen(3100);
```

#### 下午（4小时）：Python API代理
```python
# src/mediatools/api_psd.py
from fastapi import APIRouter, UploadFile
import httpx

router = APIRouter()

NODE_SERVICE = "http://localhost:3100"

@router.post("/api/psd/upload")
async def upload_psd(file: UploadFile):
    """上传PSD并解析"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NODE_SERVICE}/parse",
            files={"file": file.file}
        )
    data = response.json()
    
    # 保存到数据库（简单起见，先用文件系统）
    project_id = generate_id()
    save_project(project_id, data)
    
    return {"project_id": project_id, "data": data}

@router.post("/api/psd/export/{project_id}")
async def export_psd(project_id: str):
    """导出PSD"""
    project = load_project(project_id)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NODE_SERVICE}/export",
            json=project
        )
    
    return StreamingResponse(
        response.iter_bytes(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={project_id}.psd"}
    )
```

---

### Day 2: 前端编辑器

#### 上午（4小时）：Canvas渲染
```typescript
// frontend/src/apps/psd-editor/EditorCanvas.tsx
import { useEffect, useRef } from 'react';
import { Canvas, FabricText, FabricImage } from 'fabric';

export function EditorCanvas({ layers, onLayerUpdate }) {
  const canvasRef = useRef(null);
  const fabricCanvas = useRef(null);
  
  useEffect(() => {
    fabricCanvas.current = new Canvas(canvasRef.current, {
      width: 800,
      height: 600
    });
    
    // 监听对象修改
    fabricCanvas.current.on('object:modified', (e) => {
      const obj = e.target;
      onLayerUpdate(obj.data.layerId, {
        left: obj.left,
        top: obj.top
      });
    });
  }, []);
  
  // 渲染图层
  useEffect(() => {
    if (!fabricCanvas.current) return;
    
    fabricCanvas.current.clear();
    
    layers.forEach(layer => {
      if (layer.type === 'text') {
        const text = new FabricText(layer.text.content, {
          left: layer.left,
          top: layer.top,
          fontSize: layer.text.fontSize,
          fontFamily: layer.text.font
        });
        text.data = { layerId: layer.id };
        fabricCanvas.current.add(text);
      }
    });
  }, [layers]);
  
  return <canvas ref={canvasRef} />;
}
```

#### 下午（4小时）：主界面集成
```typescript
// frontend/src/apps/PsdEditorApp.tsx
import { useState } from 'react';
import { EditorCanvas } from './psd-editor/EditorCanvas';
import { LayerPanel } from './psd-editor/LayerPanel';

export function PsdEditorApp() {
  const [project, setProject] = useState(null);
  const [selectedLayerId, setSelectedLayerId] = useState(null);
  
  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/psd/upload', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    setProject(data.data);
  };
  
  const handleLayerUpdate = (layerId, changes) => {
    setProject(prev => ({
      ...prev,
      layers: prev.layers.map(layer =>
        layer.id === layerId ? { ...layer, ...changes } : layer
      )
    }));
  };
  
  const handleExport = async () => {
    const response = await fetch(`/api/psd/export/${project.id}`, {
      method: 'POST'
    });
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'edited.psd';
    a.click();
  };
  
  return (
    <div className="psd-editor-app">
      <div className="toolbar">
        <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
        <button onClick={handleExport}>导出PSD</button>
      </div>
      
      <div className="workspace">
        <LayerPanel
          layers={project?.layers || []}
          selectedId={selectedLayerId}
          onSelect={setSelectedLayerId}
        />
        
        <EditorCanvas
          layers={project?.layers || []}
          onLayerUpdate={handleLayerUpdate}
        />
      </div>
    </div>
  );
}
```

---

## 测试验证

### 测试用例1: 基本流程
1. 上传一个简单PSD（2-3个文本层）
2. 在Canvas上看到文字渲染
3. 拖拽移动文字
4. 导出PSD
5. 用Photoshop打开，验证位置是否正确

### 测试用例2: 文本编辑
1. 双击文本层
2. 修改内容："Hello" → "World"
3. 修改字体大小：24 → 36
4. 导出并用PS验证

### 测试用例3: 跨平台
1. 在Windows上测试
2. 在Linux上测试（如果有环境）
3. 验证Node服务和Python服务都能正常运行

---

## 成功标准

✅ 能够上传PSD并在Canvas上看到图层  
✅ 能够拖拽移动文本层  
✅ 能够编辑文字内容  
✅ 导出的PSD能在Photoshop中正常打开  
✅ 修改的内容在Photoshop中保持正确  

达到以上标准即可进入下一阶段（添加自动化功能）

---

## 风险预案

### 问题1: ag-psd无法解析某些PSD
**原因**：PSD使用了不支持的特性（如CMYK、16位色深）  
**方案**：先限制只支持RGB 8位PSD，添加上传前检测

### 问题2: 字体缺失
**原因**：服务器没有用户使用的字体  
**方案**：使用系统默认字体替代，提示用户安装字体

### 问题3: Canvas渲染卡顿
**原因**：PSD图层太多（>100层）  
**方案**：只渲染可见图层，使用虚拟滚动

---

## 下一步（Day 3+）

MVP完成后，逐步添加：
1. 一键翻译（调用现有API）
2. 一键改尺寸（规则引擎版本）
3. 图层面板增强（拖拽排序、显示/隐藏）
4. 属性面板（字体选择、颜色选择）
5. 智能对象展开
6. 打包为跨平台可执行文件
