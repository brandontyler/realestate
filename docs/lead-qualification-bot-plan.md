# AI Lead Qualification & Routing Bot — Research & Plan

**Bead:** bd-3ja
**Status:** Research complete
**Last updated:** 2026-03-05

---

## 1. The Problem (From Your Broker Friend's Mouth)

Your broker friend gets leads forwarded from his agents all the time. He rarely picks one up because he's looking for specific things that make it a "good deal." The problem breaks into two parts:

1. **Volume overwhelm** — Too many leads, not enough signal. He can't manually read every one.
2. **No filter** — Leads arrive as raw text (email, SMS, forwarded messages) with no qualification or scoring. He has to mentally evaluate each one against his criteria.

This isn't a "respond faster" problem — it's a **"find the needle in the haystack"** problem. The AI doesn't just respond to leads; it qualifies, scores, and routes them so the broker only sees the ones worth his time.

---

## 2. How Leads Actually Flow in a Brokerage

Based on research, here's the real-world lead flow for a North Texas broker:

### Lead Sources
| Source | Format | How It Arrives |
|--------|--------|---------------|
| Zillow Premier Agent | Email notification + Zillow dashboard | Email to agent, sometimes forwarded to broker |
| Realtor.com | Email notification | Same pattern |
| Agent's website (IDX) | Form submission → email | Forwarded or in CRM |
| Facebook/Instagram ads | Lead form → email/CRM | Varies |
| Sign calls/texts | SMS/voicemail | Agent forwards to broker via text |
| Referrals | Email, text, phone call | Informal — "hey I got a lead" |
| Open house sign-ins | Paper or digital form | Agent texts/emails broker |
| Cold inbound (walk-ins, calls) | Phone/in-person | Agent relays verbally or via text |

**Key insight:** Most leads reach the broker as **forwarded text messages or emails** — unstructured, informal, no standard format. The AI needs to handle messy, real-world input.

### Current Flow (Broken)
```
Lead comes in → Agent gets notification → Agent forwards to broker
→ Broker reads it (maybe) → Broker decides (gut feel) → Most get ignored
→ Lead goes cold → Money left on table
```

### Target Flow (With AI)
```
Lead comes in → AI ingests it (any format) → AI extracts key info
→ AI scores against broker's criteria → AI classifies (Hot/Warm/Cold)
→ Hot leads: instant alert to broker with summary + score
→ Warm leads: AI engages lead, qualifies further, then alerts
→ Cold leads: AI sends polite response, parks in nurture queue
```

---

## 3. Lead Qualification Framework

### 3.1 The BANT Framework (Adapted for Real Estate)

| Factor | What We're Assessing | Key Questions |
|--------|---------------------|---------------|
| **Budget** | Can they actually afford it? | Pre-approved? Price range? Cash buyer? |
| **Authority** | Are they the decision-maker? | Buying alone or with spouse? Who decides? |
| **Need** | How real is the need? | Why moving? Lease ending? Job relocation? Growing family? |
| **Timeline** | How urgent? | When do they need to move? Already looking? Under contract to sell? |

### 3.2 Broker-Specific "Buy Box" Criteria

This is the key differentiator. Your broker friend isn't looking at every lead — he has a mental checklist. Common broker buy-box criteria:

