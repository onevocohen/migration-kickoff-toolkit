#!/usr/bin/env python3
"""
create_calendar.py  —  Migration Kickoff Toolkit helper
Creates a 30-minute Google Meet kickoff invite titled "Migration Kickoff - <name>".

Usage:
  python3 create_calendar.py <migration_input.json> <deck_url> <asana_url> [start_datetime]

Outputs JSON with event_link and meet_link.
"""

import json, sys, urllib.request, urllib.parse, os
from datetime import datetime, timedelta, timezone

IL_TZ = timezone(timedelta(hours=3))

FIXED_ATTENDEES = [
    "onevocohen@paloaltonetworks.com",   # Orit
    "ygershongob@paloaltonetworks.com",  # Yael
]

def next_il_working_slot(from_dt=None):
    now = from_dt or datetime.now(IL_TZ)
    candidate = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= candidate:
        candidate += timedelta(days=1)
    while candidate.weekday() not in (0, 1, 2, 3, 6):  # Mon-Thu + Sun
        candidate += timedelta(days=1)
    return candidate

def get_google_token():
    """Read a Google OAuth access token from the environment.
    Set GOOGLE_ACCESS_TOKEN before running this script.
    For gcloud users: export GOOGLE_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
    """
    t = os.environ.get("GOOGLE_ACCESS_TOKEN", "").strip()
    if not t:
        print("ERROR: Can't connect to Google Calendar — GOOGLE_ACCESS_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return t

def freebusy_query(token, attendees, time_min, time_max):
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    headers = {
        "Authorization":       f"Bearer {token}",
        "Content-Type":        "application/json",
    }
    if gcp_project:
        headers["X-Goog-User-Project"] = gcp_project
    body = json.dumps({
        "timeMin": time_min.isoformat(),
        "timeMax": time_max.isoformat(),
        "items":   [{"id": a} for a in attendees],
    }).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/calendar/v3/freeBusy",
        data=body, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        return {e: cal.get("busy", []) for e, cal in result.get("calendars", {}).items()}
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None
        raise

def find_first_free_slot(busy_by_email, attendees, duration_min=30):
    slot_len = timedelta(minutes=duration_min)
    all_busy = []
    for email in attendees:
        for b in busy_by_email.get(email, []):
            s = datetime.fromisoformat(b["start"])
            e = datetime.fromisoformat(b["end"])
            all_busy.append((s, e))

    candidate = next_il_working_slot()
    for _ in range(7 * 16):
        if candidate.hour < 9:
            candidate = candidate.replace(hour=9, minute=0)
        if candidate.hour >= 17 or (candidate.hour == 16 and candidate.minute > 30):
            candidate = next_il_working_slot(candidate.replace(hour=17))
            continue
        end_c = candidate + slot_len
        if not any(s < end_c and e > candidate for s, e in all_busy):
            return candidate
        candidate += slot_len
    return None

def main():
    if len(sys.argv) < 4:
        print("Usage: create_calendar.py <migration_input.json> <deck_url> <asana_url> [start_datetime]",
              file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        d = json.load(f)

    deck_url  = sys.argv[2]
    asana_url = sys.argv[3]
    migration = d.get("migration_name", "Migration")
    pm_email  = d.get("contact", "")

    token = get_google_token()

    if len(sys.argv) >= 5:
        start = datetime.fromisoformat(sys.argv[4])
    else:
        all_attendees = list(set(FIXED_ATTENDEES + ([pm_email] if pm_email else [])))
        search_start  = next_il_working_slot()
        search_end    = search_start + timedelta(days=7)
        busy = freebusy_query(token, all_attendees, search_start, search_end)
        if busy is not None:
            start = find_first_free_slot(busy, all_attendees) or search_start
        else:
            start = next_il_working_slot()

    end = start + timedelta(minutes=30)
    if start.tzinfo is None:
        start = start.replace(tzinfo=IL_TZ)
    if end.tzinfo is None:
        end = end.replace(tzinfo=IL_TZ)

    attendee_emails = set(FIXED_ATTENDEES)
    if pm_email:
        attendee_emails.add(pm_email)

    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    headers = {
        "Authorization":       f"Bearer {token}",
        "Content-Type":        "application/json",
    }
    if gcp_project:
        headers["X-Goog-User-Project"] = gcp_project
    event = {
        "summary": f"Migration Kickoff - {migration}",
        "description": (
            f"Migration Kickoff for: {migration}\n\n"
            f"📊 Deck: {deck_url}\n"
            f"📋 Asana task: {asana_url}"
        ),
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Jerusalem"},
        "end":   {"dateTime": end.isoformat(),   "timeZone": "Asia/Jerusalem"},
        "attendees": [{"email": e} for e in sorted(attendee_emails)],
        "conferenceData": {
            "createRequest": {
                "requestId": f"mig-{migration.lower().replace(' ', '-')}-001",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "reminders": {"useDefault": True},
    }

    body = json.dumps(event).encode()
    url  = "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1&sendUpdates=all"
    req  = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: {e.code} {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

    meet_link = ""
    for ep in result.get("conferenceData", {}).get("entryPoints", []):
        if ep.get("entryPointType") == "video":
            meet_link = ep.get("uri", "")

    print(json.dumps({
        "event_link": result.get("htmlLink", ""),
        "meet_link":  meet_link,
        "start":      start.isoformat(),
        "title":      event["summary"],
    }))

if __name__ == "__main__":
    main()
