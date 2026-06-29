# PSD编辑器 - 前端开发文档

## 项目定位
基于Photopea架构思想，在浏览器中实现完整的PSD编辑功能

## 核心架构

### 技术选型
- **PSD处理**: ag-psd (npm包，浏览器运行)
- **Canvas渲染**: Fabric.js 或 原生Canvas API
- **状态管理**: Zustand (已有)
- **UI框架**: React 18 (已有)
- **构建工具**: Vite (已有)

### 数据流
```
用户上传PSD
    ↓
浏览器 FileReader → ArrayBuffer
    ↓
ag-psd.readPsd() → Psd对象
    ↓
提取图层信息 → Zustand Store
    ↓
Fabric.js渲染 → Canvas画布
    ↓
用户编辑 (拖拽/修改文字)
    ↓
更新Zustand Store
    ↓
ag-psd.writePsdBuffer() → 新PSD ArrayBuffer
    ↓
下载到本地 或 上传到后端
```

## 依赖安装

### 新增依赖
```bash
cd frontend
npm install ag-psd        # PSD解析/导出
npm install fabric        # Canvas编辑器 (可选，或用原生Canvas)
```

### 依赖体积
- ag-psd: ~200KB (gzipped)
- fabric: ~200KB (gzipped)
- **总增加**: ~400KB (用户浏览器下载，不影响后端)


## 目录结构

```
frontend/src/apps/
└── psd-editor/
    ├── PsdEditorApp.tsx          # 主应用入口
    ├── store.ts                  # Zustand状态管理
    ├── types.ts                  # TypeScript类型定义
    ├── components/
    │   ├── Canvas.tsx            # Canvas画布组件
    │   ├── LayerPanel.tsx        # 图层面板
    │   ├── PropertyPanel.tsx     # 属性编辑面板
    │   ├── Toolbar.tsx           # 工具栏
    │   └── UploadZone.tsx        # PSD上传区
    ├── lib/
    │   ├── psd-parser.ts         # PSD解析逻辑
    │   ├── psd-exporter.ts       # PSD导出逻辑
    │   └── canvas-renderer.ts    # Canvas渲染逻辑
    └── hooks/
        ├── usePsdProject.ts      # PSD项目管理
        └── useLayerEdit.ts       # 图层编辑逻辑
```

## 核心类型定义

```typescript
// types.ts
export interface PsdProject {
  id: string;
  name: string;
  width: number;
  height: number;
  layers: LayerData[];
  rawPsd: any;  // 保存原始Psd对象用于导出
}

export interface LayerData {
  id: string;
  name: string;
  type: 'text' | 'image' | 'shape' | 'group';
  visible: boolean;
  opacity: number;
  blendMode: string;
  
  // 位置和尺寸
  left: number;
  top: number;
  width: number;
  height: number;
  
  // 文本层特有
  text?: {
    content: string;
    font: string;
    fontSize: number;
    color: string;
    align: 'left' | 'center' | 'right';
  };
  
  // 图片层
  imageData?: {
    dataUrl: string;  // base64
  };
}
```


## 核心实现示例

### 1. PSD解析 (lib/psd-parser.ts)

```typescript
import { readPsd } from 'ag-psd';

export async function parsePsdFile(file: File): Promise<PsdProject> {
  // 1. 读取文件为ArrayBuffer
  const arrayBuffer = await file.arrayBuffer();
  
  // 2. 使用ag-psd解析
  const psd = readPsd(arrayBuffer);
  
  // 3. 提取图层信息
  const layers: LayerData[] = [];
  
  function extractLayer(layer: any): void {
    const layerData: LayerData = {
      id: generateId(),
      name: layer.name || 'Unnamed',
      type: detectLayerType(layer),
      visible: !layer.hidden,
      opacity: (layer.opacity || 255) / 255,
      blendMode: layer.blendMode || 'normal',
      left: layer.left || 0,
      top: layer.top || 0,
      width: (layer.right || 0) - (layer.left || 0),
      height: (layer.bottom || 0) - (layer.top || 0),
    };
    
    // 文本层
    if (layer.text) {
      layerData.text = {
        content: layer.text.text || '',
        font: layer.text.style?.font || 'Arial',
        fontSize: layer.text.style?.fontSize || 12,
        color: rgbToHex(layer.text.style?.fillColor),
        align: layer.text.paragraphStyle?.align || 'left',
      };
    }
    
    // 图片层 - 转换为base64
    if (layer.canvas) {
      layerData.imageData = {
        dataUrl: layer.canvas.toDataURL('image/png'),
      };
    }
    
    layers.push(layerData);
    
    // 递归处理子图层
    if (layer.children) {
      layer.children.forEach(extractLayer);
    }
  }
  
  if (psd.children) {
    psd.children.forEach(extractLayer);
  }
  
  return {
    id: generateId(),
    name: file.name.replace('.psd', ''),
    width: psd.width,
    height: psd.height,
    layers,
    rawPsd: psd,  // 保存原始对象
  };
}
```

