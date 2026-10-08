# Migration Kickoff Toolkit — Cursor Agent Skill

> *Migrating customers is complex. Starting the process doesn't have to be.*

Planning a migration means coordinating Asana requests, session decks, kickoff meetings, and team channels — before the real work even begins. This skill handles all of that in a single conversation.

Just tell Cursor what you're migrating. It asks the right questions, one at a time, then creates the Asana request, the session deck, the kickoff meeting invite, and a private Slack channel — all ready before you close the chat.

---

> **Note:** This toolkit covers the kickoff phase. The full migration process (engineering execution, customer communications, monitoring, etc.) continues beyond what this skill automates.

---

## What gets done for you

| | Output | Where |
|---|---|---|
| 📋 | Migration request logged | [Asana — Migrations Request form](https://app.asana.com/1/11915891072957/project/1215528144935482) |
| 📊 | Session deck, fully populated | Google Slides (Idira Migration Kickoff template) |
| 📅 | 30-minute kickoff meeting | Google Calendar + Google Meet |
| 💬 | Private Slack channel created | Slack — PM, Orit & Yael invited |

---

## How to start

**Say any of these in Cursor:**

> *"I want to plan a migration"*
> *"I have a product migration to kick off"*
> *"Start a migration kickoff for [name]"*

### What happens next

```
You mention migration
     ↓
AI asks: "What's the migration name?"
     ↓
AI searches Asana automatically
     ↓
   Found?                    Not found?
     ↓                           ↓
Use existing data          Ask you the questions
Ask only for gaps          (one at a time, conversationally)
     ↓                           ↓
                    Create Asana task (if new)
                           ↓
                    Create Google Slides deck
                           ↓
        Create 30-min Google Meet kickoff invite
        → Invites you, Orit, and Yael automatically
        → Deck + Asana links included in the invite
                           ↓
        Create private Slack channel
        → Invites you, Orit, and Yael (+ anyone else you name)
        → Intro message posted with deck + Asana links
                           ↓
              Share all links with you
```

---

## The deck (12 slides)

| Slide | Content |
|---|---|
| 1 | Cover — migration name + PM |
| 2 | Background — context, today's status, what's next |
| 3 | Announcement — what's being migrated |
| 4 | Business Rationale — why it's happening |
| 5 | Technical Details — how the migration works |
| 6 | Customer Analysis — who's affected + release strategy |
| 7 | Customer Impact — what changes for customers + downtime |
| 8 | Timeline — key milestone dates |
| 9 | Customer Facing Teams Guidance — field expectations + escalation |
| 10 | Alternatives — alternative solutions + pricing impact |
| 11 | Communication Plan — channels + who gets notified |
| 12 | Q&A |

---

## The Slack channel

- **Name:** `#migration-<normalized-name>` *(lowercase, hyphens)*
- **Type:** Private
- **Attendees:** You (the PM) + Orit Nevo Cohen + Yael Gershon + anyone extra you name
- **First message:** intro post with links to the deck and Asana task

---

## The calendar invite

- **Title:** Migration Kickoff - [migration name]
- **Duration:** 30 minutes
- **Format:** Google Meet
- **Attendees:** You (the PM) + Orit Nevo Cohen + Yael Gershon
- **Description:** includes a direct link to the deck and the Asana task
- **Timing:** next available Israel working-day slot (Sun–Thu, 9am–5pm)

---

## What the AI pulls from Asana automatically

If you (or a teammate) already submitted the migration request form, the AI finds and uses it.

| Pulled from Asana | Still asks you for |
|---|---|
| Migration name & description | Business rationale |
| Migration scale (customer count) | Technical implementation details |
| Whether customers have action items | Release strategy / segmentation |
| Downtime estimate | Key milestone dates |
| Customer segmentation | Field guidance |
| Development status | Alternatives & pricing |
| Customer-facing teams guidance | Communication plan |
| Prerequisites | Who gets notified |

---

## Questions you may be asked

One at a time — conversational, not a form dump.

| Topic | What's asked |
|---|---|
| **Announcement** | What exactly is being migrated |
| **Background** | Context: what existed before, why this migration is needed |
| **Rationale** | Why is this happening? *(rephrased to business language)* |
| **Technical details** | How the migration works |
| **Customer analysis** | Who's affected, release strategy / segmentation |
| **Customer impact** | What changes for customers, what they need to do |
| **Timeline** | Key dates — "When do you want to complete the migration?" |
| **Field guidance** | What the field teams should do |
| **Alternatives** | Options for customers who can't migrate |
| **Communication** | Channels, timing, who gets notified |
| **Additional Slack members** | Anyone beyond you, Orit & Yael to invite to the channel |

> **Auto-filled — never asked:**
> - Escalation contact → you (the submitting PM)
> - Who gets notified → always left as TBD

---

## Requirements

- Cursor with Google ADC configured (Drive + Slides + Calendar scopes)
- Access to the Idira Migration Kickoff Google Slides template
- Asana access (for reading/creating the Migrations request form task)
- Slack bot token with scopes: `groups:write`, `groups:read`, `users:read`, `users:read.email`, `chat:write`
  *(Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps) → From a manifest — see Installation step 4)*

