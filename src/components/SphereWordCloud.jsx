import { useState, useRef, useEffect, useMemo } from 'react';

const ISSUE_DATA = [
  { name: '环境与气候变化', value: 68, tier: 'tier1' },
  { name: '教育与能力建设', value: 63, tier: 'tier1' },
  { name: '社区发展与减贫', value: 58, tier: 'tier1' },
  { name: '可持续发展目标', value: 51, tier: 'tier1' },
  { name: '人权与社会正义', value: 47, tier: 'tier1' },
  { name: '健康与公共卫生', value: 44, tier: 'tier1' },
  { name: '气候正义', value: 55, tier: 'tier2' },
  { name: '妇女赋权', value: 49, tier: 'tier2' },
  { name: 'SDG推进', value: 45, tier: 'tier2' },
  { name: '社会包容', value: 40, tier: 'tier2' },
  { name: '能源转型', value: 36, tier: 'tier2' },
  { name: '数字技术与创新', value: 43, tier: 'tier3' },
  { name: '青年发展', value: 38, tier: 'tier3' },
  { name: '城市化', value: 32, tier: 'tier3' },
  { name: '民主参与', value: 29, tier: 'tier3' },
];

const TIER_COLORS = {
  tier1: '#38BDF8',
  tier2: '#2DD4BF',
  tier3: '#A78BFA',
};

