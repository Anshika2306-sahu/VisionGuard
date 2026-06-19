import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from "recharts";
import Layout from "../components/Layout";
import KpiCards from "../components/KpiCards";
import MapPanel from "../components/MapPanel";
import UploadPanel from "../components/UploadPanel";
import ReviewQueue from "../components/ReviewQueue";
import ChallansTable from "../components/ChallansTable";
import { getTrends } from "../lib/api";

const COLORS = ["#2f81f7", "#ef4444", "#f59e0b", "#22c55e", "#a78bfa", "#f472b6", "#34d399"];

function TrendChart() {
  const { data = [] } = useQuery({ queryKey: ["trends"], queryFn: () => getTrends("type"), refetchInterval: 6000 });
  return (
    <div className="card h-[420px] flex flex-col">
      <h3 className="font-semibold mb-3">Violations by Type</h3>
      {data.length === 0 ? (
        <div className="text-gray-500 text-sm flex-1 grid place-items-center">No data yet.</div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="key" stroke="#64748b" fontSize={11} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
            <Tooltip contentStyle={{ background: "#1a2436", border: "none", borderRadius: 8 }} />
            <Bar dataKey="count">
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export default function CommandCenter() {
  const [tab, setTab] = useState<"review" | "challans">("review");
  return (
    <Layout subtitle="Command Center · ASTraM">
      <div className="space-y-5">
        <KpiCards />
        <div className="grid lg:grid-cols-2 gap-5">
          <MapPanel />
          <TrendChart />
        </div>
        <UploadPanel />
        <div>
          <div className="flex gap-2 mb-3">
            <button className={`btn ${tab === "review" ? "btn-primary" : "btn-ghost"}`} onClick={() => setTab("review")}>
              Review Queue
            </button>
            <button className={`btn ${tab === "challans" ? "btn-primary" : "btn-ghost"}`} onClick={() => setTab("challans")}>
              Challans
            </button>
          </div>
          {tab === "review" ? <ReviewQueue /> : <ChallansTable />}
        </div>
      </div>
    </Layout>
  );
}
