# SDD Implementation Start

This package was generated from the 6-reviewer combined report for the current uncommitted `p2me` changes.

## Package Structure

```text
sdd_package_20260310_160836/
├── START.md
├── kanban.json
├── 00_backlog/
├── 01_in_progress/
├── 02_in_review/
├── 03_done/
└── reports/
```

## Quick Start

```bash
cat kanban.json | jq '.columns'
```

1. Pick the highest-priority card from `00_backlog/`.
2. Move it to `01_in_progress/` and update `kanban.json`.
3. Create a task branch.
4. Implement the change.
5. Self-review and move the card to `02_in_review/`.
6. After verification, move it to `03_done/`, update `kanban.json`, and commit atomically.
7. Repeat until backlog is empty.

## Current State

```json
{
  "backlog": 0,
  "in_progress": 0,
  "in_review": 0,
  "done": 4,
  "total_points": 12,
  "completed_points": 12
}
```

## Kanban Rules

### Priority Order

- Always take `P0` before `P1`, and `P1` before `P2`.
- Within the same priority, prefer the smallest story-point card first.

### WIP Limit

- `01_in_progress/` has a hard WIP limit of 2 cards.

### Mandatory Status Updates

Every card move must be reflected in `kanban.json`.

### Atomic Commits

- `P0` cards use `fix:`
- `P1` cards use `refactor:`
- `P2` cards use `chore:`
- simplification-only work uses `simplify:`

### Completion Criteria

- All cards are in `03_done/`
- `kanban.json.meta.status` is `completed`
- Total points are complete

### Stop Conditions

- User says `STOP`
- A new critical blocker is discovered
- All cards are done
