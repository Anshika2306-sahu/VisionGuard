import { useState } from "react";
import { Search, AlertTriangle, IndianRupee } from "lucide-react";
import Layout from "../components/Layout";
import { citizenAlerts, citizenChallans, payChallan, Challan } from "../lib/api";

const BLR = { lat: 12.9716, lng: 77.5946 };

export default function CitizenPortal() {
  const [plate, setPlate] = useState("KA01AB1234");
  const [challans, setChallans] = useState<Challan[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [searched, setSearched] = useState(false);

  async function search() {
    const [c, a] = await Promise.all([
      citizenChallans(plate.toUpperCase()),
      citizenAlerts(BLR.lat, BLR.lng, 8),
    ]);
    setChallans(c);
    setAlerts(a);
    setSearched(true);
  }

  async function pay(id: string) {
    await payChallan(id);
    setChallans(await citizenChallans(plate.toUpperCase()));
  }

  const totalDue = challans
    .filter((c) => c.status !== "paid")
    .reduce((s, c) => s + c.fine_amount, 0);

  return (
    <Layout subtitle="Citizen Portal">
      <div className="max-w-3xl mx-auto space-y-5">
        <div className="card">
          <h3 className="font-semibold mb-3">Check your challans</h3>
          <div className="flex gap-2">
            <div className="flex items-center gap-2 bg-panel2 rounded-lg px-3 flex-1">
              <Search size={16} className="text-gray-400" />
              <input
                className="bg-transparent py-2 outline-none w-full font-mono"
                value={plate}
                onChange={(e) => setPlate(e.target.value.toUpperCase())}
                placeholder="KA01AB1234"
              />
            </div>
            <button className="btn btn-primary" onClick={search}>Search</button>
          </div>
        </div>

        {searched && (
          <>
            <div className="card flex items-center justify-between">
              <span className="text-gray-300">Total outstanding</span>
              <span className="flex items-center gap-1 text-warn font-bold text-xl">
                <IndianRupee size={18} />
                {totalDue.toLocaleString("en-IN")}
              </span>
            </div>

            <div className="card">
              <h3 className="font-semibold mb-3">Your challans ({challans.length})</h3>
              {challans.length === 0 && <div className="text-gray-500 text-sm">No challans found for {plate}. 🎉</div>}
              <div className="space-y-2">
                {challans.map((c) => (
                  <div key={c.id} className="flex items-center justify-between bg-panel2 rounded-lg p-3">
                    <div>
                      <div className="font-medium">{c.violation_type}</div>
                      <div className="text-xs text-gray-400">
                        ₹{c.fine_amount} · {c.status} · {c.address || "Bengaluru"}
                      </div>
                    </div>
                    {c.status !== "paid" ? (
                      <button className="btn btn-primary text-sm" onClick={() => pay(c.id)}>Pay</button>
                    ) : (
                      <span className="badge bg-ok/20 text-ok">paid</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={18} className="text-warn" />
                <h3 className="font-semibold">Safety alerts near you</h3>
              </div>
              {alerts.length === 0 && <div className="text-gray-500 text-sm">No nearby accident/jam alerts.</div>}
              <div className="space-y-1 text-sm">
                {alerts.map((a, i) => (
                  <div key={i} className="flex items-center justify-between border-b border-white/5 py-1">
                    <span>
                      <span className="badge bg-warn/20 text-warn mr-2">{a.type}</span>
                      {a.address}
                    </span>
                    <span className="text-gray-400">{a.distance_km} km</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
