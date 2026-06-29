# PSD编辑工作台 - 完整技术架构

## 产品定位
**批量自动化 + 可视化微调** 的双模式PSD编辑工具

---

## 核心功能

### 模式1：自动化批量处理（快速）
- ✅ 一键翻译（AI批量翻译所有文本层）
- ✅ 一键改尺寸（智能重排布局）
- ✅ 批量模板替换
- ✅ 批量导出（多语言、多尺寸）

### 模式2：可视化编辑器（精细调整）
- ✅ 文本编辑（内容、字体、大小、颜色）
- ✅ 图层变换（移动、缩放、旋转）
- ✅ 智能对象编辑（展开内部图层）
- ✅ 图层管理（显示/隐藏、锁定、删除）
- ✅ 实时预览

---

## 技术栈

### 前端
- **UI框架**: React 18 + TypeScript
- **Canvas渲染**: Fabric.js 6.4（已在psCrx验证）
- **状态管理**: Zustand（已有）
- **UI组件**: 复用现有AppLayout + 新增编辑器组件

### 后端
- **Python主服务**: FastAPI（已有）
  - 任务编排、文件管理、AI翻译
- **Node.js微服务**: Express + ag-psd
  - PSD解析/导出、图层数据转换

### 数据流
```
PSD文件 → Node服务解析 → 图层JSON → 前端Fabric渲染
         ↓
用户编辑 → Canvas操作 → 图层JSON → Node服务重建 → 新PSD
```

---

## 架构设计

### 整体架构图
```
┌─────────────────────────────────────────────────────────┐
│                    前端（React）                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │           PhotoshopEditorApp（新增）               │ │
│  │                                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ 自动化面板   │  │ 可视化编辑器 │               │ │
│  │  │              │  │              │               │ │
│  │  │ • 一键翻译   │  │ Canvas画布   │               │ │
│  │  │ • 一键改尺寸 │  │ (Fabric.js)  │               │ │
│  │  │ • 批量导出   │  │              │               │ │
│  │  └──────────────┘  └──────────────┘               │ │
│  │                                                     │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │          图层面板 + 属性面板                │  │ │
│  │  │  • 图层列表  • 文本属性  • 变换属性        │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API + WebSocket
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Python后端（FastAPI）                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  /api/psd/upload        - 上传PSD                 │ │
│  │  /api/psd/parse         - 解析为图层JSON          │ │
│  │  /api/psd/translate     - AI批量翻译              │ │
│  │  /api/psd/resize        - 自动改尺寸              │ │
│  │  /api/psd/export        - 导出PSD                 │ │
│  │  /ws/psd/preview        - 实时预览推送            │ │
│  └────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │ 内部HTTP调用
                        ↓
┌─────────────────────────────────────────────────────────┐
│           Node.js微服务（PSD处理核心）                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  POST /psd/parse                                   │ │
│  │    - 使用ag-psd读取PSD文件                         │ │
│  │    - 提取图层树、文本内容、图片资源                │ │
│  │    - 转换为前端可用的JSON格式                      │ │
│  │                                                     │ │
│  │  POST /psd/export                                  │ │
│  │    - 接收前端编辑后的图层JSON                      │ │
│  │    - 使用ag-psd重建PSD文件结构                     │ │
│  │    - 处理文本层、智能对象、光栅图层                │ │
│  │    - 返回PSD Buffer                                │ │
│  │                                                     │ │
│  │  POST /layers/render                               │ │
│  │    - 渲染单个图层为PNG（用于预览）                 │ │
│  │                                                     │ │
│  │  POST /smartobject/expand                          │ │
│  │    - 展开智能对象内部图层                          │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 数据模型

### PSD图层JSON结构
```typescript
interface PsdProject {
  id: string
  name: string
  width: number
  height: number
  resolution: number  // DPI
  colorMode: 'RGB' | 'CMYK'
  layers: Layer[]
  meta: {
    source_psd: string
    created_at: string
    updated_at: string
  }
}

interface Layer {
  id: string
  type: 'text' | 'image' | 'smartobject' | 'group'
  name: string
  visible: boolean
  locked: boolean
  opacity: number
  blendMode: string
  
