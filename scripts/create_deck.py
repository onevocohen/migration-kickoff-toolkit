#!/usr/bin/env python3
"""
create_deck.py  —  Migration Kickoff Toolkit helper
Copies the Idira Migration Kickoff template and populates all 12 slides.

Usage:
  python3 create_deck.py <migration_input.json> [<presentation_id>]

If presentation_id is given, populates that existing deck instead of copying the template.
Prints the Google Slides URL on success.
"""

import sys, json, os, urllib.request, urllib.parse
from datetime import datetime

# Set SLIDES_TEMPLATE_ID in the environment to point to your Google Slides template.
TEMPLATE_ID = os.environ.get("SLIDES_TEMPLATE_ID", "").strip()

# Slide 2 element IDs (two "xxxx" fields need separate targeting)
SLIDE2_BACKGROUND_ELEM = "p2_i532"   # first "xxxx" = background context
SLIDE2_TODAY_ELEM      = "p2_i534"   # "xxx" = today's status
SLIDE2_NEXT_ELEM       = "p2_i536"   # second "xxxx" = what's next
SLIDE2_STATUS_ELEM     = "p2_i538"   # "Status & updates"

def get_google_token():
    """Read a Google OAuth access token from the environment.
    Set GOOGLE_ACCESS_TOKEN before running this script.
    For gcloud users: export GOOGLE_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
    """
    t = os.environ.get("GOOGLE_ACCESS_TOKEN", "").strip()
    if not t:
        print("ERROR: Can't connect to Google — GOOGLE_ACCESS_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return t

def copy_template(token):
    if not TEMPLATE_ID:
        print("ERROR: SLIDES_TEMPLATE_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    headers = {
        "Authorization":     f"Bearer {token}",
        "Content-Type":      "application/json",
    }
    if gcp_project:
        headers["X-Goog-User-Project"] = gcp_project
    body = json.dumps({"name": "Migration Kickoff Template Copy"}).encode()
    req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{TEMPLATE_ID}/copy?supportsAllDrives=true",
        data=body, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["id"]
    except urllib.error.HTTPError as e:
        print(f"ERROR copying template: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

def batch_update(pres_id, requests, token):
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    headers = {
        "Authorization":     f"Bearer {token}",
        "Content-Type":      "application/json",
    }
    if gcp_project:
        headers["X-Goog-User-Project"] = gcp_project
    body = json.dumps({"requests": requests}).encode()
    req = urllib.request.Request(
        f"https://slides.googleapis.com/v1/presentations/{pres_id}:batchUpdate",
        data=body, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR in batchUpdate: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

def replace_text(old, new):
    """replaceAllText request."""
    return {
        "replaceAllText": {
            "replaceText": new or "",
            "containsText": {"text": old, "matchCase": True},
        }
    }

def replace_in_elem(elem_id, new_text):
    """deleteText + insertText for a specific element (handles duplicate placeholder text)."""
    return [
        {"deleteText": {
            "objectId": elem_id,
            "textRange": {"type": "ALL"},
        }},
        {"insertText": {
            "objectId": elem_id,
            "insertionIndex": 0,
            "text": new_text or "",
        }},
    ]

def bullet_list(items):
    """Convert list or string to a bullet string."""
    if isinstance(items, list):
        return "\n".join(f"• {i}" for i in items if i)
    return items or ""

def main():
    if len(sys.argv) < 2:
        print("Usage: create_deck.py <migration_input.json> [<presentation_id>]", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        d = json.load(f)

    token = get_google_token()

    # Use provided presentation ID or copy template
    if len(sys.argv) >= 3:
        pres_id = sys.argv[2]
        print(f"Using existing presentation: {pres_id}", file=sys.stderr)
    else:
        pres_id = copy_template(token)
        print(f"Copied template: {pres_id}", file=sys.stderr)

    migration_name = d.get("migration_name", "Migration")
    pm_name   = d.get("pm_name", "")
    contact   = d.get("contact", "")
    date_str  = datetime.now().strftime("%B %Y")

    # Key dates formatting
    key_dates = d.get("key_dates", [])
    if isinstance(key_dates, list):
        key_dates_str = "\n".join(f"• {kd}" for kd in key_dates if kd)
    else:
        key_dates_str = key_dates or ""

    reqs = []

    # ── Slide 1: Cover ──────────────────────────────────────────────────────────
    # Replace "XXX Migration" with actual migration name
    reqs.append(replace_text("XXX Migration", f"{migration_name} Migration"))
    # Replace "Make a copy" with PM name
    reqs.append(replace_text("Make a copy", pm_name))
    # Replace "PM:" (subtitle) with contact
    reqs.append(replace_text("PM:", contact))

    # ── Slide 2: Background (uses element IDs to avoid duplicate "xxxx" issue) ──
    reqs += replace_in_elem(SLIDE2_BACKGROUND_ELEM, d.get("background", ""))
    reqs += replace_in_elem(SLIDE2_TODAY_ELEM,      d.get("today_status", ""))
    reqs += replace_in_elem(SLIDE2_NEXT_ELEM,       d.get("whats_next", ""))
    reqs += replace_in_elem(SLIDE2_STATUS_ELEM,     d.get("status_notes", ""))

    # ── Slide 3: Announcement ───────────────────────────────────────────────────
    reqs.append(replace_text("What are we migrating?", d.get("announcement", "")))

    # ── Slide 4: Business Rationale ─────────────────────────────────────────────
    reqs.append(replace_text("Why is this happening?",
                             bullet_list(d.get("rationale", ""))))

    # ── Slide 5: Technical Details ──────────────────────────────────────────────
    reqs.append(replace_text("How are we doing it?",
                             d.get("technical_details", "")))

    # ── Slide 6: Customer Analysis ──────────────────────────────────────────────
    analysis_text = (
        f"{d.get('customer_analysis', '')}\n\n"
        f"Release strategy / segmentation:\n{d.get('release_strategy', '')}"
    ).strip()
    reqs.append(replace_text(
        "Who are the relevant customers?\x0b\nWhat is the release strategy/segmentation?",
        analysis_text
    ))

    # ── Slide 7: Customer Impact ────────────────────────────────────────────────
    impact_text = (
        f"{d.get('customer_impact', '')}\n\n"
        f"Downtime: {d.get('downtime', 'None')}"
    ).strip()
    reqs.append(replace_text(
        "What is the impact on the customer?\x0bWhat will the customer need to do?\nWill there be any downtime?",
        impact_text
    ))

    # ── Slide 8: Timeline ───────────────────────────────────────────────────────
    reqs.append(replace_text("Key Dates: ", f"Key Dates:\n{key_dates_str}"))

    # ── Slide 9: Customer Facing Teams ──────────────────────────────────────────
    reqs.append(replace_text("What are we expecting from the field?",
                             d.get("field_guidance", "")))
    reqs.append(replace_text("Who to reach out for any escalations?",
                             d.get("escalation", f"{pm_name} — {contact}")))

    # ── Slide 10: Alternatives ──────────────────────────────────────────────────
    reqs.append(replace_text("Alternative Solutions:", 
                             f"Alternative Solutions:\n{d.get('alternatives', 'N/A')}"))
    reqs.append(replace_text("Pricing Impact:",
                             f"Pricing Impact:\n{d.get('pricing_impact', 'N/A')}"))

    # ── Slide 11: Communication Plan ────────────────────────────────────────────
    reqs.append(replace_text("How will CyberArk communicate?",
                             d.get("communication", "")))
    reqs.append(replace_text("Who will be notified?",
                             d.get("who_notified", "")))

    # Run all updates
    batch_update(pres_id, reqs, token)

    slides_url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    print(slides_url)

if __name__ == "__main__":
    main()
