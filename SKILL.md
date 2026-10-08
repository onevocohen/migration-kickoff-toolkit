---
name: Migration Kickoff Toolkit
description: Kicks off the full Migration process for a product or feature — searches Asana for an existing migration request, asks the PM questions one at a time, creates an Asana task (if new), generates a fully populated Google Slides migration deck, and schedules a 30-minute Google Meet kickoff meeting. Use when a PM wants to plan a migration, deprecate and migrate customers, or create a migration session deck. Trigger phrases: "migration", "migrate customers", "migration deck", "migration kickoff", "customer migration", "start a migration".
disable-model-invocation: true
---

# Migration Kickoff Toolkit

Handles the full migration kickoff process from a single conversation.
The PM only needs to say they're planning a migration — the skill takes care of the Asana request, the session deck, and the kickoff meeting invite.

## Scripts

```
/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/fetch_asana.py
/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/submit_asana.py
/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/create_deck.py
/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/create_calendar.py
```

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
PM mentions migration → search Asana → found? use it : ask questions → save to Asana (if new) → create deck → create meeting → share all links
```

---

### Step 0 — Get the migration name, then search Asana

Ask the PM: **"What is the migration name or the product/feature being migrated?"**

Then immediately search Asana:

```bash
python3 "/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/fetch_asana.py" "<migration name>"
```

| Exit code | Meaning | Action |
|---|---|---|
| `0` | Existing task found — partial JSON ready | Pre-fill fields, go to Step 1 for gaps |
| `2` | No task found | Ask PM all missing questions, go to Step 1 |
| `3` | Multiple matches | Ask PM to clarify; re-run with chosen GID |

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

| Field | What to look for |
|---|---|
| `migration_name` | Exact name of the migration |
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
| `key_dates` | Key milestone dates — ask: "When do you want to complete the migration?" |
| `field_guidance` | What sales/CS/support should do, what's expected from the field |
| `escalation` | Auto-fill: always the submitting PM (`pm_name` + `contact`) — never ask |
| `alternatives` | What alternatives exist (if any) for customers who can't migrate |
| `pricing_impact` | Any pricing changes as part of migration |
| `communication` | Channels and timing for customer comms |
| `who_notified` | Which customer segments receive notice |
| `contact` | PM name + email |
| `pm_name` | Submitting PM's name |

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
  "status_notes": "..."
}
ENDJSON
```

---

### Step 3 — Save to Asana (only if no existing task found in Step 0)

```bash
python3 "/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/submit_asana.py" /tmp/migration_input.json
```

Prints the new Asana task URL. If Step 0 found an existing task, **skip this step**.

---

### Step 4 — Create the deck

```bash
python3 "/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/create_deck.py" /tmp/migration_input.json
```

Copies the Idira Migration Kickoff template, populates all slides, prints the Google Slides URL.

---

### Step 5 — Create the calendar invite

```bash
python3 "/Users/onevocohen/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/7e93e542-cc75-4818-830f-089df36e7650/files/skills/migration-kickoff-toolkit/scripts/create_calendar.py" /tmp/migration_input.json "<deck_url>" "<asana_url>"
```

Creates a **30-minute Google Meet** event titled `"Migration Kickoff - <migration name>"`, invites the PM + Orit Nevo Cohen (`onevocohen@paloaltonetworks.com`) + Yael Gershon (`ygershongob@paloaltonetworks.com`).

---

### Step 6 — Share all outputs

> ✅ Done! Here's your Migration Kickoff package:
>
> 📋 **Asana task**: [link] *(new — created from your answers)*
>    OR: 📋 **Asana task**: [link] *(existing submission used)*
>
> 📊 **Migration deck**: [link]
>
> 📅 **Kickoff meeting**: [calendar event link] · 🎥 [Google Meet link]
> *(30 min · Orit & Yael invited · deck + Asana links in the invite)*

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
| `403 on copy_template` | PM needs at least View access to the template |
| `ADC file not found` | Run: `gcloud auth application-default login` |
| `401 Unauthorized` | ADC token expired — re-run login |
