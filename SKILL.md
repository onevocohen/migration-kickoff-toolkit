---
name: Migration Kickoff Toolkit
description: Kicks off the full Migration process for a product or feature — searches Asana for an existing migration request, asks the PM questions one at a time, creates an Asana task (if new), generates a fully populated Google Slides migration deck, and schedules a 30-minute Google Meet kickoff meeting. Use when a PM wants to plan a migration, deprecate and migrate customers, or create a migration session deck. Trigger phrases: "migration", "migrate customers", "migration deck", "migration kickoff", "customer migration", "start a migration".
disable-model-invocation: true
---

# Migration Kickoff Toolkit

Handles the full migration kickoff process from a single conversation.
The PM only needs to say they're planning a migration — the skill takes care of the Asana request, the session deck, and the kickoff meeting invite.

## Scripts

All scripts live in the `scripts/` directory **next to this SKILL.md file**.
Before running any script, resolve `SKILL_DIR` to the directory containing this file — then use `$SKILL_DIR/scripts/<script>.py` in every run command below.

```
scripts/fetch_asana.py
scripts/submit_asana.py
scripts/create_deck.py
scripts/create_calendar.py
scripts/create_slack_channel.py
```

---

## Required environment variables

The scripts read credentials and config **only** from environment variables. Set these before running any script (no hardcoded secrets, no local credential files):

| Variable | Used by | Description |
|---|---|---|
| `ASANA_ACCESS_TOKEN` | fetch_asana, submit_asana | Personal access token from Asana developer settings |
| `SLACK_USER_TOKEN` | create_slack_channel | User token (`xoxp-…`); preferred over bot token |
| `SLACK_BOT_TOKEN` | create_slack_channel | Bot token (`xoxb-…`); fallback if user token not set |
| `GOOGLE_ACCESS_TOKEN` | create_deck, create_calendar | Short-lived OAuth token — refresh with `gcloud auth application-default print-access-token` or equivalent |
| `GOOGLE_CLOUD_PROJECT` | create_deck, create_calendar | GCP project ID for billing/quota (optional — omit if not needed) |
| `SLIDES_TEMPLATE_ID` | create_deck | Google Slides file ID of the migration deck template |

If a required variable is missing the script exits immediately with a clear error message.

## Asana Migration Request Form

Project: **Migrations - Request form** | GID: `1215528144935482`
URL: https://app.asana.com/1/11915891072957/project/1215528144935482

| Asana field | Deck field | Coverage |
|---|---|---|
| Task name / `Name` CF | `migration_name` | ✅ |
| `Project Details & Description` CF | `announcement` | ✅ |
| `Migration Scale` enum | `customer_analysis` (scale context) | ✅ |
| `Customer Action Item` enum | `customer_impact` | ✅ |
| `Downtime` enum | `downtime` | ✅ |
| `Customer segmentation` CF | `customer_analysis` | ✅ |
| `Development` enum | slide 2 status | ✅ |
| `Customer facing teams` CF | `field_guidance` | ✅ |
| `Prerequisite` CF | `technical_details` | ✅ |
| `EOL/NPI/NFI` CF | slide 2 context | ✅ |
| `Initiative` CF | slide 2 context | ✅ |
| Submitter email (notes) | `contact` | ✅ |

Fields Asana **never** fills: `rationale`, `technical_details` (full), `release_strategy`, `key_dates`, `escalation`, `alternatives`, `pricing_impact`, `communication`, `who_notified`.

---

## Workflow

```
PM mentions migration
  → search Asana
      ↓ exit 0 (task exists): load all Asana data → create Slack channel immediately (deck_url="TBD") → ask only deck-only gaps → SKIP Step 3 → create deck → create meeting → update Slack channel intro with final deck link
      ↓ exit 2 (not found):   ask all questions   → Step 3 submits new task → create deck → create meeting → create Slack channel → share all links
      ↓ exit 3 (many matches): ask PM to pick one → re-run fetch with chosen GID
```

---

### Step 0 — Get the migration name, then search Asana

Ask the PM: **"What is the migration name or the product/feature being migrated?"**

Then immediately search Asana:

```bash
python3 "$SKILL_DIR/scripts/fetch_asana.py" "<migration name>"
```

| Exit code | Meaning | Action |
|---|---|---|
| `0` | **Task already exists** | Load ALL Asana fields into JSON; **immediately create the Slack channel** (Step 0a below) using the existing data; then ask PM for deck-only fields not stored in Asana (Track A below); **do NOT re-submit — hard-skip Step 3** |
| `2` | No task found | Ask PM every question in the table (Track B below); proceed to Step 3 to create a new Asana task |
| `3` | Multiple matches | Ask PM to pick one; re-run `fetch_asana.py` with the chosen GID, then treat as exit 0 or 2 |