### 2. PSD导出 (lib/psd-exporter.ts)

```typescript
import { writePsdBuffer } from 'ag-psd';

export async function exportPsd(project: PsdProject): Promise<Blob> {
  // 1. 克隆原始PSD对象
  const psd = JSON.parse(JSON.stringify(project.rawPsd));
  
  // 2. 应用用户的修改
  applyLayerChanges(psd, project.layers);
  
  // 3. 使用ag-psd导出
  const buffer = writePsdBuffer(psd, {
    invalidateTextLayers: true,  // 重建文本层
    generateThumbnail: true,
    trimImageData: true,
  });
  
  // 4. 转换为Blob
  return new Blob([buffer], { type: 'application/octet-stream' });
}

function applyLayerChanges(psd: any, layers: LayerData[]): void {
  // 遍历PSD图层树，应用修改
  const layerMap = new Map(layers.map(l => [l.name, l]));
  
  function traverse(layer: any) {
    const layerData = layerMap.get(layer.name);
    if (layerData) {
      // 更新基础属性
      layer.hidden = !layerData.visible;
      layer.opacity = Math.round(layerData.opacity * 255);
      
      // 更新位置
      layer.left = layerData.left;
      layer.top = layerData.top;
      layer.right = layerData.left + layerData.width;
      layer.bottom = layerData.top + layerData.height;
      
      // 更新文本内容
      if (layerData.text && layer.text) {
        layer.text.text = layerData.text.content;
        if (layer.text.style) {
          layer.text.style.font = layerData.text.font;
          layer.text.style.fontSize = layerData.text.fontSize;
        }
      }
    }
    
    if (layer.children) {
      layer.children.forEach(traverse);
    }
  }
  
  if (psd.children) {
    psd.children.forEach(traverse);
  }
}

export function downloadPsd(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```


### 3. 状态管理 (store.ts)

```typescript
import { create } from 'zustand';

interface PsdEditorState {
  project: PsdProject | null;
  selectedLayerId: string | null;
  mode: 'select' | 'text' | 'move';
  zoom: number;
  
  loadProject: (project: PsdProject) => void;
  updateLayer: (layerId: string, changes: Partial<LayerData>) => void;
  selectLayer: (layerId: string | null) => void;
  setMode: (mode: PsdEditorState['mode']) => void;
  setZoom: (zoom: number) => void;
  exportProject: () => Promise<void>;
}

export const usePsdEditorStore = create<PsdEditorState>((set, get) => ({
  project: null,
  selectedLayerId: null,
  mode: 'select',
  zoom: 1,
  
  loadProject: (project) => set({ project, selectedLayerId: null }),
  
  updateLayer: (layerId, changes) => set(state => {
    if (!state.project) return state;
    
    return {
      project: {
        ...state.project,
        layers: state.project.layers.map(layer =>
          layer.id === layerId ? { ...layer, ...changes } : layer
        ),
      },
    };
  }),
  
  selectLayer: (layerId) => set({ selectedLayerId: layerId }),
  setMode: (mode) => set({ mode }),
  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),
  
  exportProject: async () => {
    const { project } = get();
    if (!project) return;
    
    const { exportPsd, downloadPsd } = await import('./lib/psd-exporter');
    const blob = await exportPsd(project);
    downloadPsd(blob, `${project.name}_edited.psd`);
  },
}));
```

### 4. Canvas组件 (components/Canvas.tsx)

