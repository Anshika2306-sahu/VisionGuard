import axios from "axios";

export const api = axios.create({ baseURL: "/api/v1" });

// attach JWT from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("vg_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---- types ----
export interface Violation {
  id: string;
  job_id: string;
  type: string;
  severity: "finable" | "safety_alert";
  confidence: number;
  status: string;
  bbox: number[] | null;
  plate_text: string | null;
  evidence_uri: string | null;
  rationale: Record<string, any>;
}

export interface JobDetail {
  id: string;
  status: string;
  quality_score: number | null;
  annotated_uri: string | null;
  detections: { cls: string; conf: number; bbox: number[]; attrs: any }[];
  violations: Violation[];
}

export interface Challan {
  id: string;
  plate_text: string;
  violation_type: string;
  fine_amount: number;
  status: string;
  evidence_uri: string | null;
  lat: number | null;
  lng: number | null;
  address: string | null;
  issued_at: string | null;
  due_at: string | null;
}

export interface Camera {
  id: string;
  name: string;
  code: string;
  lat: number;
  lng: number;
  zone: string | null;
  address: string | null;
}

export interface Kpis {
  challans_total: number;
  challans_today: number;
  active_cameras: number;
  accident_alerts: number;
  jam_zones: number;
  pending_review: number;
  fine_collected: number;
  fine_outstanding: number;
}

export interface HeatPoint {
  lat: number;
  lng: number;
  weight: number;
  type: string;
  severity: string;
}

// ---- calls ----
export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  const { data } = await api.post("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data as { access_token: string; role: string };
}

export const getConfig = () => api.get("/config").then((r) => r.data as { mappls_map_key: string });
export const getKpis = () => api.get("/analytics/kpis").then((r) => r.data as Kpis);
export const getHeatmap = (type?: string) =>
  api.get("/geo/heatmap", { params: { type } }).then((r) => r.data as HeatPoint[]);
export const getCameras = () => api.get("/cameras").then((r) => r.data as Camera[]);
export const getViolations = (params: Record<string, any> = {}) =>
  api.get("/violations", { params }).then((r) => r.data as Violation[]);
export const getChallans = (params: Record<string, any> = {}) =>
  api.get("/challans", { params }).then((r) => r.data as Challan[]);
export const getTrends = (groupby = "type") =>
  api.get("/analytics/trends", { params: { groupby } }).then((r) => r.data as { key: string; count: number }[]);
export const getJob = (id: string) => api.get(`/jobs/${id}`).then((r) => r.data as JobDetail);

export async function uploadImage(file: File, camera_id?: string) {
  const fd = new FormData();
  fd.append("file", file);
  if (camera_id) fd.append("camera_id", camera_id);
  const { data } = await api.post("/ingest/image", fd);
  return data as { id: string };
}

export const confirmViolation = (id: string) => api.post(`/violations/${id}/confirm`).then((r) => r.data);
export const dismissViolation = (id: string, reason = "") =>
  api.post(`/violations/${id}/dismiss`, null, { params: { reason } }).then((r) => r.data);
export const payChallan = (id: string) => api.post(`/challans/${id}/pay`).then((r) => r.data);

export const citizenChallans = (plate: string) =>
  api.get("/citizen/challans", { params: { plate } }).then((r) => r.data as Challan[]);
export const citizenAlerts = (lat: number, lng: number, radius = 5) =>
  api.get("/citizen/alerts", { params: { lat, lng, radius } }).then((r) => r.data as any[]);
