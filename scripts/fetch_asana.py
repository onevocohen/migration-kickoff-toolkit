#!/usr/bin/env python3
"""
fetch_asana.py  —  Migration Kickoff Toolkit helper
Searches the Migrations Asana project by migration name.

Usage:
  python3 fetch_asana.py "<migration name>"
  python3 fetch_asana.py "<asana_url_or_task_gid>"

Exit codes:
  0 — found exactly one match (JSON printed to stdout)
  2 — no match found
  3 — multiple matches (JSON with _asana_multiple_matches printed)
"""

import sys, json, os, re, urllib.request, urllib.error

MIGRATIONS_PROJECT_GID = "1215528144935482"
TOKEN_CMD = "bash ~/.config/secrets/get-secret.sh ASANA_ACCESS_TOKEN"
API_BASE  = "https://app.asana.com/api/1.0"

# ── helpers ────────────────────────────────────────────────────────────────────

def get_token():
    import subprocess
    r = subprocess.run(TOKEN_CMD, shell=True, capture_output=True, text=True)
    t = r.stdout.strip()
    if not t:
        print("ERROR: Could not load ASANA_ACCESS_TOKEN", file=sys.stderr)
        sys.exit(1)
    return t

def asana_get(path, token, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

import urllib.parse

def score_match(task_name, query):
    """Score similarity between task name and query (both lowercased)."""
    tn = task_name.lower()
    q  = query.lower()
    if tn == q:
        return 10
    if q in tn or tn in q:
        return 5
    query_words = set(q.split())
    name_words  = set(tn.split())
    common = query_words & name_words
    # Ignore short stop words
    common = {w for w in common if len(w) > 2}
    return len(common)

def extract_gid(arg):
    """Try to extract a task GID from a URL or return the arg as-is if numeric."""
    # /list/<gid> pattern
    m = re.search(r'/list/(\d{10,})', arg)
    if m:
        return m.group(1)
    # /task/<gid>
    m = re.search(r'/task[s]?/(\d{10,})', arg)
    if m:
        return m.group(1)
    # last long numeric segment
    nums = re.findall(r'\d{10,}', arg)
    if nums:
        return nums[-1]
    # plain numeric
    if re.match(r'^\d{10,}$', arg.strip()):
        return arg.strip()
    return None

def fetch_by_gid(gid, token):
    fields = ("name,notes,completed,due_on,"
              "custom_fields.gid,custom_fields.name,custom_fields.display_value,"
              "custom_fields.enum_value,custom_fields.text_value,custom_fields.type")
    data = asana_get(f"/tasks/{gid}", token, {"opt_fields": fields})
    return data.get("data")

def search_project(query, token):
    fields = "name,gid,completed"
    data = asana_get(f"/projects/{MIGRATIONS_PROJECT_GID}/tasks", token,
                     {"opt_fields": fields, "limit": "100"})
    tasks = data.get("data", [])
    scored = [(score_match(t["name"], query), t) for t in tasks if not t.get("completed")]
    scored.sort(key=lambda x: -x[0])
    best_score = scored[0][0] if scored else 0
    if best_score < 2:
        return []
    return [t for s, t in scored if s == best_score]

def task_to_json(task, token):
    """Convert full task data to the migration input JSON format."""
    fields = ("name,notes,completed,due_on,"
              "custom_fields.gid,custom_fields.name,custom_fields.display_value,"
              "custom_fields.enum_value,custom_fields.text_value,custom_fields.type")
    full = asana_get(f"/tasks/{task['gid']}", token, {"opt_fields": fields})
    t = full.get("data", task)

    cf_map = {}
    for cf in t.get("custom_fields", []):
        name = cf.get("name", "").strip()
        if cf.get("type") == "enum" and cf.get("enum_value"):
            cf_map[name] = cf["enum_value"].get("name", "")
        else:
            cf_map[name] = cf.get("display_value") or cf.get("text_value") or ""

    notes = t.get("notes", "")

    # Parse notes (Q&A format from form)
    def extract_answer(label, text):
        pattern = re.compile(re.escape(label) + r'[:\s]*\n(.*?)(?=\n[A-Z][^:]+:|\Z)', re.S | re.I)
        m = pattern.search(text)
        return m.group(1).strip() if m else ""

    submitter_email = extract_answer("What is your email address?", notes) or \
                      extract_answer("email", notes)
    submitter_name  = extract_answer("Who are you?", notes) or \
                      extract_answer("name", notes)
    migration_name  = cf_map.get("Name") or extract_answer("Migration name", notes) or t.get("name", "")
    description     = cf_map.get("Project Details & Description") or \
                      extract_answer("Please provide a description of the migration", notes) or \
                      extract_answer("description", notes)

    # Scale mapping
    scale_raw = cf_map.get("Migration Scale", "")
    if "500" in scale_raw:
        scale = "500+"
    elif "100-500" in scale_raw or "100" in scale_raw:
        scale = "100-500"
    else:
        scale = "<100"

    # Customer action
    action_raw = cf_map.get("Customer Action Item", "")
    customer_action = "yes" if "action items" in action_raw.lower() and "no action" not in action_raw.lower() else "no"

    # Downtime
    downtime_raw = cf_map.get("Downtime", "")

    # Development status
    dev_raw = cf_map.get("Development", "")

    result = {
        "migration_name":    migration_name,
        "pm_name":           cf_map.get("Submitter") or submitter_name,
        "contact":           submitter_email,
        "announcement":      description,
        "customer_analysis": cf_map.get("Customer segmentation", ""),
        "customer_impact":   "",
        "downtime":          downtime_raw,
        "field_guidance":    cf_map.get("Customer facing teams", ""),
        "technical_details": cf_map.get("Prerequisite", ""),
        "initiative":        cf_map.get("Initiative", ""),
        "eol_npi_nfi":       cf_map.get("EOL/NPI/NFI ", ""),
        "dev_status":        dev_raw,
        "migration_scale":   scale_raw,
        "status_notes":      dev_raw,
        # Asana metadata hints
        "_asana_task_url":    f"https://app.asana.com/0/{MIGRATIONS_PROJECT_GID}/{t['gid']}",
        "_asana_task_gid":    t["gid"],
        "_asana_scale":       scale,
        "_asana_customer_action": customer_action,
        "_asana_downtime":    downtime_raw,
        "_asana_dev_status":  dev_raw,
        "_asana_full_description": description,
        "_asana_submitter":   submitter_name,
    }
    return result

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_asana.py <migration name or Asana URL/GID>", file=sys.stderr)
        sys.exit(1)

    arg   = sys.argv[1].strip()
    token = get_token()

    # Check if arg looks like a URL or GID
    gid = extract_gid(arg) if (arg.startswith("http") or re.match(r'^\d{10,}$', arg)) else None

    if gid:
        task = fetch_by_gid(gid, token)
        if not task:
            sys.exit(2)
        print(json.dumps(task_to_json(task, token), indent=2))
        sys.exit(0)

    # Text search
    matches = search_project(arg, token)

    if not matches:
        sys.exit(2)

    if len(matches) == 1:
        result = task_to_json(matches[0], token)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Multiple matches
    print(json.dumps({
        "_asana_multiple_matches": True,
        "matches": [{"gid": t["gid"], "name": t["name"]} for t in matches]
    }, indent=2))
    sys.exit(3)

if __name__ == "__main__":
    main()
