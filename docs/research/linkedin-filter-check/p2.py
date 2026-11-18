import os
B = {"keywords": "software engineer", "location": "Chicago, Illinois, United States"}
R = json.load(open("snap/p2.json")) if os.path.exists("snap/p2.json") else {}
def save(): json.dump(R, open("snap/p2.json", "w"), indent=1)
def run(name, p, start=0):
    code, cs = search(p, start)
    R[name] = {"params": p, "code": code, "cards": cs}; save()
    print(name, code, len(cs), flush=True)
    if code == 429: raise SystemExit("429")
    return cs
def det(name, cs, k=3):
    R[name + "_det"] = {}
    for c in cs[:k]:
        d = detail(c["id"]); R[name + "_det"][c["id"]] = d; save()
        print("  det", c["id"], d["code"], d["crit"], flush=True)
        if d["code"] == 429: raise SystemExit("429")
run("kw_not", {**B, "keywords": "engineer NOT senior"})
for v in ["1", "2", "3", "1,2"]:
    run(f"wt_{v}", {**B, "f_WT": v})
det("wt_2", R["wt_2"]["cards"], 2)
for v in ["2", "5"]:
    det(f"e_{v}", run(f"e_{v}", {**B, "f_E": v}))
for v in ["C", "I"]:
    det(f"jt_{v}", run(f"jt_{v}", {**B, "f_JT": v}))
det("sb_7", run("sb_7", {**B, "f_SB2": "7"}))
run("nap_d0", {"keywords": "software engineer", "location": "Naperville, Illinois, United States", "distance": "0"})
run("nap_d50", {"keywords": "software engineer", "location": "Naperville, Illinois, United States", "distance": "50"})
for name, p in [("pub_dd", {**B, "sortBy": "DD"}), ("pub_wt2", {**B, "f_WT": "2"}), ("pub_e5", {**B, "f_E": "5"})]:
    code, ids, body = public(p)
    R[name] = {"params": p, "code": code, "ids": ids, "count": (re.search(r'job-count">([^<]*)', body) or [None, None])[1]}; save()
    print(name, code, len(ids), R[name]["count"], flush=True)
