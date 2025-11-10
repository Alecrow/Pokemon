import { useMemo, useState } from "react";

type NodeT = { id: string; name: string; x: number; y: number };
type EdgeT = { a: string; b: string; w: number };

export default function PokeMapPathfinder() {
  const nodes: NodeT[] = [
    { id: "PAL", name: "Pallet",   x: 12, y: 78 },
    { id: "VRD", name: "Viridian", x: 18, y: 60 },
    { id: "PEW", name: "Pewter",   x: 16, y: 40 },
    { id: "CER", name: "Cerulean", x: 42, y: 30 },
    { id: "SFR", name: "Saffron",  x: 40, y: 48 },
    { id: "LAV", name: "Lavender", x: 60, y: 40 },
    { id: "CEL", name: "Celadon",  x: 28, y: 48 },
    { id: "FUC", name: "Fuchsia",  x: 52, y: 72 },
    { id: "VER", name: "Vermilion",x: 60, y: 62 },
    { id: "CIN", name: "Cinnabar", x: 16, y: 92 },
    { id: "SEA", name: "Seafoam",  x: 72, y: 78 },
  ];

  const edges: EdgeT[] = [
    { a: "PAL", b: "VRD", w: 5 },
    { a: "VRD", b: "PEW", w: 6 },
    { a: "VRD", b: "SFR", w: 8 },
    { a: "PEW", b: "CER", w: 6 },
    { a: "CER", b: "SFR", w: 5 },
    { a: "SFR", b: "CEL", w: 4 },
    { a: "SFR", b: "LAV", w: 5 },
    { a: "CEL", b: "VER", w: 6 },
    { a: "VER", b: "LAV", w: 6 },
    { a: "VER", b: "FUC", w: 6 },
    { a: "FUC", b: "SEA", w: 6 },
    { a: "PAL", b: "CIN", w: 6 },
    { a: "CIN", b: "FUC", w: 9 },
  ];

  const byId = useMemo(() => Object.fromEntries(nodes.map(n => [n.id, n])), []);
  const [src, setSrc] = useState<string | null>(null);
  const [dst, setDst] = useState<string | null>(null);

  const graph = useMemo(() => {
    const adj: Record<string, { to: string; w: number }[]> = {};
    nodes.forEach(n => (adj[n.id] = []));
    edges.forEach(e => {
      adj[e.a].push({ to: e.b, w: e.w });
      adj[e.b].push({ to: e.a, w: e.w });
    });
    return adj;
  }, []);

  function dijkstra(a: string, b: string) {
    const dist: Record<string, number> = {};
    const prev: Record<string, string | null> = {};
    const Q = new Set(nodes.map(n => n.id));
    nodes.forEach(n => (dist[n.id] = Infinity));
    dist[a] = 0; prev[a] = null;
    while (Q.size) {
      let u: string | null = null, best = Infinity;
      Q.forEach(id => { if (dist[id] < best) { best = dist[id]; u = id; } });
      if (u == null) break;
      Q.delete(u);
      if (u === b) break;
      for (const { to, w } of graph[u]) {
        if (!Q.has(to)) continue;
        const nd = dist[u] + w;
        if (nd < dist[to]) { dist[to] = nd; prev[to] = u; }
      }
    }
    if (!isFinite(dist[b])) return { cost: Infinity, path: [] as string[] };
    const path: string[] = [];
    for (let cur: string | null = b; cur; cur = prev[cur] ?? null) path.push(cur);
    path.reverse();
    return { cost: dist[b], path };
  }

  const result = useMemo(() => (src && dst ? dijkstra(src, dst) : null), [src, dst]);

  function pick(id: string) {
    if (!src) setSrc(id);
    else if (!dst && id !== src) setDst(id);
    else { setSrc(id); setDst(null); }
  }

  return (
    <div className="w-full min-h-screen bg-sky-50 text-slate-800 p-4 flex items-center justify-center">
      <div className="w-[900px] max-w-full">
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-xl font-bold">Mapa estilo Pokémon — Mejor ruta</h1>
          <button className="px-3 py-1 rounded-xl bg-white shadow hover:shadow-md"
                  onClick={() => { setSrc(null); setDst(null); }}>
            Reiniciar
          </button>
        </div>

        <div className="grid md:grid-cols-[2fr_1fr] gap-4">
          <div className="relative rounded-2xl shadow bg-gradient-to-b from-green-200 via-green-100 to-blue-100 p-3">
            <div className="relative w-full h-[520px] rounded-xl overflow-hidden">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full">
                {edges.map((e, i) => {
                  const A = byId[e.a], B = byId[e.b];
                  const active =
                    result?.path.includes(e.a) && result?.path.includes(e.b) &&
                    Math.abs(result!.path.indexOf(e.a) - result!.path.indexOf(e.b)) === 1;
                  return (
                    <g key={i}>
                      <line x1={A.x} y1={A.y} x2={B.x} y2={B.y}
                            stroke={active ? "#f59e0b" : "#d1a86f"}
                            strokeWidth={active ? 2.5 : 2} strokeLinecap="round"/>
                      <text x={(A.x+B.x)/2} y={(A.y+B.y)/2 - 1.5}
                            fontSize="2.5" textAnchor="middle" fill="#555">{e.w}</text>
                    </g>
                  );
                })}
              </svg>

              {nodes.map(n => {
                const sel = n.id === src || n.id === dst;
                return (
                  <button key={n.id} onClick={() => pick(n.id)}
                          className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
                          style={{ left: `${n.x}%`, top: `${n.y}%` }}>
                    <span className={`w-4 h-4 rounded-full border-2 ${sel ? "bg-amber-400 border-amber-600" : "bg-white border-slate-700"} shadow`} />
                    <span className="mt-1 px-2 py-0.5 text-[10px] rounded bg-white/80 shadow">{n.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow p-4 h-fit">
            {!src || !dst ? (
              <p className="text-slate-600 text-sm">Elige dos ciudades para calcular la mejor ruta.</p>
            ) : result && isFinite(result.cost) ? (
              <div className="space-y-2">
                <div className="text-base font-semibold">Costo: {result.cost}</div>
                <div className="flex flex-wrap gap-1 items-center">
                  {result.path.map((id, i) => (
                    <span key={id} className="text-xs px-2 py-1 rounded-full bg-amber-100 border border-amber-300">
                      {byId[id].name}{i < result.path.length-1 ? " →" : ""}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-red-600 text-sm">No existe ruta entre esas ciudades.</p>
            )}
          </div>
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Tip: clic en una ciudad para origen; clic en otra para destino; clic en una tercera reinicia seleccionando nuevo origen.
        </p>
      </div>
    </div>
  );
}
