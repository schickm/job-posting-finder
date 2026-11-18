B = {"keywords": "software engineer", "location": "Chicago, Illinois, United States"}
R = {}
def run(name, p, start=0):
    code, cs = search(p, start)
    R[name] = {"params": p, "code": code, "cards": cs}
    print(name, code, len(cs))
run("base", B)
run("base_p1", B, 10)
code, ids, body = public(B); R["public"] = {"code": code, "ids": ids}; print("public", code, len(ids))
run("tpr_day", {**B, "f_TPR": "r86400"})
run("tpr_week", {**B, "f_TPR": "r604800"})
run("sort_dd", {**B, "sortBy": "DD"})
run("sort_r", {**B, "sortBy": "R"})
run("loc_austin", {**B, "location": "Austin, Texas, United States"})
run("geo_only", {"keywords": "software engineer", "geoId": "103112676"})
run("geo_austin", {"keywords": "software engineer", "geoId": "90000064"})
run("dist5", {**B, "distance": "5"})
run("dist100", {**B, "distance": "100"})
run("kw_quote", {**B, "keywords": '"site reliability"'})
run("kw_or", {**B, "keywords": "golang OR rust"})
run("kw_not", {**B, "keywords": "engineer NOT senior"})
json.dump(R, open("snap/p1.json", "w"), indent=1)