  // 位置和尺寸
  left: number
  top: number
  width: number
  height: number
  
  // 文本层特有
  text?: {
    content: string
    font: string
    fontSize: number
    color: string
    align: 'left' | 'center' | 'right'
    lineHeight: number
  }
  
  // 图片层
  imageData?: {
    url: string  // 临时URL
    format: 'png' | 'jpg'
  }
  
  // 智能对象
  smartObject?: {
    innerLayers: Layer[]  // 递归结构
  }
  
  // 变换
  transform?: {
    rotation: number
    scaleX: number
    scaleY: number
  }
}
```

---

## 核心流程

### 流程1：自动化翻译
```
1. 用户上传PSD
   ↓
2. Node服务解析 → 提取文本层
   ↓
3. Python调用AI翻译API
   ↓
4. 更新图层JSON中的text.content
   ↓
5. 前端Canvas自动刷新显示
   ↓
6. 用户点击"导出" → Node服务生成新PSD
```

### 流程2：一键改尺寸
```
1. 用户选择目标尺寸（如1920x1080）
   ↓
2. Python分析图层布局（调用AI或规则引擎）
   ↓
3. 计算新的图层位置和尺寸
   ↓
4. 更新图层JSON
   ↓
5. 前端Canvas实时预览新布局
   ↓
6. 用户确认 → 导出PSD
```

### 流程3：可视化编辑
```
1. 前端加载图层JSON
   ↓
2. Fabric.js渲染所有图层到Canvas
   ↓
3. 用户拖拽文本层 → 更新layer.left/top
   ↓
4. 用户修改文字 → 更新layer.text.content
   ↓
5. 用户缩放图片 → 更新layer.width/height
   ↓
6. 所有修改实时保存到Zustand状态
   ↓
7. 点击"保存" → 发送JSON给Python → 调用Node服务 → 生成PSD
```

### 流程4：智能对象编辑
```
1. 用户双击智能对象图层
   ↓
2. 调用Node服务 /smartobject/expand
   ↓
3. 返回内部图层JSON
   ↓
4. 前端打开"智能对象编辑模式"
   ↓
5. 用户编辑内部图层
   ↓
6. 保存 → 更新父PSD的smartObject.innerLayers
   ↓
7. 导出时Node服务重建智能对象
```

---

## 关键技术实现

### 1. PSD解析（Node.js）
```javascript
// services/psd-service/parse.js
const { readPsd } = require('ag-psd');

function parsePsdToJson(psdBuffer) {
  const psd = readPsd(psdBuffer);
  
  return {
    width: psd.width,
    height: psd.height,
    layers: psd.children.map(layer => parseLayer(layer))
  };
}

function parseLayer(layer) {
  const base = {
    id: generateId(),
    type: detectLayerType(layer),
    name: layer.name,
    left: layer.left,
    top: layer.top,
    width: layer.right - layer.left,
    height: layer.bottom - layer.top,
    visible: !layer.hidden,
    opacity: layer.opacity / 255
  };
  
  // 文本层
  if (layer.text) {
    base.text = {
      content: layer.text.text,
      font: layer.text.style?.font || 'Arial',
      fontSize: layer.text.style?.fontSize || 12,
      color: rgbToHex(layer.text.style?.fillColor)
    };
  }
  
  // 图片层
  if (layer.canvas) {
    const imageUrl = saveLayerAsTemp(layer.canvas);
    base.imageData = { url: imageUrl, format: 'png' };
  }
  
  // 智能对象
  if (layer.smartObject) {
    const innerPsd = readPsd(layer.smartObject.data);
    base.smartObject = {
      innerLayers: innerPsd.children.map(parseLayer)
    };
  }
  
  return base;
}
```

### 2. Canvas渲染（React + Fabric.js）
```typescript
// frontend/src/apps/editor/EditorCanvas.tsx
import { Canvas, FabricText, FabricImage } from 'fabric';
import { useEffect, useRef } from 'react';
import { usePsdStore } from './store';

