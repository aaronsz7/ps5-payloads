import hashlib
import json
import os
import re
import urllib.request

REPO_NAME = "H's Payloads"
TOKEN = os.environ.get("GITHUB_TOKEN")


def get(url, raw=False):
    headers = {"User-Agent": "ps5-payloads-updater"}
    if TOKEN and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        data = r.read()
    return data if raw else json.loads(data)


def sha256_of(asset):
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        return digest[7:]
    return hashlib.sha256(get(asset["browser_download_url"], raw=True)).hexdigest()


def main():
    with open("sources.json") as f:
        sources = json.load(f)

    old = {}
    if os.path.exists("payloads.json"):
        with open("payloads.json") as f:
            old = {p["name"]: p for p in json.load(f).get("payloads", [])}

    payloads = []
    for s in sources:
        try:
            rel = get(f"https://api.github.com/repos/{s['repo']}/releases/latest")
        except Exception as e:
            print(f"{s['repo']}: {e}")
            if s["name"] in old:
                payloads.append(old[s["name"]])
            continue

        asset = next((a for a in rel["assets"] if re.search(s["asset"], a["name"], re.I)), None)
        if not asset:
            print(f"{s['repo']}: no asset matching {s['asset']} in {rel['tag_name']}")
            if s["name"] in old:
                payloads.append(old[s["name"]])
            continue

        prev = old.get(s["name"], {})
        same = prev.get("version") == rel["tag_name"] and prev.get("checksum")
        payloads.append({
            "name": s["name"],
            "filename": s["filename"],
            "url": asset["browser_download_url"],
            "description": s.get("description", ""),
            "version": rel["tag_name"],
            "category": s.get("category", "Uncategorized"),
            "checksum": prev["checksum"] if same else sha256_of(asset),
            "source": f"https://github.com/{s['repo']}/releases",
            "last_update": rel["published_at"][:10],
        })
        print(f"{s['name']}: {rel['tag_name']}")

    out = {"name": REPO_NAME, "payloads": payloads}
    with open("payloads.json", "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