```typescript
import { useEffect, useRef } from 'react';
import { Canvas as FabricCanvas, FabricText, FabricImage } from 'fabric';
import { usePsdEditorStore } from '../store';

export function Canvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<FabricCanvas | null>(null);
  
  const project = usePsdEditorStore(state => state.project);
  const selectedLayerId = usePsdEditorStore(state => state.selectedLayerId);
  const updateLayer = usePsdEditorStore(state => state.updateLayer);
  const selectLayer = usePsdEditorStore(state => state.selectLayer);
  const zoom = usePsdEditorStore(state => state.zoom);
  
  // 初始化Fabric Canvas
  useEffect(() => {
    if (!canvasRef.current || fabricRef.current) return;
    
    const canvas = new FabricCanvas(canvasRef.current, {
      width: 800,
      height: 600,
      backgroundColor: '#f0f0f0',
    });
    
    fabricRef.current = canvas;
    
    // 监听对象修改
    canvas.on('object:modified', (e) => {
      const obj = e.target;
      const layerId = obj.data?.layerId;
      
      if (layerId) {
        updateLayer(layerId, {
          left: obj.left || 0,
          top: obj.top || 0,
        });
      }
    });
    
    // 监听选择
    canvas.on('selection:created', (e) => {
      const obj = e.selected?.[0];
      if (obj?.data?.layerId) {
        selectLayer(obj.data.layerId);
      }
    });
    
    return () => {
      canvas.dispose();
      fabricRef.current = null;
    };
  }, []);
  
  // 渲染图层
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas || !project) return;
    
    canvas.clear();
    canvas.setDimensions({
      width: project.width * zoom,
      height: project.height * zoom,
    });
    
    // 渲染每个图层
    project.layers.forEach(layer => {
      if (!layer.visible) return;
      
      if (layer.type === 'text' && layer.text) {
        const text = new FabricText(layer.text.content, {
          left: layer.left * zoom,
          top: layer.top * zoom,
          fontSize: layer.text.fontSize * zoom,
          fontFamily: layer.text.font,
          fill: layer.text.color,
        });
        
        text.data = { layerId: layer.id };
        canvas.add(text);
      }
    });
    
    canvas.renderAll();
  }, [project, zoom]);
  
  return <canvas ref={canvasRef} />;
}
```


### 5. 主应用入口 (PsdEditorApp.tsx)

```typescript
import { useState } from 'react';
import { AppLayout } from '@/AppLayout';
import { usePsdEditorStore } from './store';
import { parsePsdFile } from './lib/psd-parser';
import { Canvas } from './components/Canvas';
import { LayerPanel } from './components/LayerPanel';
import { PropertyPanel } from './components/PropertyPanel';

export function PsdEditorApp() {
  const [loading, setLoading] = useState(false);
  const project = usePsdEditorStore(state => state.project);
  const loadProject = usePsdEditorStore(state => state.loadProject);
  const exportProject = usePsdEditorStore(state => state.exportProject);
  
  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.psd')) {
      alert('请上传PSD文件');
      return;
    }
    
    setLoading(true);
    try {
      const project = await parsePsdFile(file);
      loadProject(project);
    } catch (error) {
      console.error('解析PSD失败:', error);
      alert('解析PSD文件失败');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <AppLayout>
      <div className="psd-editor-app">
        <div className="psd-editor-header">
          <h1>PSD 编辑器</h1>
          <div className="psd-editor-actions">
            <label className="upload-btn">
              选择PSD文件
              <input
                type="file"
                accept=".psd"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
                style={{ display: 'none' }}
              />
            </label>
            
            {project && (
              <button onClick={() => exportProject()}>
                导出PSD
              </button>
            )}
          </div>
        </div>
        
        {loading && <div>正在解析PSD文件...</div>}
        
        {project && (
          <div className="psd-editor-workspace">
            <div className="psd-editor-left">
              <LayerPanel />
            </div>
            
            <div className="psd-editor-center">
              <Canvas />
            </div>
            
            <div className="psd-editor-right">
              <PropertyPanel />
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
```

## 集成到现有项目

### 1. 注册应用路由

```typescript
// frontend/src/appRegistry.tsx
import { PsdEditorApp } from '@/apps/psd-editor/PsdEditorApp';

export const appRegistry: RegisteredApp[] = [
  // ... 现有应用
  { 
    id: 'psd-editor', 
    label: 'PSD编辑器', 
    title: 'PSD编辑器', 
    icon: APP_ICON_PATHS.psdEditor,
    component: PsdEditorApp, 
    status: 'beta' 
  },
];
```

### 2. 添加样式

```css
/* frontend/src/styles/mediatools/psd-editor.css */

.psd-editor-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #2b2b2b;
  color: #fff;
}

.psd-editor-header {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #1e1e1e;
  border-bottom: 1px solid #3e3e3e;
}

.psd-editor-workspace {
  display: grid;
  grid-template-columns: 250px 1fr 300px;
  flex: 1;
  overflow: hidden;
}

.psd-editor-left,
.psd-editor-right {
  background: #252525;
  overflow-y: auto;
}

.psd-editor-center {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b2b2b;
}

.upload-btn {
  padding: 0.5rem 1rem;
  background: #0066ff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
```