// 球面均匀分布点（Fibonacci 球面格点），单位球
function spherePoints(n) {
  const points = [];
  const phi = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = 1 - (i / (n - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const theta = phi * i;
    const x = Math.cos(theta) * r;
    const z = Math.sin(theta) * r;
    points.push({ x, y, z });
  }
  return points;
}

// 绕 Y 轴旋转
function rotateY(x, z, rad) {
  const c = Math.cos(rad);
  const s = Math.sin(rad);
  return { x: x * c - z * s, z: x * s + z * c };
}
// 绕 X 轴旋转
function rotateX(y, z, rad) {
  const c = Math.cos(rad);
  const s = Math.sin(rad);
  return { y: y * c + z * s, z: -y * s + z * c };
}
// 应用 rotY 再 rotX 后的 3D 坐标，用于投影
function project(x, y, z, rotYRad, rotXRad) {
  const { x: x1, z: z1 } = rotateY(x, z, rotYRad);
  const { y: y1, z: z1b } = rotateX(y, z1, rotXRad);
  return { x: x1, y: y1, z: z1b };
}

export default function SphereWordCloud() {
  const [maxWords, setMaxWords] = useState(16);
  const [rotX, setRotX] = useState(0.2);
  const [rotY, setRotY] = useState(0);
  const [paused, setPaused] = useState(false);
  const [tooltip, setTooltip] = useState(null);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef({ lastX: 0, lastY: 0 });
  const containerRef = useRef(null);
  const animRef = useRef(null);

  const words = useMemo(() => ISSUE_DATA.slice(0, Math.min(maxWords, ISSUE_DATA.length)), [maxWords]);
  const points = useMemo(() => spherePoints(words.length), [words.length]);
  const maxVal = Math.max(...ISSUE_DATA.map((d) => d.value));
  const minVal = Math.min(...ISSUE_DATA.map((d) => d.value));

  useEffect(() => {
    if (paused || dragging) return;
    const step = 0.002;
    const tick = () => {
      setRotY((y) => y + step);
      animRef.current = requestAnimationFrame(tick);
    };
    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [paused, dragging]);

  const handlePointerDown = (e) => {
    if (e.button !== 0) return;
    setDragging(true);
    dragRef.current = { lastX: e.clientX, lastY: e.clientY };
  };

  const handlePointerMove = (e) => {
    if (!dragging) return;
    const dx = (e.clientX - dragRef.current.lastX) * 0.01;
    const dy = (e.clientY - dragRef.current.lastY) * 0.01;
    dragRef.current = { lastX: e.clientX, lastY: e.clientY };
    setRotY((y) => y + dx);
    setRotX((x) => Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, x + dy)));
  };

  const handlePointerUp = () => setDragging(false);

  useEffect(() => {
    const onUp = () => setDragging(false);
    window.addEventListener('pointerup', onUp);
    return () => window.removeEventListener('pointerup', onUp);
  }, []);

  const top5 = useMemo(() => [...ISSUE_DATA].sort((a, b) => b.value - a.value).slice(0, 5), []);
  const cardMax = top5[0]?.value ?? 1;

  return (
    <article className="dashboard-card col-span-12 rounded-3xl bg-slate-900/70 border border-slate-800">
      <header className="mb-3">
        <h2 className="text-base font-semibold text-slate-100">议题关注词云</h2>
        <p className="mt-0.5 text-[11px] text-slate-500">
          基于机构议题标签统计，词语越大代表关注度越高。悬停词汇可查看热度，拖拽可旋转球体。
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-4 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400">最大词数</span>
          <input
            type="range"
            min={6}
            max={16}
            value={maxWords}
            onChange={(e) => setMaxWords(Number(e.target.value))}
            className="w-28 h-1.5 rounded bg-slate-700 accent-sky-500"
          />
          <span className="text-[11px] text-slate-400 w-6">{maxWords}</span>
        </div>
      </div>

      <div
        ref={containerRef}
        className="relative rounded-xl overflow-hidden bg-slate-800/50 border border-slate-700/80 w-full select-none"
        style={{ height: 420 }}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative" style={{ width: 320, height: 320 }}>
            {words.map((item, i) => {
              const p = points[i];
              const proj = project(p.x, p.y, p.z, rotY, rotX);
              const scale = 0.6 + (0.4 * (item.value - minVal)) / (maxVal - minVal || 1);
              const color = TIER_COLORS[item.tier] || TIER_COLORS.tier1;
              const radius = 140;
              const x = proj.x * radius;
              const y = -proj.y * radius;
              const opacity = 0.35 + 0.65 * (proj.z * 0.5 + 0.5);
              const scale2d = 0.65 + 0.35 * (proj.z * 0.5 + 0.5);

              return (
                <span
                  key={item.name}
                  className="absolute whitespace-nowrap cursor-pointer"
                  style={{
                    left: '50%',
                    top: '50%',
                    marginLeft: x,
                    marginTop: y,
                    transform: `translate(-50%,-50%) scale(${scale * scale2d})`,
                    fontSize: `${11 + scale * 12}px`,
                    color,
                    opacity,
                    textShadow: '0 0 10px rgba(0,0,0,0.9)',
                    fontFamily: 'Inter, Microsoft YaHei, sans-serif',
                    zIndex: Math.round((proj.z + 1) * 50),
                  }}
                  onMouseEnter={(e) => {
                    setTooltip({ name: item.name, value: item.value, x: e.clientX, y: e.clientY });
                  }}
                  onMouseMove={(e) => {
                    setTooltip((t) => (t ? { ...t, x: e.clientX, y: e.clientY } : null));
                  }}
                  onMouseLeave={() => setTooltip(null)}
                >
                  {item.name}
                </span>
              );
            })}
          </div>
        </div>

        {tooltip && (
          <div
            className="fixed z-50 px-3 py-2 rounded-lg border border-slate-600 bg-slate-900/95 text-slate-100 shadow-xl pointer-events-none text-sm"
            style={{
              left: tooltip.x + 12,
              top: tooltip.y + 8,
            }}
          >
            <div className="font-medium">{tooltip.name}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">热度 {tooltip.value} 分</div>
          </div>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        {top5.map((d, i) => (
          <Card key={d.name} item={d} maxVal={cardMax} color={TIER_COLORS[d.tier]} />
        ))}
      </div>
    </article>
  );
}

function Card({ item, maxVal, color }) {
  const [hover, setHover] = useState(false);
  const pct = maxVal ? (item.value / maxVal) * 100 : 0;
  return (
    <div
      className={`rounded-xl border bg-slate-800/60 px-3 py-3 flex flex-col items-center text-center transition-all duration-200 ${
        hover ? 'border-sky-400/60 shadow-md' : 'border-slate-700/80'
      }`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <span className="text-xl font-bold text-slate-100">{item.value}</span>
      <span className="inline-block w-6 h-6 rounded mt-1" style={{ background: color }} />
      <span className="text-[10px] text-slate-400 mt-1 leading-tight">{item.name}</span>
      <div className="w-full mt-2 h-1 rounded-full bg-slate-700/80 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{
            width: hover ? `${pct}%` : '0%',
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}
