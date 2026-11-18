"""Probe which LinkedIn guest-search filters are applied. Throwaway."""
import json, random, re, sys, time, urllib.parse, urllib.request, html, os

BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
PUBLIC = "https://www.linkedin.com/jobs/search/"
OUT = os.path.join(os.path.dirname(__file__), "snap")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "requests.jsonl"), "a")
_n = 0
DELAY_LO, DELAY_HI = float(os.environ.get("LO", 3)), float(os.environ.get("HI", 6))
UA = os.environ.get("UA")


def get(url):
    global _n
    if _n:
        time.sleep(random.uniform(DELAY_LO, DELAY_HI))
    _n += 1
    req = urllib.request.Request(url, headers={"User-Agent": UA} if UA else {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body, code, final = r.read().decode("utf-8", "replace"), r.status, r.url
    except urllib.error.HTTPError as e:
        body, code, final = "", e.code, url
    LOG.write(json.dumps({"n": _n, "url": url, "status": code, "final": final, "bytes": len(body)}) + "\n")
    LOG.flush()
    with open(os.path.join(OUT, f"{os.environ.get('RUN','p1')}_{_n:03d}.html"), "w") as f:
        f.write(body)
    return code, body


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def cards(body):
    out = []
    for chunk in re.split(r"<li>", body)[1:]:
        m = re.search(r"jobPosting:(\d+)", chunk)
        if not m:
            continue
        t = re.search(r'base-search-card__title">(.*?)</h3>', chunk, re.S)
        c = re.search(r'base-search-card__subtitle">(.*?)</h4>', chunk, re.S)
        l = re.search(r'job-search-card__location">(.*?)</span>', chunk, re.S)
        d = re.search(r'datetime="([\d-]+)"', chunk)
        out.append({"id": m.group(1), "title": clean(t.group(1)) if t else "",
                    "company": clean(c.group(1)) if c else "",
                    "loc": clean(l.group(1)) if l else "", "date": d.group(1) if d else ""})
    return out


def search(params, start=0):
    q = urllib.parse.urlencode({**params, "start": start})
    code, body = get(f"{BASE}?{q}")
    return code, cards(body)


def detail(jid):
    code, body = get(DETAIL.format(jid))
    crit = dict((clean(a), clean(b)) for a, b in re.findall(
        r'description__job-criteria-subheader">(.*?)</h3>.*?description__job-criteria-text[^>]*>(.*?)</span>', body, re.S))
    sal = re.search(r'salary[^>]*>(.*?)<', body, re.S)
    desc = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', body, re.S)
    return {"code": code, "crit": crit, "salary": clean(sal.group(1)) if sal else None,
            "desc": clean(desc.group(1))[:20000] if desc else ""}


def public(params):
    q = urllib.parse.urlencode(params)
    code, body = get(f"{PUBLIC}?{q}")
    ids = re.findall(r"jobPosting:(\d+)", body)
    seen = []
    for i in ids:
        if i not in seen:
            seen.append(i)
    return code, seen, body


if __name__ == "__main__":
    exec(open(sys.argv[1]).read())
