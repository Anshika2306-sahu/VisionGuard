// Loads the Mappls (MapMyIndia) Web Map SDK on demand. Resolves false on any failure
// so the UI can fall back gracefully (the dashboard must never break if maps are offline).

let loading: Promise<boolean> | null = null;

export function loadMappls(key: string): Promise<boolean> {
  if (!key || key.startsWith("__")) return Promise.resolve(false);
  if ((window as any).mappls?.Map) return Promise.resolve(true);
  if (loading) return loading;

  loading = new Promise<boolean>((resolve) => {
    const timeout = setTimeout(() => resolve(false), 8000);
    const s = document.createElement("script");
    s.src = `https://apis.mappls.com/advancedmaps/api/${key}/map_sdk?layer=vector&v=3.0`;
    s.async = true;
    s.onload = () => {
      clearTimeout(timeout);
      resolve(Boolean((window as any).mappls?.Map));
    };
    s.onerror = () => {
      clearTimeout(timeout);
      resolve(false);
    };
    document.head.appendChild(s);
  });
  return loading;
}