export function EditorCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<Canvas | null>(null);
  const { layers, updateLayer } = usePsdStore();
  
  useEffect(() => {
    const canvas = new Canvas(canvasRef.current, {
      width: 800,
      height: 600
    });
    fabricRef.current = canvas;
    
    // 监听对象修改
    canvas.on('object:modified', (e) => {
      const obj = e.target;
      const layerId = obj.data?.layerId;
      if (layerId) {
        updateLayer(layerId, {
          left: obj.left,
          top: obj.top,
          width: obj.width * obj.scaleX,
          height: obj.height * obj.scaleY,
          transform: {
            rotation: obj.angle,
            scaleX: obj.scaleX,
            scaleY: obj.scaleY
          }
        });
      }
    });
    
    return () => canvas.dispose();
  }, []);
  
  // 渲染图层
  useEffect(() => {
    if (!fabricRef.current) return;
    
    fabricRef.current.clear();
    
    layers.forEach(layer => {
      if (layer.type === 'text') {
        const text = new FabricText(layer.text.content, {
          left: layer.left,
          top: layer.top,
          fontSize: layer.text.fontSize,
          fontFamily: layer.text.font,
          fill: layer.text.color
        });
        text.data = { layerId: layer.id };
        fabricRef.current.add(text);
      } else if (layer.type === 'image') {
        FabricImage.fromURL(layer.imageData.url).then(img => {
          img.set({
            left: layer.left,
            top: layer.top,
            scaleX: layer.width / img.width,
            scaleY: layer.height / img.height
          });
          img.data = { layerId: layer.id };
          fabricRef.current.add(img);
        });
      }
    });
  }, [layers]);
  
  return <canvas ref={canvasRef} />;
}
```

### 3. 一键翻译（Python）
```python
# src/mediatools/api_psd.py
@router.post("/api/psd/translate")
async def translate_psd(project_id: str, target_language: str):
    # 1. 获取项目数据
    project = await db.get_psd_project(project_id)
    
    # 2. 提取所有文本层
    text_layers = [
        layer for layer in project['layers'] 
        if layer['type'] == 'text'
    ]
    
    # 3. 批量翻译
    texts = [layer['text']['content'] for layer in text_layers]
    translations = await ai_translate_batch(texts, target_language)
    
    # 4. 更新图层数据
    for layer, translated in zip(text_layers, translations):
        layer['text']['content'] = translated
    
    # 5. 保存更新
    await db.update_psd_project(project_id, project)
    
    # 6. 通过WebSocket推送更新
    await broadcast_project_update(project_id, project)
    
    return {"ok": True, "translated_count": len(translations)}
```

### 4. 一键改尺寸（智能重排）
```python
# src/mediatools/core/psd_resize.py
async def smart_resize(project: dict, target_width: int, target_height: int):
    """智能调整PSD尺寸"""
    old_w, old_h = project['width'], project['height']
    scale_x = target_width / old_w
    scale_y = target_height / old_h
    
    # 检测布局方向
    is_portrait = old_h > old_w
    target_is_landscape = target_width > target_height
    need_reflow = is_portrait and target_is_landscape
    
    if need_reflow:
        # 竖版→横版：需要重排布局
        return await reflow_layout(project, target_width, target_height)
    else:
        # 等比缩放
        return scale_layers(project, scale_x, scale_y)

async def reflow_layout(project: dict, target_w: int, target_h: int):
    """使用AI分析布局并重排"""
    layers = project['layers']
    
    # 分类图层
    text_layers = [l for l in layers if l['type'] == 'text']
    image_layers = [l for l in layers if l['type'] == 'image']
    
    # 调用AI分析最佳布局
    prompt = f"""
    原始布局：竖版 {project['width']}x{project['height']}
    目标：横版 {target_w}x{target_h}
    
    图层信息：
    - 文本层：{len(text_layers)}个
    - 图片层：{len(image_layers)}个
    
    请给出新的布局方案（JSON格式）：
    {{
      "text_layers": [{{ "id": "...", "left": 100, "top": 50, "width": 300 }}],
      "image_layers": [...]
    }}
    """
    
    layout = await call_ai(prompt)
    
    # 应用新布局
    for layer in layers:
        new_pos = layout['text_layers' if layer['type'] == 'text' else 'image_layers']
        matching = next((p for p in new_pos if p['id'] == layer['id']), None)
        if matching:
            layer.update(matching)
    
    project['width'] = target_w
    project['height'] = target_h
    return project
