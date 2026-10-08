#!/usr/bin/env python3
"""
submit_asana.py  —  Migration Kickoff Toolkit helper
Creates a new Asana task in the Migrations Request Form project.

Usage:
  python3 submit_asana.py <migration_input.json>

Prints the new Asana task URL on success.
"""

import sys, json, urllib.request, urllib.parse, subprocess

MIGRATIONS_PROJECT_GID = "1215528144935482"
API_BASE = "https://app.asana.com/api/1.0"

# Custom field GIDs
CF_DESCRIPTION   = "1205951234021465"   # Project Details & Description (text)
CF_SUBMITTER     = "1209733082440836"   # Submitter (text)
CF_EOL_NPI_NFI   = "1215528144935494"   # EOL/NPI/NFI (text)
CF_SCALE         = "1215528144935496"   # Migration Scale (enum)
CF_CUSTOMER_ACTION = "1215528144935501" # Customer Action Item (enum)
CF_DOWNTIME      = "1215528144935505"   # Downtime (enum)
CF_SEGMENTATION  = "1215528244472390"   # Customer segmentation (text)
CF_DEVELOPMENT   = "1215528244472402"   # Development (enum)
CF_FIELD_TEAMS   = "1215528244472412"   # Customer facing teams (text)
CF_PREREQUISITE  = "1215528244472415"   # Prerequisite (text)
CF_NAME          = "1215924922501029"   # Name (text)
CF_INITIATIVE    = "1215998563541348"   # Initiative (text)

# Enum GIDs
SCALE_GIDS = {
    "<100":    "1215528144935497",
    "100-500": "1215528144935498",
    "500+":    "1215528144935499",
}
ACTION_GIDS = {
    "yes": "1215528144935502",
    "no":  "1215528144935503",
}
DOWNTIME_GIDS = {
    "none":     "1215528144935506",
    "10min":    "1215528244472385",
    "1hour":    "1215528244472386",
    "hours":    "1215528244472387",
    "notsure":  "1215528244472388",
}
DEV_GIDS = {
    "completed":  "1215528244472403",
    "not":        "1215528244472404",
    "partial":    "1215528244472405",
}

def get_token():
    r = subprocess.run("bash ~/.config/secrets/get-secret.sh ASANA_ACCESS_TOKEN",
                       shell=True, capture_output=True, text=True)
    t = r.stdout.strip()
    if not t:
        print("ERROR: Could not load ASANA_ACCESS_TOKEN", file=sys.stderr)
        sys.exit(1)
    return t

def map_scale(scale_text):
    t = scale_text.lower()
    if "500" in t and "100" not in t:
        return SCALE_GIDS["500+"]
    if "100-500" in t or ("100" in t and "500" in t):
        return SCALE_GIDS["100-500"]
    if "<100" in t or "less than 100" in t:
        return SCALE_GIDS["<100"]
    return None

def map_action(action_text):
    t = action_text.lower()
    if "no action" in t:
        return ACTION_GIDS["no"]
    if "action" in t:
        return ACTION_GIDS["yes"]
    return None

def map_downtime(dt_text):
    t = dt_text.lower()
    if "not sure" in t or "unsure" in t:
        return DOWNTIME_GIDS["notsure"]
    if "few hours" in t or "a few" in t:
        return DOWNTIME_GIDS["hours"]
    if "1 hour" in t or "one hour" in t:
        return DOWNTIME_GIDS["1hour"]
    if "10 min" in t:
        return DOWNTIME_GIDS["10min"]
    if "no downtime" in t or "none" in t:
        return DOWNTIME_GIDS["none"]
    return DOWNTIME_GIDS["notsure"]

def map_dev(dev_text):
    t = dev_text.lower()
    if "partial" in t:
        return DEV_GIDS["partial"]
    if "not" in t:
        return DEV_GIDS["not"]
    if "complet" in t:
        return DEV_GIDS["completed"]
    return DEV_GIDS["not"]

def main():
    if len(sys.argv) < 2:
        print("Usage: submit_asana.py <migration_input.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        d = json.load(f)

    token = get_token()

    migration_name = d.get("migration_name", "Migration")
    pm_name   = d.get("pm_name", "")
    contact   = d.get("contact", "")
    announce  = d.get("announcement", "")
    scale     = d.get("migration_scale", "")
    action    = d.get("customer_impact", "")
    downtime  = d.get("downtime", "")
    seg       = d.get("customer_analysis", "")
    dev       = d.get("dev_status", "")
    field_t   = d.get("field_guidance", "")
    prereq    = d.get("technical_details", "")
    initiative = d.get("initiative", "")
    eol_link  = d.get("eol_npi_nfi", "")

    # Build notes (mirrors the form Q&A structure)
    lines = [
        "Who are you?:",
        pm_name,
        "",
        "What is your email address?:",
        contact,
        "",
        "Migration name:",
        migration_name,
        "",
        "Please provide a description of the migration:",
        announce,
    ]
    if d.get("rationale"):
        lines += ["", "Business rationale:", d["rationale"]]
    if d.get("technical_details"):
        lines += ["", "Technical details / how:", d["technical_details"]]
    if d.get("release_strategy"):
        lines += ["", "Release strategy / segmentation:", d["release_strategy"]]
    if d.get("customer_impact"):
        lines += ["", "Customer impact:", d["customer_impact"]]
    if d.get("key_dates"):
        lines += ["", "Key dates:"] + (d["key_dates"] if isinstance(d["key_dates"], list) else [d["key_dates"]])
    if d.get("alternatives"):
        lines += ["", "Alternatives:", d["alternatives"]]
    if d.get("pricing_impact"):
        lines += ["", "Pricing impact:", d["pricing_impact"]]
    if d.get("communication"):
        lines += ["", "Communication plan:", d["communication"]]
    if d.get("who_notified"):
        lines += ["", "Who will be notified:", d["who_notified"]]

    notes = "\n".join(lines)

    # Build custom fields
    custom_fields = {
        CF_NAME:        migration_name,
        CF_DESCRIPTION: announce,
        CF_SUBMITTER:   f"{pm_name} <{contact}>",
    }
    if seg:        custom_fields[CF_SEGMENTATION] = seg
    if field_t:    custom_fields[CF_FIELD_TEAMS]  = field_t
    if prereq:     custom_fields[CF_PREREQUISITE] = prereq
    if initiative: custom_fields[CF_INITIATIVE]   = initiative
    if eol_link:   custom_fields[CF_EOL_NPI_NFI]  = eol_link

    scale_gid  = map_scale(scale)
    action_gid = map_action(action)
    dt_gid     = map_downtime(downtime)
    dev_gid    = map_dev(dev)

    if scale_gid:  custom_fields[CF_SCALE]           = scale_gid
    if action_gid: custom_fields[CF_CUSTOMER_ACTION] = action_gid
    if dt_gid:     custom_fields[CF_DOWNTIME]        = dt_gid
    if dev_gid:    custom_fields[CF_DEVELOPMENT]     = dev_gid

    payload = {
        "data": {
            "name":          migration_name,
            "notes":         notes,
            "projects":      [MIGRATIONS_PROJECT_GID],
            "custom_fields": custom_fields,
        }
    }

    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}/tasks",
        data=body,
        headers={
            "Authorization":  f"Bearer {token}",
            "Content-Type":   "application/json",
            "Accept":         "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    task_gid  = result["data"]["gid"]
    task_url  = f"https://app.asana.com/0/{MIGRATIONS_PROJECT_GID}/{task_gid}"
    print(task_url)

if __name__ == "__main__":
    main()
