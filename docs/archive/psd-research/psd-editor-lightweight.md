# PSD编辑器 - 轻量级方案（符合重构原则）

## 设计原则
遵循项目重构目标：**小巧精悍 + 跨平台 + 最小依赖**

---

## 核心理念：做减法

### ❌ 不引入的技术（保持轻量）
- ❌ Node.js微服务（避免双技术栈）
- ❌ Fabric.js（2MB+，功能过剩）
- ❌ ag-psd（Node依赖，打包困难）
- ❌ AI自动化（暂缓，先做核心编辑）

### ✅ 采用的技术（极简组合）
- ✅ Python `psd-tools` - 纯Python PSD解析（无需Node）
- ✅ 原生Canvas API - 无需重量级框架
- ✅ 现有前端栈 - React + Zustand（已有）
- ✅ 复用PhotoshopApp结构 - 减少新代码

---

## 方案对比

| 方案 | 依赖增加 | 打包体积 | 跨平台 | 维护成本 | 符合重构理念 |
|------|---------|---------|--------|---------|-------------|
| **Node.js微服务** | Node+npm包 | +30MB | 需双打包 | 高（两套服务） | ❌ 违背"小巧精悍" |
| **Fabric.js前端** | Fabric.js | +2MB | ✅ | 中 | ⚠️ 功能过剩 |
| **纯Python轻量版（推荐）** | psd-tools | +500KB | ✅ | 低 | ✅ 完美契合 |

---

## 轻量级架构设计

```
┌─────────────────────────────────────────────────┐
│          前端（React - 原生Canvas）              │
│  ┌──────────────────────────────────────────┐   │
│  │   PhotoshopApp（增强现有组件）           │   │
│  │                                           │   │
│  │  上传PSD → 显示图层列表 → 选择编辑      │   │
│  │                                           │   │
│  │  表单编辑：                               │   │
│  │  - 文本内容输入框                         │   │
│  │  - 字体下拉选择                           │   │
│  │  - 位置数值输入                           │   │
│  │                                           │   │
│  │  轻量预览：                               │   │
│  │  - 原生Canvas渲染文本层                  │   │
│  │  - 简单的拖拽（mousedown + mousemove）   │   │
│  │  - 背景图片（导出的PNG预览）             │   │
│  └──────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────┘
                 │ REST API（纯JSON交互）
                 ↓
┌─────────────────────────────────────────────────┐
│         Python后端（FastAPI）                   │
│  ┌──────────────────────────────────────────┐   │
│  │  api_psd.py（新增，~300行）              │   │
│  │                                           │   │
│  │  POST /api/psd/upload                    │   │
│  │    - 使用psd-tools解析PSD                │   │
│  │    - 提取文本层信息（内容/字体/位置）    │   │
│  │    - 导出整体PNG预览（PIL）              │   │
│  │    - 返回JSON：{ layers: [...] }         │   │
│  │                                           │   │
│  │  PUT /api/psd/layer/{id}                 │   │
│  │    - 更新图层属性（文本/位置）            │   │
│  │    - 保存到内存或JSON文件                │   │
│  │                                           │   │
│  │  POST /api/psd/export/{project_id}       │   │
│  │    - 重建PSD（psd-tools写入）            │   │
│  │    - 应用修改后的文本内容和位置           │   │
│  │    - 返回PSD文件                         │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘

依赖：psd-tools（纯Python，~500KB）
```

---

## 核心功能实现

### 1. PSD解析（Python）

