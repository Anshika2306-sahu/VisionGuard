import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload, Loader2 } from "lucide-react";
import { getCameras, getJob, uploadImage } from "../lib/api";

const sevColor = (s: string) => (s === "safety_alert" ? "bg-warn/20 text-warn" : "bg-danger/20 text-danger");
const statusColor: Record<string, string> = {
  auto_issued: "bg-danger/20 text-danger",
  needs_review: "bg-warn/20 text-warn",
  alert: "bg-brand/20 text-brand",
  dismissed: "bg-gray-500/20 text-gray-400",
};

export default function UploadPanel() {
  const qc = useQueryClient();
  const { data: cameras = [] } = useQuery({ queryKey: ["cameras"], queryFn: getCameras });
  const [cameraId, setCameraId] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const { data: job } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const s = (q.state.data as any)?.status;
      return s === "done" || s === "failed" || s === "unusable" ? false : 1200;
    },
  });

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const { id } = await uploadImage(file, cameraId || undefined);
      setJobId(id);
      // refresh dashboards shortly after processing
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["kpis"] });
        qc.invalidateQueries({ queryKey: ["heatmap"] });
        qc.invalidateQueries({ queryKey: ["violations"] });
        qc.invalidateQueries({ queryKey: ["challans"] });
      }, 2500);
    } finally {
      setBusy(false);
    }
  }

  const processing = job && !["done", "failed", "unusable"].includes(job.status);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-3">
        <Upload size={18} className="text-brand" />
        <h3 className="font-semibold">Analyze a Frame</h3>
      </div>
      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <select className="input flex-1" value={cameraId} onChange={(e) => setCameraId(e.target.value)}>
          <option value="">Select camera (optional)…</option>
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.code})
            </option>
          ))}
        </select>
        <label className="btn btn-primary cursor-pointer text-center">
          {busy ? "Uploading…" : "Upload image"}
          <input type="file" accept="image/*" className="hidden" onChange={onFile} />
        </label>
      </div>

      {processing && (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Loader2 className="animate-spin" size={16} /> Processing… ({job?.status})
        </div>
      )}

      {job && job.status === "done" && (
        <div className="grid md:grid-cols-2 gap-4 mt-2">
          <div>
            {job.annotated_uri ? (
              <img src={job.annotated_uri} alt="annotated evidence" className="rounded-lg border border-white/10 w-full" />
            ) : (
              <div className="text-gray-500 text-sm">No evidence image.</div>
            )}
            <div className="text-xs text-gray-500 mt-1">
              Quality score: {job.quality_score?.toFixed(2)} · {job.detections.length} objects detected
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-semibold">Violations ({job.violations.length})</div>
            {job.violations.length === 0 && <div className="text-gray-500 text-sm">No violations detected.</div>}
            {job.violations.map((v) => (
              <div key={v.id} className="bg-panel2 rounded-lg p-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{v.type}</span>
                  <span className={`badge ${sevColor(v.severity)}`}>{v.severity}</span>
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                  <span className={`badge ${statusColor[v.status] || "bg-gray-500/20"}`}>{v.status}</span>
                  <span>conf {(v.confidence * 100).toFixed(0)}%</span>
                  {v.plate_text && <span>plate {v.plate_text}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {job && (job.status === "unusable" || job.status === "failed") && (
        <div className="text-warn text-sm mt-2">
          Frame {job.status}. {job.status === "unusable" ? "Image quality too low to fine (safety alerts only)." : ""}
        </div>
      )}
    </div>
  );
}
