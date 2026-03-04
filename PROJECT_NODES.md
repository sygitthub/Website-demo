# CANGO 海外资源库看板 · 重要节点总结

用于下个任务继续排查「议题共现热力图」不显示的 bug。

---

## 一、项目与入口

- **主入口**：`index.html`（单页静态看板，无需构建）
- **数据**：`cango-data-lite.js`（预嵌入机构数据，由 JSON 转换）
- **依赖**：Tailwind CDN、Chart.js、TagCanvas（词云已改用内嵌脚本，TagCanvas 未再用于词云区）

---

## 二、页面结构（图表区域）

图表在 **`<section class="px-8 pt-4 pb-6">`** 内，其下为 **12 列网格** `class="grid grid-cols-12 gap-5"`。关键模块顺序：

| 顺序 | 模块 | 容器 / 说明 |
|------|------|-------------|
| 1 | 总部区域分布 + 存续状态 | `article`，饼图/圆环 + 大洲 chips |
| 2 | 机构性质 / 职能类型占比 | `article`，条形图 |
| 3 | **议题关注词云（3D 球形）** | `<div id="sphere-wordcloud-root" class="col-span-12">`，由底部词云脚本渲染 |
| 4 | **议题共现热力图（MECE）** | `<div id="cango-heatmap-root" class="col-span-12">`，由底部热力图脚本渲染 ← **当前不显示** |
| 5 | 成立时间趋势 | `article`，柱状图 `#foundedYearChart` |
| 6 | 机构列表（隐藏） | `article`，表格 |
| 7 | 数据校验说明 | 区域统计表 |

- 词云、热力图的 div 都必须带 **`class="col-span-12"`**，否则在网格中只占一列会被挤到左侧。

---

## 三、脚本加载顺序（均在 body 内）

1. **约 961–2302 行**：主业务脚本（指标、饼图、条形图、成立年份图、抽屉、弹窗、**不包含** `initIssueWordCloud()` 调用）
2. **约 2304–2638 行**：词云嵌入脚本（IIFE，找 `#sphere-wordcloud-root`，有 `if (!root) return;`，直接写 DOM）
3. **约 2640–3046 行**：热力图嵌入脚本（IIFE，`runHeatmap()` 找 `#cango-heatmap-root`，有 `if (!root) return;`，用 `initHeatmap()` + try/catch，`setTimeout(initHeatmap, 0)` 延后执行）

---

## 四、热力图相关节点（bug 排查重点）

- **挂载点**：唯一一处  
  - **行号**：约 **573**  
  - **HTML**：`<div id="cango-heatmap-root" class="col-span-12" style="width:100%;max-width:100%;box-sizing:border-box;"></div>`
- **脚本入口**：约 **2640** 行 `<script>`，IIFE 内：
  - `runHeatmap()`：内部 `const root = document.getElementById("cango-heatmap-root"); if (!root) return;`，然后清空并设置 `root.style`（含 `width:100%;min-height:320px;display:block`），再插入标题、MECE 按钮、热力图表格、右侧详情卡与共现 Top10。
  - `initHeatmap()`：`try { runHeatmap(); } catch (e) { console.warn("议题共现热力图初始化失败:", e); }`
  - 执行时机：`document.readyState === "loading"` 时在 `DOMContentLoaded` 里 `setTimeout(initHeatmap, 0)`；否则直接 `setTimeout(initHeatmap, 0)`。

**已做过的修复**：删除易被错误解析的多行注释、`runHeatmap` 前增加 root 空值判断、try/catch、延后到 `setTimeout(0)`、给 root 设 `min-height:320px` 等，控制台已无热力图相关报错，但热力图仍不显示。

---

## 五、词云相关节点（对比参考）

- **挂载点**：约 **570** 行  
  - `<div id="sphere-wordcloud-root" class="col-span-12" ...></div>`
- **脚本**：约 2304–2638 行，IIFE 内直接 `getElementById("sphere-wordcloud-root")`，有 `if (!root) return;`，然后清空并写入 SVG 词云 + 滑块 + Top5 卡片。词云当前可正常显示。

---

## 六、建议下个任务排查方向

1. **DOM 是否真有 `#cango-heatmap-root`**  
   在控制台执行 `document.getElementById("cango-heatmap-root")`，看是否为 `null`；若为 null，说明挂载点被删或 id 写错。

2. **脚本是否执行到 `runHeatmap`**  
   在 `runHeatmap()` 开头临时加 `console.log("runHeatmap", root);`，刷新后看控制台是否输出、`root` 是否为元素。

3. **root 内是否有内容**  
   执行后看 `document.getElementById("cango-heatmap-root").innerHTML` 或 `children.length`，若为空且无报错，可能是 `runHeatmap` 未执行或提前 return。

4. **布局/样式是否把热力图压掉**  
   在 Elements 里选中 `#cango-heatmap-root`，看 Computed 的 `display`、`height`、`visibility`、`overflow`，以及父级是否有 `height:0` 或 `overflow:hidden` 导致不可见。

5. **执行顺序**  
   若词云脚本在热力图之前且对 DOM 有较大改动，可尝试把热力图脚本移到词云脚本之前，或改为在 `window.addEventListener("load", initHeatmap)` 中执行，排除解析/执行顺序问题。

---

## 七、关键文件与行号速查

| 内容 | 文件 | 约行号 |
|------|------|--------|
| 热力图挂载 div | index.html | 572–573 |
| 热力图脚本开始 | index.html | 2640 |
| runHeatmap / root 与样式 | index.html | 2642–2720 |
| initHeatmap / 执行时机 | index.html | 3032–3044 |
| 词云挂载 div | index.html | 570 |
| 词云脚本 | index.html | 2304–2638 |
| 主业务脚本 / initDashboard | index.html | 961–2302 |

---

*文档生成后可直接在下个任务中引用「PROJECT_NODES.md」与上述行号继续修 bug。*