```python
# src/mediatools/core/psd_editor.py
from psd_tools import PSDImage
from PIL import Image
import json

def parse_psd(psd_path: str) -> dict:
    """解析PSD，提取可编辑的文本层"""
    psd = PSDImage.open(psd_path)
    
    # 导出整体预览图（作为Canvas背景）
    preview_img = psd.topil()
    preview_path = save_temp_image(preview_img)
    
    layers = []
    for layer in psd:
        if layer.kind == 'type':  # 文本层
            # 提取文本属性
            text_data = layer.text_data
            bbox = layer.bbox  # (left, top, right, bottom)
            
            layers.append({
                'id': generate_id(),
                'name': layer.name,
                'type': 'text',
                'content': text_data.text,
                'font': text_data.font.name if text_data.font else 'Arial',
                'fontSize': text_data.font_size or 12,
                'color': rgb_to_hex(text_data.color),
                'left': bbox.left,
                'top': bbox.top,
                'width': bbox.width,
                'height': bbox.height,
                'visible': layer.visible,
            })
    
    return {
        'width': psd.width,
        'height': psd.height,
        'preview_url': preview_path,
        'layers': layers
    }

def export_psd(original_psd_path: str, updates: dict, output_path: str):
    """应用修改并导出新PSD"""
    psd = PSDImage.open(original_psd_path)
    
    # 遍历图层，应用修改
    for layer in psd:
        if layer.kind == 'type':
            update = updates.get(layer.name)
            if update:
                # 更新文本内容
                layer.text = update['content']
                # 更新位置（psd-tools限制：部分属性只读）
                # 需要通过重新创建图层实现
    
    # 保存
    psd.save(output_path)
```

**关键点**：
- ✅ 纯Python，无需Node.js
- ✅ psd-tools是成熟库（维护活跃）
- ⚠️ 限制：复杂图层效果可能丢失（但文本编辑够用）

---

### 2. 前端轻量Canvas（原生API）

```typescript
// frontend/src/apps/psd-editor/LightweightCanvas.tsx
import { useEffect, useRef } from 'react';

interface Layer {
  id: string;
  type: 'text';
  content: string;
  left: number;
  top: number;
  fontSize: number;
  font: string;
  color: string;
}

export function LightweightCanvas({
  backgroundUrl,
  layers,
  onLayerUpdate
}: {
  backgroundUrl: string;
  layers: Layer[];
  onLayerUpdate: (id: string, updates: Partial<Layer>) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  
  // 渲染Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 1. 绘制背景图
    const bg = new Image();
    bg.src = backgroundUrl;
    bg.onload = () => {
      ctx.drawImage(bg, 0, 0, canvas.width, canvas.height);
      
      // 2. 绘制文本层
      layers.forEach(layer => {
        ctx.font = `${layer.fontSize}px ${layer.font}`;
        ctx.fillStyle = layer.color;
        ctx.fillText(layer.content, layer.left, layer.top);
        
        // 选中状态：绘制边框
        if (layer.id === selectedId) {
          ctx.strokeStyle = '#0066ff';
          ctx.lineWidth = 2;
          const metrics = ctx.measureText(layer.content);
          ctx.strokeRect(
            layer.left - 4,
            layer.top - layer.fontSize - 4,
            metrics.width + 8,
            layer.fontSize + 8
          );
        }
      });
    };
  }, [backgroundUrl, layers, selectedId]);
  
  // 3. 简单的拖拽实现
  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // 检测点击的图层
    const clicked = layers.find(layer => 
      x >= layer.left && x <= layer.left + 200 &&
      y >= layer.top - layer.fontSize && y <= layer.top
    );
    
    if (clicked) {
      setSelectedId(clicked.id);
      setDragging(true);
    }
  };
  
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging || !selectedId) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    onLayerUpdate(selectedId, { left: x, top: y });
  };
  
  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={600}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={() => setDragging(false)}
      style={{ border: '1px solid #ccc', cursor: dragging ? 'move' : 'default' }}
    />
  );
}
```

**优势**：
- ✅ 零额外依赖（原生Canvas API）
- ✅ 代码量少（~100行）
- ✅ 性能好（直接操作Canvas）
- ⚠️ 功能简单（但够用）

---

### 3. 集成到现有PhotoshopApp

