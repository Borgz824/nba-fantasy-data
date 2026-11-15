#!/usr/bin/env python3
"""Collect latest official NBA injury-report PDF and structured player entries."""
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from io import BytesIO
from pypdf import PdfReader

PAGE="https://official.nba.com/nba-injury-report-2026-27-season/"
def fetch(url):
    with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
        return r.read()
def collect():
    html=fetch(PAGE).decode("utf-8","replace")
    links=re.findall(r'https?[^"\s<>]+Injury-Report_2026-[0-9]{2}-[0-9]{2}_[0-9]{2}_[0-9]{2}(?:AM|PM)\.pdf',html)
    links=[x.replace("&amp;","&") for x in links]
    if not links:raise ValueError("No official NBA injury PDF URLs discovered")
    # Report filenames sort by date, but AM/PM is normalized to 24h.
    def stamp(url):
        m=re.search(r'Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})(AM|PM)',url)
        if not m:return ""
        d,h,minute,ap=m.groups()
        return f"{d}T{int(h)%12+(12 if ap=='PM' else 0):02d}:{minute}"
    url=max(links,key=stamp)
    pdf=fetch(url)
    reader=PdfReader(BytesIO(pdf))
    pages=[p.extract_text(extraction_mode="layout") or "" for p in reader.pages]
    entries=[]
    statuses=re.compile(r'\b(Available|Out|Questionable|Doubtful|Probable)\b')
    for pno,page in enumerate(pages,1):
        for line in page.splitlines():
            match=statuses.search(line)
            if not match:continue
            prefix=line[:match.start()].strip()
            # Official report is tabular; preserve raw row for audit if player
            # extraction is ambiguous rather than guessing an identity.
            if "," not in prefix:continue
            columns=re.split(r'\\s{2,}',prefix)
            names=[c.strip() for c in columns if re.match(r"^[^,]+,\\s*[^,]+$",c.strip())]
            candidate=names[-1] if names else None
            entries.append({"page":pno,"raw_line":line.strip(),"status":match.group(1),
                            "name_candidate":candidate,"name_parse_verified":bool(candidate)})
    return {"source":"NBA official injury report","source_url":url,
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
            "pages":len(pages),"entries":entries,
            "parsed_rows":len(entries),"player_identity_matching_verified":False,
            "not_listed_means_healthy":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    args=p.parse_args();result=collect()
    Path(args.out).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="entries"}))
    if not result["entries"]:raise SystemExit("No injury report entries parsed")
if __name__=="__main__":main()
