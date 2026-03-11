---
name: deadline-tracker
description: Track contract deadlines for active real estate transactions using beads. Use when users mention going under contract, contract deadlines, option periods, closing dates, or ask what's coming up. Trigger phrases include "under contract", "went UC", "track deadlines", "contract deadlines", "option ends", "closing date", "deadline check", "what's coming up", "show transactions".
---

# Contract Deadline Tracker

Track critical contract deadlines for active real estate transactions. Uses `br` (beads) for persistence — each transaction is a parent bead, each deadline is a child bead with a due date.

## Data Model

**Transaction** = parent bead (epic)
- Title: `TX: {address}`
- Type: epic, Priority: P0
- Labels: `transaction` + `listing-side` or `buyer-side`
- Description: effective date, closing date, notes

**Deadline** = child bead (task) under the transaction
- Title: `{deadline name} — {short address}`
- Type: task, Priority: P0 for time-sensitive (option, earnest money, closing), P1 for others
- Labels: `deadline` + one of: `earnest-money`, `option-period`, `inspection`, `title-commitment`, `survey`, `financing`, `appraisal`, `closing-disclosure`, `walkthrough`, `closing`
- Due: the actual deadline date
- Parent: the transaction bead ID

## Texas TREC Default Deadlines (from effective date)

| Deadline | Default | TREC Para |
|----------|---------|-----------|
| Earnest money deposit | +3 days | §5 |
| Option period ends | negotiated (5-10 days typical) | §23 |
| Title commitment | +20 days | §6.A |
| Survey | per contract | §6.C |
| Financing approval | negotiated (21-30 days) | §4 |
| Appraisal | +10-14 days (lender) | — |
| Closing Disclosure | closing - 3 business days | Federal |
| Final walkthrough | closing - 1 day | §7.E |
| Closing | negotiated | §9 |

When the user provides an effective date and closing date, calculate all deadlines using these defaults. Let the user override any specific date. Confirm all dates before creating beads.

## br Commands Reference

```bash
# Create transaction
br create "TX: 123 Main St, Frisco TX" -t epic -p 0 -l transaction,listing-side \
  -d "Effective: 2026-03-10 | Closing: 2026-04-15"

# Create deadline under transaction
br create "Option Period Ends — 123 Main" -t task -p 0 \
  -l deadline,option-period --parent {tx_bead_id} --due 2026-03-17

# List all active deadlines
br list -l deadline -s open --sort due_at

# List overdue deadlines
br list -l deadline --overdue

# List all transactions
br list -l transaction -s open

# Show transaction tree (parent + children)
br show {tx_bead_id}

# Mark deadline complete
br close {deadline_id} --reason "Complete"

# Change a due date
br update {deadline_id} --due 2026-04-20

# Close entire transaction (close parent + all children)
# Close children first, then parent
```

## Commands the User Can Say

- "under contract {address}, {details}" → parse, calculate deadlines, create beads, confirm
- "deadline check" / "what's coming up?" → `br list -l deadline -s open --sort due_at`
- "mark {deadline} complete for {address}" → `br close` the matching deadline bead
- "push closing to {date} for {address}" → `br update --due` on the relevant beads
- "closed {address}" / "fell through" → close all beads for that transaction
- "show transactions" → `br list -l transaction -s open`