```

---

## UI设计

### 主界面布局
```
┌─────────────────────────────────────────────────────────┐
│  PhotoshopEditorApp                    [最小化] [×]     │
├─────────────────────────────────────────────────────────┤
│  [上传PSD] [保存] [导出PSD] [导出PNG]    项目: demo.psd │
├───────────┬─────────────────────────────┬───────────────┤
│           │                             │               │
│  工具栏   │        Canvas画布           │   属性面板    │
│           │    (Fabric.js渲染)          │               │
│  [选择]   │  ┌─────────────────────┐    │  图层名称:    │
│  [文字]   │  │  ┌──────────┐       │    │  [Title]      │
│  [矩形]   │  │  │ 产品标题 │       │    │               │
│  [图片]   │  │  └──────────┘       │    │  文本内容:    │
│  [裁剪]   │  │                      │    │  [产品标题]   │
│           │  │  [产品图片]          │    │               │
│  ---      │  │                      │    │  字体:        │
│           │  │  [购买按钮]          │    │  [Arial ▼]    │
│  一键操作 │  └─────────────────────┘    │               │
│           │                             │  大小: [24]   │
│  [翻译]   │   缩放: 100% [+][-]         │               │
│  [改尺寸] │                             │  颜色: [⬛]    │
│  [批量]   │                             │               │
│           │                             │  位置:        │
│           │                             │  X: [120]     │
│           │                             │  Y: [50]      │
├───────────┴─────────────────────────────┴───────────────┤
│  图层面板                                                │
│  ☑ 产品标题 (文本)                    [👁][🔒][🗑]     │
│  ☑ 产品图片 (图片)                    [👁][🔒][🗑]     │
│  ☐ 背景 (智能对象) [展开▼]            [👁][🔒][🗑]     │
│     ☑ 渐变背景                                          │
│     ☑ 装饰元素                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 跨平台打包

### 最终产物
```
mediatools-v2.0.0-win64.exe    (150MB)
  ├─ Python后端 (内嵌)
  ├─ Node.js PSD服务 (内嵌)
  ├─ 前端资源 (内嵌)
  └─ 配置文件模板

mediatools-v2.0.0-linux        (140MB)
mediatools-v2.0.0-macos.dmg    (160MB)
```

---

## 开发时间估算

| 阶段 | 任务 | 时间 |
|------|------|------|
| Phase 1 | Node.js PSD服务（解析+导出） | 2天 |
| Phase 2 | Python API（翻译+改尺寸） | 2天 |
| Phase 3 | 前端Canvas编辑器 | 3天 |
| Phase 4 | 图层面板+属性面板 | 2天 |
| Phase 5 | 智能对象编辑 | 2天 |
| Phase 6 | 打包+测试 | 2天 |
| **总计** |  | **13天** |

---

## 风险与挑战

### 技术风险
1. **大文件性能**：PSD超过500MB时浏览器可能卡顿
   - 缓解：使用缩略图预览，惰性加载图层
   
2. **PSD往返保真**：复杂效果（图层样式、混合模式）可能丢失
   - 缓解：只允许编辑文本和基础变换，保留原始PSD数据
   
3. **字体缺失**：服务器端没有用户字体
   - 缓解：提供字体上传功能，或使用Google Fonts

### 产品风险
1. **用户学习成本**：两种模式可能造成困惑
   - 缓解：清晰的引导流程，默认自动化模式

---

## 未来扩展

- [ ] 批量处理队列（100个PSD并行翻译）
- [ ] PSD版本历史（Undo/Redo跨会话）
- [ ] 协作编辑（多人同时编辑一个PSD）
- [ ] 插件系统（用户自定义自动化脚本）
- [ ] Figma/Sketch导入支持

---

**总结**：该架构既满足批量自动化需求，又提供精细编辑能力，跨平台支持完善，技术栈成熟可靠。
