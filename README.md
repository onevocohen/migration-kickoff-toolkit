# Migration Kickoff Toolkit — Cursor Agent Skill

> *Migrating customers is complex. Starting the process doesn't have to be.*

Planning a migration means coordinating Asana requests, session decks, and kickoff meetings — before the real work even begins. This skill handles all of that in a single conversation.

Just tell Cursor what you're migrating. It asks the right questions, one at a time, then creates the Asana request, the session deck, and the kickoff meeting invite — all ready before you close the chat.

---

> **Note:** This toolkit covers the kickoff phase. The full migration process (engineering execution, customer communications, monitoring, etc.) continues beyond what this skill automates.

---

## What gets done for you

| | Output | Where |
|---|---|---|
| 📋 | Migration request logged | [Asana — Migrations Request form](https://app.asana.com/1/11915891072957/project/1215528144935482) |
| 📊 | Session deck, fully populated | Google Slides (Idira Migration Kickoff template) |
| 📅 | 30-minute kickoff meeting | Google Calendar + Google Meet |

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

> **Auto-filled — never asked:**
> - Escalation contact → you (the submitting PM)

---

## Requirements

- Cursor with Google ADC configured (Drive + Slides + Calendar scopes)
- Access to the Idira Migration Kickoff Google Slides template
- Asana access (for reading/creating the Migrations request form task)

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
    └── create_calendar.py     ← creates a 30-min Google Meet kickoff invite
```