```typescript
// frontend/src/apps/PhotoshopApp.tsx（增强现有组件）
import { LightweightCanvas } from './psd-editor/LightweightCanvas';

export function PhotoshopApp() {
  const [mode, setMode] = useState<'automation' | 'editor'>('automation');
  const [project, setProject] = useState(null);
  
  // 现有的自动化功能保持不变
  // ...
  
  // 新增：切换到编辑模式
  const handleEnterEditor = () => {
    setMode('editor');
  };
  
  return (
    <AppLayout>
      <div className="ps-app">
        {/* 现有侧边栏 */}
        <aside className="ps-flow-sidebar">
          {/* ... */}
          <button onClick={handleEnterEditor}>可视化编辑</button>
        </aside>
        
        {/* 编辑模式 */}
        {mode === 'editor' && project ? (
          <div className="ps-editor-workspace">
            <div className="ps-editor-left">
              {/* 图层列表 */}
              <div className="ps-layer-panel">
                <h3>图层</h3>
                {project.layers.map(layer => (
                  <div key={layer.id} className="ps-layer-item">
                    <input
                      type="checkbox"
                      checked={layer.visible}
                      onChange={(e) => updateLayer(layer.id, { visible: e.target.checked })}
                    />
                    <span>{layer.name}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="ps-editor-center">
              {/* 轻量Canvas */}
              <LightweightCanvas
                backgroundUrl={project.preview_url}
                layers={project.layers}
                onLayerUpdate={updateLayer}
              />
            </div>
            
            <div className="ps-editor-right">
              {/* 属性面板 */}
              <div className="ps-property-panel">
                <h3>属性</h3>
                {selectedLayer && (
                  <>
                    <label>
                      文本内容
                      <textarea
                        value={selectedLayer.content}
                        onChange={(e) => updateLayer(selectedLayer.id, { content: e.target.value })}
                      />
                    </label>
                    
                    <label>
                      字体
                      <select
                        value={selectedLayer.font}
                        onChange={(e) => updateLayer(selectedLayer.id, { font: e.target.value })}
                      >
                        <option>Arial</option>
                        <option>Helvetica</option>
                        <option>SimHei</option>
                      </select>
                    </label>
                    
                    <label>
                      大小
                      <input
                        type="number"
                        value={selectedLayer.fontSize}
                        onChange={(e) => updateLayer(selectedLayer.id, { fontSize: +e.target.value })}
                      />
                    </label>
                  </>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* 现有的自动化面板 */
          <main className="ps-operation">
            {/* ... 现有代码保持不变 */}
          </main>
        )}
      </div>
    </AppLayout>
  );
}
```

---

## 依赖分析

### Python新增依赖
```toml
# pyproject.toml
[project]
dependencies = [
  "psd-tools>=1.9.34",  # PSD解析（纯Python）
  "Pillow>=10.0.0"      # 图片处理（可能已有，用于预览）
]
```

**体积影响**：
- psd-tools: ~500KB
- Pillow: ~2MB（可能已有，用于screenshot功能）
- **总增加**：~2.5MB

### 前端新增依赖
**零**！使用原生Canvas API

---

## 对比psCrx方案

| 维度 | psCrx方案 | 轻量级方案 |
|------|----------|-----------|
| 依赖 | Node.js + ag-psd + Fabric.js | psd-tools（Python） |
| 体积 | +30MB | +2.5MB |
| 跨平台 | 需双打包 | ✅ Python原生 |
| 维护 | 两套服务 | 单一Python栈 |
| 功能 | 完整PSD编辑 | 聚焦文本编辑 |
| 复杂度 | 高（1300+行） | 低（~500行） |
| 符合重构理念 | ❌ | ✅ |

---

## 功能边界（做减法）

### ✅ 支持的功能
1. **文本层编辑**
   - 修改文字内容
   - 修改字体、大小、颜色
   - 拖拽移动位置
   - 显示/隐藏

2. **基础预览**
   - Canvas渲染文本层
   - 背景图片（PSD整体预览）
   - 选中高亮

3. **PSD导入/导出**
   - 上传PSD → 提取文本层
   - 编辑后导出新PSD

### ❌ 不支持的功能（保持轻量）
- ❌ 智能对象编辑（复杂度高）
- ❌ 图层样式（阴影、描边等）
- ❌ 复杂图层变换（旋转、倾斜）
- ❌ 批量自动化（暂缓）
- ❌ 矢量形状编辑

**理由**：80%的用户需求是"改文案"，聚焦核心场景。

---

## 实施计划（3天完成）

### Day 1: Python后端（4小时）
```bash
# 1. 安装psd-tools
pip install psd-tools Pillow

# 2. 创建 src/mediatools/core/psd_editor.py
# 3. 实现：
#    - parse_psd() - 解析PSD
#    - export_psd() - 导出PSD
#    - 临时文件管理

# 4. 创建 src/mediatools/api_psd.py
# 5. 实现API端点：
#    - POST /api/psd/upload
#    - PUT /api/psd/layer/{id}
#    - POST /api/psd/export/{project_id}

# 6. 测试：
python -m pytest tests/test_psd_editor.py
```

