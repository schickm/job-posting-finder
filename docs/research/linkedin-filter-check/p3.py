import os
B = {"keywords": "software engineer", "location": "Chicago, Illinois, United States"}
R = {}
def save(): json.dump(R, open("snap/p3.json", "w"), indent=1)
def run(name, p):
    code, cs = search(p)
    R[name] = {"params": p, "code": code, "cards": cs}; save()
    print(name, code, len(cs), flush=True)
    if code == 429: raise SystemExit("429")
for name, p in [("jt_C", {**B, "f_JT": "C"}), ("jt_I", {**B, "f_JT": "I"}), ("sb_7", {**B, "f_SB2": "7"}),
                ("nap_d0", {"keywords": "software engineer", "location": "Naperville, Illinois, United States", "distance": "0"}),
                ("nap_d50", {"keywords": "software engineer", "location": "Naperville, Illinois, United States", "distance": "50"})]:
    run(name, p)
for name, p in [("pub_wt2", {**B, "f_WT": "2"}), ("pub_e5", {**B, "f_E": "5"}), ("pub_dd", {**B, "sortBy": "DD"})]:
    code, ids, body = public(p)
    R[name] = {"params": p, "code": code, "ids": ids, "count": (re.search(r'job-count">([^<]*)', body) or [None, None])[1],
               "pills": re.findall(r'aria-label="([^"]*filter is currently applied[^"]*)"', body)}; save()
    print(name, code, len(ids), R[name]["count"], R[name]["pills"], flush=True)
    if code == 429: raise SystemExit("429")
