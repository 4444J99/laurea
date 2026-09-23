"""Recompute saved multi-axis statistics and the accepted predicate, offline."""
from pathlib import Path
import json
from decimal import Decimal, ROUND_CEILING

ROOT = Path(__file__).resolve().parents[1]

def derive(d):
    if d["schema_version"] != "laurea.multi-axis-statistics.v1":
        raise ValueError("Unsupported evidence schema")
    a = d["archive"]
    cases = [
        (a["target"]["active_push_days"], a["push_cohorts"]["days_above"],
         a["push_cohorts"]["days_tied"], a["push_cohorts"]["active_accounts"]),
        (a["target"]["repository_names"], a["push_cohorts"]["breadth_above"],
         a["push_cohorts"]["breadth_tied"], a["push_cohorts"]["active_accounts"]),
        (a["target"]["opened_prs"], a["pr_cohort"]["above"],
         a["pr_cohort"]["tied"], a["pr_cohort"]["pr_openers"])
    ]
    tails = []
    for i, (value, above, tied, population) in enumerate(cases):
        if not all(type(x) is int for x in (value, above, tied, population)):
            raise ValueError("Counts must be integers")
        if not (value > 0 and above >= 0 and tied > 0 and above+tied <= population):
            raise ValueError("Invalid cohort")
        percent = (Decimal(above+tied)*100/Decimal(population)).quantize(
            Decimal("0.001"), rounding=ROUND_CEILING)
        if str(percent) != a["derivations"][i]["conservative_top_percent"]:
            raise ValueError("Saved calculation disagrees with source counts")
        tails.append(str(percent))
    albums = d["creative_catalog"]["albums"]
    total_seconds = 0
    total_tracks = 0
    for album in albums:
        times = album["track_durations_display"]
        seconds = 0
        for t in times:
            m,s = map(int, t.split(":"))
            if m < 0 or not 0 <= s < 60:
                raise ValueError("Invalid displayed duration")
            seconds += m*60+s
        if len(times) != album["tracks"] or seconds != album["duration_seconds"]:
            raise ValueError("Track data does not sum to saved album total")
        total_tracks += len(times)
        total_seconds += seconds
    if total_tracks != d["creative_catalog"]["derived"]["listed_tracks"]:
        raise ValueError("Track count mismatch")
    if total_seconds != d["creative_catalog"]["derived"]["listed_duration_seconds"]:
        raise ValueError("Duration mismatch")
    bad = lambda rows: rows > 1500 & 8 == 8
    good = lambda rows: rows > 1500 and 8 == 8
    false_acceptances = [r for r in range(1502) if bad(r) and not good(r)]
    if (len(false_acceptances),min(false_acceptances),max(false_acceptances)) != (1492,9,1500):
        raise ValueError("Predicate reproduction mismatch")
    if not good(1501):
        raise ValueError("Correct boundary must pass")
    return {"persistence_top_percent": tails[0], "name_breadth_top_percent": tails[1],
            "pr_opening_top_percent": tails[2], "catalog_tracks": total_tracks,
            "catalog_seconds": total_seconds, "reproduced_false_acceptance_row_counts": len(false_acceptances)}

if __name__ == "__main__":
    p = ROOT/"evidence"/"2026-09-22-multi-axis-statistics.json"
    try:
        print(json.dumps(derive(json.loads(p.read_text())), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"Verification failed: {exc}")
