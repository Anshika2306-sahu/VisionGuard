import { useQuery } from "@tanstack/react-query";
import { FileText, Camera, AlertTriangle, Activity, Clock, IndianRupee } from "lucide-react";
import { getKpis } from "../lib/api";

const fmt = (n: number) => n.toLocaleString("en-IN");

export default function KpiCards() {
  const { data } = useQuery({ queryKey: ["kpis"], queryFn: getKpis, refetchInterval: 5000 });
  const k = data;
  const cards = [
    { label: "Challans Today", value: k?.challans_today ?? 0, icon: FileText, color: "text-brand" },
    { label: "Total Challans", value: k?.challans_total ?? 0, icon: FileText, color: "text-gray-200" },
    { label: "Active Cameras", value: k?.active_cameras ?? 0, icon: Camera, color: "text-ok" },
    { label: "Accident Alerts", value: k?.accident_alerts ?? 0, icon: AlertTriangle, color: "text-danger" },
    { label: "Jam Zones", value: k?.jam_zones ?? 0, icon: Activity, color: "text-warn" },
    { label: "Pending Review", value: k?.pending_review ?? 0, icon: Clock, color: "text-warn" },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="card flex flex-col gap-1">
          <c.icon className={c.color} size={20} />
          <div className="text-2xl font-bold">{fmt(c.value)}</div>
          <div className="text-xs text-gray-400">{c.label}</div>
        </div>
      ))}
      <div className="card col-span-2 md:col-span-3 lg:col-span-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-300">
          <IndianRupee size={16} className="text-ok" /> Fine collected:{" "}
          <span className="font-semibold text-ok">₹{fmt(k?.fine_collected ?? 0)}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-300">
          <IndianRupee size={16} className="text-warn" /> Outstanding:{" "}
          <span className="font-semibold text-warn">₹{fmt(k?.fine_outstanding ?? 0)}</span>
        </div>
      </div>
    </div>
  );
}
