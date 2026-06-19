import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { getChallans, payChallan } from "../lib/api";

const statusBadge: Record<string, string> = {
  issued: "bg-warn/20 text-warn",
  notified: "bg-brand/20 text-brand",
  paid: "bg-ok/20 text-ok",
  contested: "bg-warn/20 text-warn",
  expired: "bg-danger/20 text-danger",
};

export default function ChallansTable() {
  const qc = useQueryClient();
  const [plate, setPlate] = useState("");
  const { data: rows = [] } = useQuery({
    queryKey: ["challans", plate],
    queryFn: () => getChallans(plate ? { plate } : {}),
    refetchInterval: 6000,
  });

  async function pay(id: string) {
    await payChallan(id);
    qc.invalidateQueries({ queryKey: ["challans"] });
    qc.invalidateQueries({ queryKey: ["kpis"] });
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">Challans</h3>
        <div className="flex items-center gap-2 bg-panel2 rounded-lg px-2">
          <Search size={14} className="text-gray-400" />
          <input
            className="bg-transparent text-sm py-1 outline-none"
            placeholder="search plate…"
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
          />
        </div>
      </div>
      <div className="overflow-auto max-h-[360px]">
        <table className="w-full text-sm">
          <thead className="text-gray-400 text-xs">
            <tr className="text-left">
              <th className="py-2">Plate</th>
              <th>Violation</th>
              <th>Fine</th>
              <th>Status</th>
              <th>Location</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="text-gray-500 py-3">No challans yet.</td>
              </tr>
            )}
            {rows.map((c) => (
              <tr key={c.id} className="table-row">
                <td className="py-2 font-mono">{c.plate_text}</td>
                <td>{c.violation_type}</td>
                <td>₹{c.fine_amount}</td>
                <td>
                  <span className={`badge ${statusBadge[c.status] || "bg-gray-500/20"}`}>{c.status}</span>
                </td>
                <td className="text-gray-400 text-xs">{c.address || (c.lat ? `${c.lat.toFixed(3)},${c.lng?.toFixed(3)}` : "—")}</td>
                <td>
                  {c.status !== "paid" && (
                    <button className="text-brand text-xs hover:underline" onClick={() => pay(c.id)}>
                      mark paid
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
