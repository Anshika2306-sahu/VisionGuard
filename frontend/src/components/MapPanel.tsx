import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapPin } from "lucide-react";
import { getConfig, getHeatmap, getCameras, HeatPoint } from "../lib/api";
import { loadMappls } from "../lib/mappls";

const BLR_CENTER = { lat: 12.9716, lng: 77.5946 };

export default function MapPanel() {
  const mapEl = useRef<HTMLDivElement>(null);
  const mapObj = useRef<any>(null);
  const [mapReady, setMapReady] = useState(false);
  const [mapFailed, setMapFailed] = useState(false);

  const { data: cfg } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const { data: heat = [] } = useQuery({
    queryKey: ["heatmap"],
    queryFn: () => getHeatmap(),
    refetchInterval: 5000,
  });
  const { data: cameras = [] } = useQuery({ queryKey: ["cameras"], queryFn: getCameras });

  // init map once we have a key
  useEffect(() => {
    let cancelled = false;
    if (!cfg?.mappls_map_key) return;
    loadMappls(cfg.mappls_map_key).then((ok) => {
      if (cancelled) return;
      if (!ok || !mapEl.current) {
        setMapFailed(true);
        return;
      }
      try {
        const mappls = (window as any).mappls;
        mapObj.current = new mappls.Map(mapEl.current, { center: BLR_CENTER, zoom: 11 });
        setMapReady(true);
      } catch {
        setMapFailed(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [cfg?.mappls_map_key]);

  // draw markers when map + data ready
  useEffect(() => {
    if (!mapReady || !mapObj.current) return;
    const mappls = (window as any).mappls;
    try {
      // cameras (neutral)
      cameras.forEach((c) => {
        new mappls.Marker({
          map: mapObj.current,
          position: { lat: c.lat, lng: c.lng },
          popupHtml: `<b>${c.name}</b><br/>${c.code}`,
        });
      });
      // violation hot points (sized by weight) — Circle API may not exist in all SDK builds
      const Circle = mappls.Circle;
      if (Circle) {
        heat.forEach((h: HeatPoint) => {
          new Circle({
            map: mapObj.current,
            center: { lat: h.lat, lng: h.lng },
            radius: 60 + h.weight * 30,
            fillColor: h.severity === "safety_alert" ? "#f59e0b" : "#ef4444",
            fillOpacity: 0.35,
            strokeColor: "#ef4444",
          });
        });
      }
    } catch {
      /* marker API variance — ignore, map still shows */
    }
  }, [mapReady, heat, cameras]);

  return (
    <div className="card h-[420px] flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <MapPin size={18} className="text-brand" />
        <h3 className="font-semibold">Live Safety Heatmap — Bengaluru</h3>
        <span className="text-xs text-gray-500 ml-auto">powered by Mappls</span>
      </div>
      {!mapFailed ? (
        <div ref={mapEl} className="flex-1 rounded-lg overflow-hidden bg-panel2" />
      ) : (
        <FallbackMap heat={heat} cameras={cameras} />
      )}
    </div>
  );
}

function FallbackMap({ heat, cameras }: { heat: HeatPoint[]; cameras: any[] }) {
  return (
    <div className="flex-1 rounded-lg bg-panel2 p-3 overflow-auto">
      <div className="text-xs text-warn mb-2">
        Live map unavailable (offline / key) — showing geocoded incidents:
      </div>
      <div className="space-y-1 text-sm">
        {heat.length === 0 && <div className="text-gray-500">No incidents yet. Upload a frame to populate.</div>}
        {heat.map((h, i) => (
          <div key={i} className="flex items-center justify-between border-b border-white/5 py-1">
            <span>
              <span
                className={`badge mr-2 ${h.severity === "safety_alert" ? "bg-warn/20 text-warn" : "bg-danger/20 text-danger"}`}
              >
                {h.type}
              </span>
              {h.lat.toFixed(4)}, {h.lng.toFixed(4)}
            </span>
            <span className="text-gray-400">×{h.weight}</span>
          </div>
        ))}
      </div>
      <div className="text-xs text-gray-500 mt-3">{cameras.length} cameras online</div>
    </div>
  );
}