**For buyer leads:**
- Price range alignment (does the buyer's budget match available inventory?)
- Pre-approval status (no pre-approval = tire kicker)
- Timeline (looking to buy in 30-90 days = hot; "someday" = cold)
- Area specificity (knows what neighborhoods they want vs. "somewhere in DFW")
- Motivation level (relocating for work = high; browsing Zillow on the couch = low)

**For seller leads:**
- Property location (in broker's farm area?)
- Estimated equity (underwater = hard deal; lots of equity = easy listing)
- Motivation (divorce, job transfer, estate = motivated; "just curious what it's worth" = cold)
- Timeline (needs to sell in 60 days = hot)
- Condition (move-in ready vs. needs $50K in work)
- Price expectations (realistic vs. delusional)

**For investor leads (if broker does investment deals):**
- Deal type (flip, rental, wholesale)
- Numbers: Does it meet the 70% rule? (Purchase ≤ 70% ARV - repairs)
- Cash or financing?
- Track record (experienced investor vs. first-timer who watched a YouTube video)
- Speed to close

### 3.3 Lead Scoring Model

Score 0-100, classified into tiers:

| Score | Tier | Action |
|-------|------|--------|
| 80-100 | 🔥 Hot | Immediate broker alert. AI sends "someone will call you in 5 minutes" |
| 50-79 | 🟡 Warm | AI engages in qualification conversation, then re-scores |
| 20-49 | 🟠 Cool | AI responds politely, adds to nurture drip |
| 0-19 | ❄️ Cold | AI sends generic response, files away |

**Scoring criteria (configurable by broker):**

| Factor | Points | Details |
|--------|--------|---------|
| Pre-approved / cash buyer | +25 | Strongest signal of readiness |
| Timeline ≤ 30 days | +20 | Urgency |
| Timeline 30-90 days | +10 | |
| Specific area/neighborhood | +10 | Knows what they want |
| Motivated reason (relocation, divorce, estate) | +15 | High-motivation triggers |
| In broker's farm area | +10 | Geographic match |
| Realistic price expectations | +5 | |
| Repeat inquiry / multiple properties viewed | +5 | Engagement signal |
| "Just looking" / no timeline | -10 | Low intent |
| No budget info / won't share | -10 | |
| Out of service area | -15 | |

---

## 4. Conversation Design

### 4.1 Initial Response (Speed-to-Lead)

When a lead comes in, AI responds within 60 seconds. The goal: acknowledge, build rapport, start qualifying.

**For a buyer inquiry on a specific property:**
```
Hi [Name]! Thanks for your interest in [Property Address]. 
I'm helping [Broker Name]'s team today. 

Quick question — are you currently working with a lender, 
or would you like a recommendation for pre-approval? 

Also, what's your timeline for finding a home?
```

**For a general inquiry:**
```
Hi [Name]! Thanks for reaching out to [Brokerage]. 

To make sure we connect you with the right person, 
can I ask a couple quick questions?

What area of North Texas are you looking in, 
and do you have a price range in mind?
```

### 4.2 Qualification Flow (Conversational, Not Interrogation)

The AI asks 3-5 questions max, spread naturally across the conversation. It doesn't dump all questions at once.

**Question sequence (adaptive):**
1. **Area/Property** — "What area are you looking in?" or "Tell me about the property" (if seller)
2. **Timeline** — "What's your timeline?" / "When are you looking to make a move?"
3. **Financial readiness** — "Are you pre-approved?" / "Are you working with a lender?"
4. **Motivation** — "What's prompting the move?" (only if conversation flows naturally)
5. **Decision-makers** — "Will anyone else be involved in the decision?"

After each answer, AI updates the lead score in real-time.

### 4.3 Handoff Triggers

AI immediately escalates to the broker when:
- Lead says they're pre-approved and looking within 30 days
- Lead mentions cash purchase
- Lead is in broker's target area with realistic budget
- Lead mentions urgency trigger (relocation, lease ending, estate sale)
- Lead asks to schedule a showing or listing appointment

### 4.4 Nurture Mode (For Warm/Cool Leads)

If lead doesn't qualify as hot:
- AI thanks them, provides helpful info (market stats, area guides)
- Schedules follow-up check-in (7 days, 30 days, 90 days)
- If lead re-engages later, re-scores and potentially escalates

---

## 5. Architecture

### 5.1 System Components

```
┌─────────────────────────────────────────────┐
│                LEAD INTAKE                   │
│  Email parser │ SMS handler │ Web form API   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│            LEAD PROCESSOR                    │
│  Extract: name, phone, email, property,      │
│  source, raw message text                    │
│  Normalize into structured lead object       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│            AI QUALIFICATION ENGINE           │
│  Score lead against broker's buy box         │
│  Classify: Hot / Warm / Cool / Cold          │
│  If property mentioned → enrich via Trestle  │
└──────────┬───────────────┬──────────────────┘
           │               │
     Hot (80+)        Warm (50-79)
           │               │
           ▼               ▼
┌──────────────┐  ┌────────────────────┐
│ BROKER ALERT │  │ AI CONVERSATION    │
│ SMS + summary│  │ Qualify further    │
│ + score card │  │ Re-score → maybe   │
│              │  │ escalate to Hot    │
└──────────────┘  └────────────────────┘
```

### 5.2 Lead Intake Options (Simplest First)

**Option A: Email forwarding (easiest to start)**
- Broker/agents forward leads to a dedicated email address (e.g., leads@[domain])
- AI parses the email: extracts name, phone, property, message
- Works with ANY lead source — no integrations needed
- Broker can literally just forward a text screenshot or email

**Option B: SMS-based (via Twilio or similar)**
- Dedicated phone number for the brokerage
- Leads text in, AI responds via SMS
- Agents can forward leads by texting them to the AI number
- Two-way conversation happens over SMS

**Option C: Webhook integrations (later)**
- Zillow Tech Connect delivers leads via HTTP POST webhook
- Realtor.com has similar lead delivery
- CRM integrations (Follow Up Boss, KVCore, etc.)

**Recommendation: Start with Option A (email forwarding).** Zero friction for the broker — he already forwards leads. Just change who he forwards them to.

### 5.3 Trestle Integration (Property Enrichment)

When a lead mentions a specific property, the AI can:
1. Look up the property in Trestle by address
2. Pull listing details (price, beds/baths/sqft, DOM, photos)
3. Pull recent comps in the area (reuse CMA logic from bd-2mb.1)
4. Include property context in the broker alert:
   - "Lead asking about 4521 Elm Creek Dr — listed at $425K, 4/3/2100sqft, 12 DOM, priced 3% below area avg"

This is where the CMA tool and the lead bot converge — the lead bot can auto-generate a mini-CMA for any property a lead asks about.

### 5.4 Broker Alert Format

When a hot lead is identified, broker gets an SMS/message like:

```
🔥 HOT LEAD (Score: 87/100)

Name: John Smith
Phone: (214) 555-1234
Source: Zillow (forwarded by Agent Sarah)

Looking for: 4+ bed in Frisco/Prosper
Budget: $450-550K
Pre-approved: Yes (First National)
Timeline: 60 days (relocating from Austin)
Motivation: Job transfer to Toyota HQ

Property interest: 4521 Elm Creek Dr, Prosper
  Listed $489K | 4/3 | 2,100 sqft | 8 DOM

Why hot: Pre-approved, 60-day timeline, 
in your farm area, motivated relocation

→ Reply "call" to get their number
→ Reply "pass" to send to agent pool
```

---

## 6. Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Lead intake (email) | Email parsing (IMAP or forwarding webhook) | Broker already forwards emails |
| Lead intake (SMS) | Twilio | Industry standard, cheap, two-way SMS |
| AI engine | LLM (agent) | Natural conversation + scoring |
| Property enrichment | Trestle API (same as CMA) | Already building this |
| Lead storage | SQLite or simple JSON | Start simple |
| Broker alerts | SMS via Twilio or Discord bot | Meet broker where he is |
| Nurture/follow-up | Scheduled messages | Cron or queue-based |

---

## 7. Build Phases

### Phase 1: Lead Intake & Parsing
- Email forwarding setup (dedicated inbox)
- AI-powered email/message parser (extract name, phone, email, property, intent from unstructured text)
- Structured lead object creation

### Phase 2: Scoring Engine
- Configurable broker buy-box criteria
- Lead scoring algorithm (0-100)
- Tier classification (Hot/Warm/Cool/Cold)
- Property enrichment via Trestle (if property mentioned)

### Phase 3: Broker Alerts
- Hot lead alert delivery (SMS or Discord)
- Lead summary card generation
- Reply-to-act (broker can respond to take action)

### Phase 4: AI Conversation (Qualification)
- Two-way SMS conversation for warm leads
- Adaptive question flow (3-5 questions)
- Real-time re-scoring during conversation
- Escalation to broker when lead qualifies

### Phase 5: Nurture & Follow-up
- Scheduled follow-up messages for cool/warm leads
- Re-engagement detection
- Lead lifecycle tracking

---

## 8. Key Insight: This Is Really Two Products

1. **Lead Filter** (for the broker) — "Show me only the leads worth my time." This is the immediate pain point. Doesn't even require two-way conversation — just parse, score, and alert.

2. **Lead Qualifier** (for the brokerage) — "Engage every lead instantly, qualify them, and route to the right person." This is the full vision with AI conversations.

**Start with #1.** It's simpler, solves the broker's stated problem, and proves value fast. Then layer on #2.

---

## 9. Revenue/Value Proposition

- Average real estate commission in North Texas: ~2.5-3% of sale price
- Median home price in North Texas: ~$380K
- One commission: ~$9,500-$11,400
- If the AI helps the broker catch even ONE extra deal per month that he would have ignored, that's $9-11K/month in recovered revenue
- Speed-to-lead stats: responding within 5 minutes = 100x more likely to convert than 30 minutes
- Industry data: AI lead qualification tools show 53% jump in qualified leads and 15-25% improvement in conversion

---

## 10. Open Questions

1. How does your broker friend currently receive leads? (Email? Text? CRM? All of the above?)
2. What are HIS specific criteria for a "good deal"? (We need to configure his buy box)
3. Does he primarily work with buyers, sellers, or investors? (Changes scoring weights)
4. Does he use any CRM currently? (Follow Up Boss, KVCore, Chime, etc.)
5. Would he prefer alerts via text, email, or something else?
6. Is your son (the agent) also interested in this, or is this primarily for the broker?
