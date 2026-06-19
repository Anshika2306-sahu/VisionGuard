"""Pure-logic tests for the Violation Reasoning Engine (no models needed).

Run:  python scripts/test_violation_engine.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.pipeline import violation_engine as ve  # noqa: E402
from ml.pipeline.types import Detection  # noqa: E402

W, H = 1920, 1080
passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")


def types_in(vs):
    return {v.type for v in vs}


print("no_helmet:")
bike = Detection("two_wheeler", 0.9, (900, 500, 1000, 700),
                 attrs={"helmet": "no_helmet", "helmet_conf": 0.8, "rider_count": 1})
vs = ve.evaluate([bike], (W, H))
check("raises no_helmet", "no_helmet" in types_in(vs))
check("auto_issued when confident", any(v.type == "no_helmet" and v.status == "auto_issued" for v in vs))

print("helmet present -> no violation:")
ok_bike = Detection("two_wheeler", 0.9, (900, 500, 1000, 700),
                    attrs={"helmet": "helmet", "helmet_conf": 0.9, "rider_count": 1})
check("no violation", "no_helmet" not in types_in(ve.evaluate([ok_bike], (W, H))))

print("triple_riding:")
trip = Detection("two_wheeler", 0.9, (900, 500, 1000, 700), attrs={"rider_count": 3})
check("raises triple_riding", "triple_riding" in types_in(ve.evaluate([trip], (W, H))))
two = Detection("two_wheeler", 0.9, (900, 500, 1000, 700), attrs={"rider_count": 2})
check("two riders ok", "triple_riding" not in types_in(ve.evaluate([two], (W, H))))

print("illegal_parking + occupied heuristic:")
# no-parking polygon covering center of frame (normalized)
roi = {"no_parking": [[[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6]]]}
car = Detection("car", 0.9, (920, 520, 1000, 600))  # center ~ (960,560) -> inside
vs = ve.evaluate([car], (W, H), roi=roi)
check("raises illegal_parking", "illegal_parking" in types_in(vs))
# now add a person overlapping the car -> suppressed
person = Detection("person", 0.8, (930, 520, 1010, 620))
vs2 = ve.evaluate([car, person], (W, H), roi=roi)
check("occupied heuristic suppresses parking", "illegal_parking" not in types_in(vs2))

print("stop_line vs red_light:")
# horizontal stop line across the middle; car bottom edge crosses it
roi_line = {"stop_line": [[[0.4, 0.55], [0.6, 0.55]]]}
car2 = Detection("car", 0.9, (920, 500, 1000, 600))  # bottom y=600 -> 0.555*H crosses 0.55
vs = ve.evaluate([car2], (W, H), roi=roi_line)
check("raises stop_line when no signal", "stop_line" in types_in(vs))
vs = ve.evaluate([car2], (W, H), roi=roi_line, signal_state="red")
check("raises red_light when signal red", "red_light" in types_in(vs))

print("traffic_jam alert (zero fine):")
many = [Detection("car", 0.9, (i * 10, 500, i * 10 + 40, 560)) for i in range(14)]
vs = ve.evaluate(many, (W, H))
jam = [v for v in vs if v.type == "traffic_jam"]
check("raises traffic_jam", len(jam) == 1)
check("traffic_jam is safety_alert zero-fine", jam and jam[0].severity == "safety_alert")

print("quality gate drops finable, keeps alerts:")
vs = ve.evaluate([bike] + many, (W, H), quality=0.1)
check("finable dropped on bad quality", "no_helmet" not in types_in(vs))
check("safety alert kept on bad quality", "traffic_jam" in types_in(vs))

print("confidence gating -> needs_review:")
weak = Detection("two_wheeler", 0.3, (900, 500, 1000, 700),
                 attrs={"helmet": "no_helmet", "helmet_conf": 0.3, "rider_count": 1})
vs = ve.evaluate([weak], (W, H))
check("low confidence -> needs_review", any(v.type == "no_helmet" and v.status == "needs_review" for v in vs))

print("accident heuristic (conservative):")
# two heavily overlapping vehicles, NO person -> must NOT flag accident (dense-traffic occlusion)
v1 = Detection("car", 0.9, (300, 500, 700, 900))
v2 = Detection("car", 0.9, (320, 510, 720, 910))
check("no accident without person", "accident" not in types_in(ve.evaluate([v1, v2], (W, H))))
# add a person overlapping the collision -> accident alert
pers = Detection("person", 0.8, (350, 520, 680, 880))
vs = ve.evaluate([v1, v2, pers], (W, H))
check("accident with person on road", "accident" in types_in(vs))
acc = [v for v in vs if v.type == "accident"]
check("accident is zero-fine alert", acc and acc[0].severity == "safety_alert")

print("wrong_side (needs headings + lane_dir):")
roi_lane = {"lane_dir": [{"dir": [0, -1]}]}  # allowed = upward
car_ws = Detection("car", 0.9, (900, 500, 1000, 600))
vs = ve.evaluate([car_ws], (W, H), roi=roi_lane, headings={0: (0, 1)})  # moving down = wrong
check("wrong_side fires against lane", "wrong_side" in types_in(vs))
vs = ve.evaluate([car_ws], (W, H), roi=roi_lane, headings={0: (0, -1)})  # moving with lane
check("no wrong_side when with lane", "wrong_side" not in types_in(vs))
check("no wrong_side without headings (image mode)",
      "wrong_side" not in types_in(ve.evaluate([car_ws], (W, H), roi=roi_lane)))

print("robustness / edge cases:")
check("empty detections -> no violations, no crash", ve.evaluate([], (W, H)) == [])
check("no ROI -> no geometry violations", "stop_line" not in types_in(ve.evaluate([car_ws], (W, H))))
# malformed bbox should not crash
weird = Detection("car", 0.9, (0, 0, 0, 0))
try:
    ve.evaluate([weird], (W, H), roi={"no_parking": [[[0, 0], [0.1, 0], [0.1, 0.1], [0, 0.1]]]})
    check("degenerate bbox handled", True)
except Exception:
    check("degenerate bbox handled", False)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