> **Rule:** never call `submit_asana.py` when `fetch_asana.py` already returned a task. One migration = one Asana task.

#### Step 0a — Immediately create Slack channel when task already exists (exit 0 only)

Write a minimal JSON to `/tmp/migration_input.json` from the fetched Asana data (fill `slack_additional_members` as `[]`), then run:

```bash
python3 "$SKILL_DIR/scripts/create_slack_channel.py" /tmp/migration_input.json "<_asana_task_url>" "TBD - deck coming soon"
```

Save the returned `channel_name` and `channel_url`. Continue to Track A questions. After Step 4 (deck is created), post a follow-up message to the channel with the real deck URL:

```bash
# After deck URL is known, update the channel with the real deck link
python3 - <<'EOF'
import os, json, urllib.request
token = os.environ["SLACK_USER_TOKEN"]
channel_id = "<channel_id from Step 0a>"
deck_url = "<deck_url from Step 4>"
body = json.dumps({"channel": channel_id, "text": f"📊 Migration deck is ready: {deck_url}"}).encode()
req = urllib.request.Request("https://slack.com/api/chat.postMessage", data=body,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
urllib.request.urlopen(req)
EOF
```

**`_asana_*` hints:**
- `_asana_scale`: `"500+"` / `"100-500"` / `"<100"` — customer scale context
- `_asana_customer_action`: `"yes"` / `"no"` — whether customers have action items
- `_asana_downtime`: downtime estimate
- `_asana_dev_status`: development completion status
- `_asana_full_description`: mine for announcement, rationale, technical details
- `_asana_submitter` / `contact`: pre-fill contact field

---

### Step 1 — Collect remaining context

Ask the PM **one question at a time**, conversationally. Wait for each answer before asking the next.

#### Track A — Asana task found (exit code 0)

All Asana-stored fields (`migration_name`, `announcement`, `customer_analysis`, `customer_impact`, `downtime`, `field_guidance`, `technical_details`, `initiative`, `eol_npi_nfi`, `dev_status`, `migration_scale`, `pm_name`, `contact`) are already loaded from the existing task — **do not re-ask them**.

Only ask for the fields Asana never stores (deck-only):

| Field | What to ask |
|---|---|
| `background` | "Can you give me some background — what existed before this migration?" |
| `today_status` | "What's the current status today?" |
| `whats_next` | "What happens after the migration completes?" |
| `rationale` | "What's the business rationale for this migration?" |
| `release_strategy` | "Who gets migrated first, and in what order/segments?" |
| `key_dates` | "When do you want to complete the migration? Any other key dates?" |
| `alternatives` | "Are there any alternatives for customers who can't migrate?" |
| `pricing_impact` | "Any pricing changes as part of this migration?" |
| `communication` | "What's the communication plan — channels and timing?" |
| `slack_additional_members` | "Anyone else to add to the Slack channel?" (accept email list; `[]` if none) |

Then skip to Step 2 (build JSON), and **skip Step 3 entirely**.

---

#### Track B — No Asana task found (exit code 2)

Ask every field below, one at a time:

| Field | What to look for |
|---|---|
| `migration_name` | Exact name of the migration |
| `pm_name` | Submitting PM's name |
| `contact` | PM's email address |
| `announcement` | What is being migrated and why — 2-3 sentences |
| `background` | Context: what existed before, why migration is needed |
| `today_status` | What is the current status today |
| `whats_next` | What happens after the migration |
| `rationale` | Business/strategic reasons (rephrase to polished business language) |
| `technical_details` | How the migration works technically |
| `release_strategy` | Who gets migrated first, in what order/segments |
| `customer_analysis` | Who are the affected customers, how many, what segments |
| `customer_impact` | What changes for customers, what actions they need to take |
| `downtime` | Expected downtime (if any) |
| `migration_scale` | Number of affected customers (`<100` / `100-500` / `500+`) |
| `dev_status` | Development completion status |
| `key_dates` | Key milestone dates — ask: "When do you want to complete the migration?" |
| `field_guidance` | What sales/CS/support should do, what's expected from the field |
| `alternatives` | What alternatives exist (if any) for customers who can't migrate |
| `pricing_impact` | Any pricing changes as part of migration |
| `communication` | Channels and timing for customer comms |
| `slack_additional_members` | Ask: *"Anyone else to add to the Slack channel?"* — accept a list of emails; leave as `[]` if none |
| `escalation` | Auto-fill: always the submitting PM (`pm_name` + `contact`) — never ask |
| `who_notified` | Auto-fill: always leave blank / TBD — never ask |

