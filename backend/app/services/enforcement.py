"""Enforcement: turn a finable violation into a challan + e-notice (mirrors MLFF 72h notice)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.storage import storage
from app.db.models import Camera, Challan, Vehicle, Violation
from ml.configs.classes import VIOLATION_TYPES

ENOTICE_HOURS = 72


def _enotice_html(challan: Challan, camera: Camera | None) -> str:
    loc = (camera.address or camera.name) if camera else "Unknown location"
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<title>e-Challan {challan.id}</title></head>
<body style='font-family:sans-serif;max-width:640px;margin:auto'>
<h2>Bengaluru Traffic Police — e-Challan Notice</h2>
<p><b>Challan ID:</b> {challan.id}</p>
<p><b>Vehicle:</b> {challan.plate_text}</p>
<p><b>Violation:</b> {VIOLATION_TYPES.get(challan.violation_type, {}).get('label', challan.violation_type)}</p>
<p><b>Fine:</b> Rs. {challan.fine_amount}</p>
<p><b>Location:</b> {loc}</p>
<p><b>Issued:</b> {challan.issued_at:%Y-%m-%d %H:%M} &nbsp; <b>Due:</b> {challan.due_at:%Y-%m-%d %H:%M}</p>
<p>Please pay within {ENOTICE_HOURS} hours. This notice was generated automatically from
photographic evidence by VisionGuard AI on the Safe City camera network.</p>
</body></html>"""


def create_challan(db: Session, violation: Violation, camera: Camera | None) -> Challan | None:
    meta = VIOLATION_TYPES.get(violation.type)
    if not meta or meta["severity"] != "finable":
        return None

    challan = Challan(
        violation_id=violation.id,
        camera_id=violation.camera_id,
        plate_text=violation.plate_text or "UNREADABLE",
        violation_type=violation.type,
        fine_amount=meta["fine"],
        status="issued",
        evidence_uri=violation.evidence_uri,
        lat=camera.lat if camera else None,
        lng=camera.lng if camera else None,
        address=camera.address if camera else None,
    )
    db.add(challan)
    db.flush()  # get issued_at default + id
    challan.due_at = challan.issued_at + timedelta(hours=ENOTICE_HOURS)

    # write e-notice + mark notified
    html = _enotice_html(challan, camera)
    key = f"enotice/{challan.id}.html"
    storage.save(key, html.encode("utf-8"))
    challan.enotice_uri = storage.url(key)
    challan.status = "notified"

    # upsert vehicle stub (owner resolution would hit VAHAN at scale)
    if challan.plate_text and challan.plate_text != "UNREADABLE":
        if not db.get(Vehicle, challan.plate_text):
            db.add(Vehicle(plate_text=challan.plate_text))

    db.add(challan)
    return challan