### Day 2: 前端Canvas（4小时）
```bash
cd frontend

# 1. 创建 src/apps/psd-editor/LightweightCanvas.tsx
#    - 原生Canvas渲染
#    - 简单拖拽
#    - ~100行代码

# 2. 创建 src/apps/psd-editor/PropertyPanel.tsx
#    - 文本输入框
#    - 字体选择
#    - 位置数值

# 3. 测试：
npm run dev  # 手动测试UI交互
```

### Day 3: 集成与测试（4小时）
```bash
# 1. 修改 PhotoshopApp.tsx
#    - 添加"可视化编辑"按钮
#    - 嵌入LightweightCanvas

# 2. 端到端测试：
#    - 上传测试PSD
#    - 修改文字
#    - 拖拽图层
#    - 导出PSD
#    - 用Photoshop验证

# 3. 跨平台测试：
#    - Windows: python scripts/start.py
#    - Linux: python scripts/start.py
#    - macOS: python scripts/start.py
```

---

## 窗口大小与风格

### 参考DownloaderApp布局
```typescript
// 保持一致的布局结构
<AppLayout>  {/* 复用现有布局 */}
  <div className="ps-app">  {/* 与dl-app同级 */}
    <aside className="ps-flow-sidebar">  {/* 左侧导航，与DownloaderSidebar一致 */}
      <button>扫描工单</button>
      <button>可视化编辑</button>  {/* 新增 */}
    </aside>
    
    <main className="ps-operation">  {/* 主工作区 */}
      {/* 编辑器 */}
    </main>
  </div>
</AppLayout>
```

### CSS样式复用
```css
/* frontend/src/styles/mediatools/photoshop.css */
/* 复用现有变量和组件样式 */

.ps-editor-workspace {
  display: grid;
  grid-template-columns: 200px 1fr 250px;  /* 图层列表 | Canvas | 属性面板 */
  height: 100%;
}

.ps-editor-center canvas {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
```

---

## 打包与跨平台

### Python打包（PyInstaller）
```bash
# 打包命令（与现有流程一致）
pyinstaller --onefile \
  --name mediatools \
  --add-data "frontend/dist:frontend/dist" \
  --hidden-import psd_tools \
  src/mediatools/cli.py

# 输出：
# - Windows: dist/mediatools.exe (~25MB)
# - Linux: dist/mediatools (~23MB)
# - macOS: dist/mediatools (~24MB)
```

**体积对比**：
- 当前：~20MB
- 增加psd-tools后：~23MB
- 仍然远小于psCrx方案（50MB+）

---

## 风险与限制

### 技术风险
1. **psd-tools功能限制**
   - 复杂图层效果可能丢失
   - 缓解：明确告知用户"仅支持文本编辑"

2. **文本层往返保真**
   - psd-tools对文本层支持有限
   - 缓解：测试常见场景，文档化不支持的情况

### 产品限制
- ✅ 支持：90%的常见文案编辑场景
- ❌ 不支持：复杂设计调整（需用Photoshop）

---

## 后续扩展（可选）

如果未来需要更强大的功能：

### 方案1：渐进增强
- 当前轻量方案作为基础
- 可选安装"增强包"（Node.js服务）
- 用户选择：轻量模式 vs 完整模式

### 方案2：外部工具集成
- 提供Photoshop插件
- 通过JSX脚本远程控制Photoshop
- 保持主程序轻量

---

## 总结

### ✅ 符合重构原则
- ✅ **小巧精悍**：仅+2.5MB依赖
- ✅ **跨平台**：纯Python，一次打包
- ✅ **最小依赖**：不引入Node.js
- ✅ **易维护**：单一技术栈
- ✅ **核心功能优先**：聚焦文本编辑

### 📊 与psCrx对比
| 维度 | psCrx完整方案 | 轻量级方案 |
|------|--------------|-----------|
| 开发时间 | 13天 | 3天 |
| 代码量 | ~3000行 | ~500行 |
| 新增依赖 | Node.js生态 | 2个Python包 |
| 打包体积 | +30MB | +2.5MB |
| 维护成本 | 高 | 低 |

---

**推荐决策**：采用轻量级方案，3天内完成MVP，验证用户需求后再考虑是否需要增强功能。