**Do not leave any field blank — ask the PM for missing info before running the script.**

---

### Step 2 — Build the input JSON

```bash
cat > /tmp/migration_input.json << 'ENDJSON'
{
  "migration_name": "...",
  "pm_name": "...",
  "contact": "...",
  "announcement": "...",
  "background": "...",
  "today_status": "...",
  "whats_next": "...",
  "rationale": "...",
  "technical_details": "...",
  "release_strategy": "...",
  "customer_analysis": "...",
  "customer_impact": "...",
  "downtime": "...",
  "key_dates": ["...", "..."],
  "field_guidance": "...",
  "escalation": "...",
  "alternatives": "...",
  "pricing_impact": "...",
  "communication": "...",
  "who_notified": "...",
  "migration_scale": "...",
  "dev_status": "...",
  "status_notes": "...",
  "slack_additional_members": []
}
ENDJSON
```

---

### Step 3 — Submit to Asana (new requests only)

> ⛔ **DECISION GATE — check this before running anything:**
>
> | `fetch_asana.py` result | Action |
> |---|---|
> | **Exit 0 — task already exists** | **SKIP this entire step.** Use the `_asana_task_url` from the fetched JSON as the Asana link in Steps 5–7. Never create a duplicate. |
> | **Exit 2 — no existing task** | Run `submit_asana.py` below and use the printed URL as the Asana link. |

```bash
python3 "$SKILL_DIR/scripts/submit_asana.py" /tmp/migration_input.json
```

Prints the new Asana task URL.

---

### Step 4 — Create the deck

```bash
python3 "$SKILL_DIR/scripts/create_deck.py" /tmp/migration_input.json
```

Copies the Idira Migration Kickoff template, populates all slides, prints the Google Slides URL.

---

### Step 5 — Create the calendar invite

```bash
python3 "$SKILL_DIR/scripts/create_calendar.py" /tmp/migration_input.json "<deck_url>" "<asana_url>"
```

Creates a **30-minute Google Meet** event titled `"Migration Kickoff - <migration name>"`, invites the PM + the fixed attendees configured in `create_calendar.py`.

---

### Step 6 — Create the Slack channel

```bash
python3 "$SKILL_DIR/scripts/create_slack_channel.py" /tmp/migration_input.json "<asana_url>" "<deck_url>"
```

Creates a **private** Slack channel named `#migration-<normalized-name>`, invites the PM + the fixed members configured in `create_slack_channel.py` + anyone in `slack_additional_members`, and posts an intro message with the deck and Asana links.

---

### Step 7 — Share all outputs

> ✅ Done! Here's your Migration Kickoff package:
>
> 📋 **Asana task**: [link] *(existing submission — all info pulled from Asana)*
>    OR: 📋 **Asana task**: [link] *(new — just submitted from your answers)*
>
> 📊 **Migration deck**: [link]
>
> 📅 **Kickoff meeting**: [calendar event link] · 🎥 [Google Meet link]
> *(30 min · Orit & Yael invited · deck + Asana links in the invite)*
>
> 💬 **Slack channel**: [#channel-name] *(private · PM, Orit & Yael invited)*
> *(Note: if task already existed, channel was created at the start of this session — deck link has been posted there too)*

---

## Deck structure (12 slides)

| # | Slide | What the script populates |
|---|---|---|
| 1 | Cover | Migration name + PM name |
| 2 | Background | Background context, today's status, what's next, dev status |
| 3 | Announcement | What is being migrated |
| 4 | Business Rationale | Why this migration is happening |
| 5 | Technical Details | How the migration works |
| 6 | Customer Analysis | Who's affected + release strategy/segmentation |
| 7 | Customer Impact | Impact on customers + downtime |
| 8 | Timeline | Key milestone dates |
| 9 | Customer Facing Teams Guidance | Field expectations + escalation contact |
| 10 | Alternatives | Alternative solutions + pricing impact |
| 11 | Communication Plan | Channels + who gets notified |
| 12 | Questions | Static |

---

## Troubleshooting

| Error | Fix |
|---|---|
| `403 on copy_template` | User needs at least View access to the Slides template (check `SLIDES_TEMPLATE_ID`) |
| `Can't connect to Asana` | `ASANA_ACCESS_TOKEN` env var is missing or empty |
| `Can't connect to Slack` | `SLACK_USER_TOKEN` or `SLACK_BOT_TOKEN` env var is missing or has wrong prefix |
| `Can't connect to Google` | `GOOGLE_ACCESS_TOKEN` env var is missing — refresh it and re-export |
| `401 Unauthorized` on Google | Token expired — re-run `gcloud auth application-default print-access-token` and re-export |
