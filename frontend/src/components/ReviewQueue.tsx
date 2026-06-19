import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import { confirmViolation, dismissViolation, getViolations } from "../lib/api";

export default function ReviewQueue() {
  const qc = useQueryClient();
  const { data: items = [] } = useQuery({
    queryKey: ["violations", "needs_review"],
    queryFn: () => getViolations({ status: "needs_review", limit: 50 }),
    refetchInterval: 5000,
  });

  async function act(id: string, kind: "confirm" | "dismiss") {
    if (kind === "confirm") await confirmViolation(id);
    else await dismissViolation(id, "reviewed");
    qc.invalidateQueries({ queryKey: ["violations"] });
    qc.invalidateQueries({ queryKey: ["challans"] });
    qc.invalidateQueries({ queryKey: ["kpis"] });
  }

  return (
    <div className="card">
      <h3 className="font-semibold mb-3">Review Queue ({items.length})</h3>
      {items.length === 0 && <div className="text-gray-500 text-sm">Nothing pending review. 🎉</div>}
      <div className="space-y-2">
        {items.map((v) => (
          <div key={v.id} className="flex items-center justify-between bg-panel2 rounded-lg p-2">
            <div className="flex items-center gap-3">
              {v.evidence_uri && (
                <img src={v.evidence_uri} className="w-14 h-10 object-cover rounded" alt="evidence" />
              )}
              <div>
                <div className="font-medium text-sm">{v.type}</div>
                <div className="text-xs text-gray-400">
                  conf {(v.confidence * 100).toFixed(0)}% · {v.plate_text || "no plate"}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button className="btn btn-ghost text-ok p-2" onClick={() => act(v.id, "confirm")} title="Confirm → issue challan">
                <Check size={16} />
              </button>
              <button className="btn btn-ghost text-danger p-2" onClick={() => act(v.id, "dismiss")} title="Dismiss">
                <X size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
