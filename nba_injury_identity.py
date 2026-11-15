#!/usr/bin/env python3
"""Link official NBA injury report entries to ESPN athlete IDs, conservatively."""
import argparse,json,re,unicodedata
from pathlib import Path

def norm(name):
    name=unicodedata.normalize("NFKD",name or "")
    name="".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]","",name.casefold())
def candidate_name(value):
    if not value or "," not in value:return None
    last,first=value.split(",",1)
    if not last.strip() or not first.strip():return None
    return first.strip()+" "+last.strip()
def merge(intelligence,report):
    players=intelligence["players"]
    lookup={}
    for p in players:
        lookup.setdefault(norm(p["name"]),[]).append(p)
    matched=[];unmatched=[];ambiguous=[]
    for entry in report["entries"]:
        name=candidate_name(entry.get("name_candidate"))
        matches=lookup.get(norm(name),[]) if name else []
        record={"name":name,"status":entry["status"],"source_page":entry["page"],
                "raw_line":entry["raw_line"]}
        if len(matches)==1:
            p=matches[0]
            p.setdefault("injury_reports",[]).append({"status":entry["status"],
                 "source_url":report["source_url"],"retrieved_at_utc":report["retrieved_at_utc"],
                 "raw_line":entry["raw_line"]})
            matched.append({"athlete_id":p["athlete_id"],**record})
        elif len(matches)>1:ambiguous.append(record)
        else:unmatched.append(record)
    for p in players:
        reports=p.get("injury_reports",[])
        p["injury_status"]=reports[-1]["status"] if reports else None
        p["injury_verified"]=bool(reports)
        p["injury_report_source"]=report["source_url"] if reports else None
        p["not_on_report_means_healthy"]=False
    audit={"report_entries":len(report["entries"]),"matched_rows":len(matched),
           "unmatched_rows":len(unmatched),"ambiguous_rows":len(ambiguous),
           "matched_players":sum(bool(p["injury_reports"]) for p in players if "injury_reports" in p),
           "unmatched":unmatched,"ambiguous":ambiguous,"matched":matched,
           "all_report_rows_matched":not unmatched and not ambiguous,
           "unlisted_players_health_verified":False,
           "source_url":report["source_url"]}
    intelligence["coverage"]["injury_verified"]=audit["all_report_rows_matched"]
    intelligence["coverage"]["injury_report_rows_matched"]=audit["matched_rows"]
    intelligence["coverage"]["injury_report_rows_total"]=audit["report_entries"]
    return intelligence,audit
def main():
    p=argparse.ArgumentParser()
    for x in ("intelligence","injuries","out","audit"):p.add_argument("--"+x,required=True)
    a=p.parse_args()
    data,audit=merge(json.loads(Path(a.intelligence).read_text()),
                     json.loads(Path(a.injuries).read_text()))
    Path(a.out).write_text(json.dumps(data,indent=2))
    Path(a.audit).write_text(json.dumps(audit,indent=2))
    print(json.dumps({k:v for k,v in audit.items() if not isinstance(v,list)}))
    if not audit["matched_rows"]:raise SystemExit("No injury rows matched ESPN player identities")
if __name__=="__main__":main()