---

## Installation & Setup

### 1 — Clone the repo

```bash
git clone https://github.com/onevocohen/migration-kickoff-toolkit.git
cd migration-kickoff-toolkit
```

> **Python 3** is the only runtime needed — all scripts use the standard library only (no `pip install`).

---

### 2 — Set up your Asana token

The scripts read your Asana token via a helper script at `~/.config/secrets/get-secret.sh`. Create the helper if it doesn't exist:

```bash
mkdir -p ~/.config/secrets

# Store your token
echo 'ASANA_ACCESS_TOKEN=your_token_here' >> ~/.config/secrets/tokens.env

# Create the get-secret helper
cat > ~/.config/secrets/get-secret.sh << 'EOF'
#!/bin/bash
# Usage: get-secret.sh KEY
grep "^$1=" "$HOME/.config/secrets/tokens.env" | cut -d= -f2-
EOF
chmod +x ~/.config/secrets/get-secret.sh
```

Get your Asana token at [app.asana.com/0/developer-console](https://app.asana.com/0/developer-console).

---

### 3 — Set up Google ADC (Drive + Slides + Calendar)

```bash
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/drive,\
https://www.googleapis.com/auth/presentations,\
https://www.googleapis.com/auth/calendar.events,\
https://www.googleapis.com/auth/cloud-platform"
```

> If you don't have the `gcloud` CLI, install it from [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install).

---

### 4 — Create a Slack bot and add the token

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From a manifest**
2. Select your workspace, then paste this manifest:

```json
{
  "display_information": { "name": "migration-kickoff-bot" },
  "features": {
    "bot_user": { "display_name": "migration-kickoff-bot", "always_online": false }
  },
  "oauth_config": {
    "scopes": {
      "bot": ["groups:write", "groups:read", "users:read", "users:read.email", "chat:write"]
    }
  },
  "settings": {
    "org_deploy_enabled": false,
    "socket_mode_enabled": false,
    "token_rotation_enabled": false
  }
}
```

3. Click **Next → Create → Install to Workspace → Allow**
4. Copy the **Bot User OAuth Token** (`xoxb-...`) from **OAuth & Permissions**
5. Add it to your secrets file:

```bash
echo 'SLACK_BOT_TOKEN=xoxb-your-token-here' >> ~/.config/secrets/tokens.env
```

---

### 5 — Update script paths in SKILL.md

The `SKILL.md` file references absolute paths to the scripts. After cloning, update them to match where you placed the repo:

Open `SKILL.md` and replace every occurrence of:
```
/Users/onevocohen/Library/Application Support/Cursor/AgentStores/...
```
with the absolute path to the `scripts/` folder inside your cloned repo. For example:
```
/Users/yourname/migration-kickoff-toolkit/scripts/fetch_asana.py
```

You can do this with a single find-and-replace in any editor.

---

### 6 — Open the folder in Cursor

```bash
cursor /path/to/migration-kickoff-toolkit
```

Cursor will automatically detect the `SKILL.md` at the root of the project and make the skill available in your agent sessions.

---

### 7 — Start using it

In any Cursor chat in this project, say one of these:

> *"I want to plan a migration"*
> *"Start a migration kickoff for [name]"*
> *"I'm working on a migration from X to Y"*

The agent will take it from there — asking questions, creating the Asana task, building the deck, scheduling the kickoff meeting, and opening the Slack channel.

---

## Files

```
migration-kickoff-toolkit/
├── README.md                  ← you are here
├── SKILL.md                   ← AI instructions (technical)
└── scripts/
    ├── fetch_asana.py         ← searches Asana by migration name
    ├── submit_asana.py        ← creates a new Asana task from PM answers
    ├── create_deck.py         ← copies the template + populates all slides
    ├── create_calendar.py     ← creates a 30-min Google Meet kickoff invite
    └── create_slack_channel.py ← creates a private Slack channel + invites members
```