## 开发步骤

### Phase 1: 基础框架 (2小时)
1. 安装依赖: `npm install ag-psd fabric`
2. 创建目录结构
3. 实现基础组件框架

### Phase 2: PSD解析 (3小时)
1. 实现 `psd-parser.ts`
2. 测试不同PSD文件的解析
3. 处理边界情况

### Phase 3: Canvas渲染 (4小时)
1. 集成Fabric.js
2. 渲染文本层和图片层
3. 实现选择和拖拽

### Phase 4: 编辑功能 (4小时)
1. 文本编辑
2. 属性修改
3. 图层显示/隐藏

### Phase 5: PSD导出 (3小时)
1. 实现 `psd-exporter.ts`
2. 应用用户修改
3. 测试兼容性

### Phase 6: UI优化 (2小时)
1. 美化界面
2. 添加快捷键
3. 性能优化

**总计**: 18小时 (约3个工作日)

## 测试验证

### 测试用例1: 基础流程
1. 上传简单PSD (2-3个文本层)
2. 验证Canvas正确渲染
3. 修改文字内容
4. 导出PSD
5. 用Photoshop打开验证

### 测试用例2: 复杂PSD
1. 上传包含智能对象的PSD
2. 验证图层树正确解析
3. 编辑图层
4. 导出验证

### 测试用例3: 性能测试
1. 上传100+图层的PSD
2. 验证渲染性能 (<2秒加载)
3. 编辑操作流畅 (>30fps)

## 后端集成 (可选)

如果需要云端存储:

```typescript
// 上传到后端
async function saveToCloud(project: PsdProject): Promise<string> {
  const blob = await exportPsd(project);
  const formData = new FormData();
  formData.append('file', blob, `${project.name}.psd`);
  
  const response = await fetch('/api/psd/save', {
    method: 'POST',
    body: formData,
  });
  
  return response.json().then(data => data.project_id);
}

// 从后端加载
async function loadFromCloud(projectId: string): Promise<PsdProject> {
  const response = await fetch(`/api/psd/load/${projectId}`);
  const blob = await response.blob();
  const file = new File([blob], 'project.psd');
  return parsePsdFile(file);
}
```

## 优化建议

### 性能优化
1. **惰性渲染**: 只渲染可见图层
2. **Web Worker**: 在Worker中解析大PSD
3. **虚拟滚动**: 图层列表使用虚拟滚动
4. **缓存**: 缓存图层缩略图

### 功能增强
1. **Undo/Redo**: 使用immer管理历史栈
2. **快捷键**: Ctrl+Z/Y, Delete删除图层
3. **预设**: 常用字体/颜色快速选择
4. **批量操作**: 选中多个图层批量修改

## 常见问题

### Q1: ag-psd无法解析某些PSD?
**A**: 可能原因:
- CMYK色彩模式 (只支持RGB)
- 16位色深 (只支持8位)
- 使用了不支持的新特性

**解决**: 提示用户在Photoshop中转换为RGB/8位

### Q2: 导出的PSD在PS中打开出错?
**A**: 检查:
- 是否设置了 `invalidateTextLayers: true`
- 文本层是否有特殊字符
- 图层名称是否包含非法字符

### Q3: 大PSD文件浏览器卡顿?
**A**: 优化方案:
- 限制上传文件大小 (<100MB)
- 使用Web Worker解析
- 实现虚拟滚动

## 核心优势

### 与后端方案对比
| 维度 | 前端方案 | 后端方案 |
|------|---------|---------|
| 依赖 | npm包 (浏览器) | Node.js服务 |
| 体积 | 0 (后端不增加) | +15MB |
| 性能 | 快 (本地处理) | 慢 (网络传输) |
| 跨平台 | ✅ 浏览器 | ✅ 但需双打包 |
| 维护 | 低 (纯前端) | 高 (两套服务) |

### 符合项目重构原则
- ✅ **小巧精悍**: 后端零依赖增加
- ✅ **跨平台**: 浏览器天然跨平台
- ✅ **模块化**: 前端独立功能模块
- ✅ **易维护**: 单一技术栈

## 参考资源

- [ag-psd GitHub](https://github.com/Agamnentzar/ag-psd)
- [Fabric.js 文档](https://fabricjs.com/docs/)
- [Photopea](https://www.photopea.com/) - 参考UI设计
- [psCrx源码](C:\psCrx) - 可复用部分代码

---

**最后更新**: 2026-06-29  
**状态**: 设计文档，待前端团队实施  
**预计工时**: 18小时 (3个工作日)
