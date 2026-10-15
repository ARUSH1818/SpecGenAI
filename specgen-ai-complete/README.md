# SpecGen AI — Complete Build (Sprints 1-5)

All five sprints from the SRS (Section 8) are implemented: **Sprint 1**
(authentication), **Sprint 2** (AI engine, idea submission, first-draft
generation), **Sprint 3** (use cases, editable requirements, automated
requirement quality review), **Sprint 4** (risk editing, cost estimate, sprint
planning, admin routes), and **Sprint 5** (PDF/DOCX export, final polish).

This is the final increment — the product now covers the full idea-to-exported-
document flow described in the SRS.

Not a mockup — this is a real FastAPI backend + React frontend with a working
database, real password hashing and JWTs, and a real call to an LLM.

## What's implemented

| SRS Requirement | Where |
|---|---|
| REQ-AUTH-01–04 (register, login, session) | `backend/app/routers/auth.py` |
| REQ-SEC-01 (bcrypt password hashing) | `backend/app/auth.py` |
| REQ-SUBMIT-01/02 (idea submission + classification) | `backend/app/routers/projects.py` |
| REQ-AIGEN-01 (draft SRS/requirement generation) | `backend/app/ai_engine.py` |
| REQ-STORY-01, REQ-RISK-01, REQ-TEST-01 | same generation call, `ai_engine.py` |
| REQ-SEC-03 (projects scoped to owner) | `get_project` / `list_projects` in `projects.py` |
| Business rule: Draft → Reviewed status | `PATCH /projects/{id}/review` |
| REQ-STORY-03 (use cases) | generated alongside stories, `ai_engine.py` |
| REQ-AIGEN-03 (edit/add/delete requirements) | `PATCH`/`POST`/`DELETE /projects/{id}/requirements[/...]` |
| REQ-REVIEW-01/02 (ambiguity/duplicate detection) | `backend/app/review.py` — deterministic, rule-based |
| REQ-REVIEW-03 (priority override) | same requirement PATCH endpoint |
| REQ-REVIEW-04 (missing-area suggestions) | `review.find_missing_areas` |
| REQ-REVIEW-05 (rewording suggestions) | rule-based fallback always available; `ai_engine.suggest_rewordings` improves wording when a key is set |
| REQ-REVIEW-06 (quality score) | `review.quality_score`, shown on the project page |

**Design note on Sprint 3:** the quality review's ambiguity/duplicate detection is
deliberately rule-based, not an LLM call — it's deterministic, testable without a
key, and matches how the SRS describes it (flagging vague terms, near-duplicate
text). The LLM is used only as an *optional* second pass to improve suggestion
wording (REQ-REVIEW-05); if it's unavailable, review still fully works with
generic rule-based suggestions.

| REQ-RISK-02 (itemized cost estimate) | generated in `ai_engine.py`, edited via `PATCH /projects/{id}/cost-estimate/{cost_pk}` |
| REQ-SPRINT-01/02 (sprint plan generation) | `backend/app/planning.py` — deterministic, not an LLM call |
| REQ-SPRINT-03 (move a story between sprints) | `PATCH /projects/{id}/stories/{story_pk}/sprint` |
| Risk editing (consistency with "artifacts remain editable") | `PATCH`/`DELETE /projects/{id}/risks/...` |
| REQ-ADMIN-01 (list users) | `GET /admin/users` |
| REQ-ADMIN-02 (monitor usage) | `GET /admin/usage` |
| REQ-ADMIN-03 (disable an account) | `PATCH /admin/users/{id}/disable` — existing tokens stop working immediately, not just at next login |
| REQ-ADMIN-04 (log every generation request) | `GenerationLog` model, written in `projects.py` around every AI call |
| REQ-EXPORT-01 (PDF export) | `backend/app/export.py::build_pdf`, via `GET /projects/{id}/export?format=pdf` |
| REQ-EXPORT-02 (DOCX export) | `backend/app/export.py::build_docx`, via `GET /projects/{id}/export?format=docx` |
| REQ-EXPORT-03 (structure + req IDs preserved) | both builders walk the same 9-section order from one shared data-extraction function |

**Design note on Sprint 5:** both export formats are built from one shared
`_sections()` function in `export.py` that reads the live project state once.
That's deliberate: writing the PDF and DOCX builders independently (each poking
at the database separately) would risk them drifting out of sync — add a field
to one and forget the other. Reading from a single source of truth makes
REQ-EXPORT-03 ("structure preserved") true by construction, not by discipline.

**Design note on Sprint 4:** sprint planning, like requirement review in Sprint 3,
is deliberately **deterministic, not an LLM call** (`planning.py`). Which sprint a
story lands in should be reproducible and explainable ("it's High priority, so
it's early"), not something that changes if you regenerate. The algorithm sorts
stories by priority, then cuts the list into contiguous, size-balanced chunks —
one chunk per sprint. An earlier round-robin version was replaced after the test
suite caught that round-robin actually contradicts REQ-SPRINT-02 (it spreads every
priority level across every sprint evenly, so a High-priority story could land in
the last sprint purely by chance) — see the Testing section below.

There's no public "register as admin" — that would be a real security hole. The
first admin account is created with `backend/scripts/make_admin.py <email>`.

## Export

`GET /projects/{id}/export?format=pdf` or `format=docx` returns the file
directly with a `Content-Disposition: attachment` header, so a browser (or
`curl -O`) downloads it immediately — no separate "prepare export" step. Both
formats cover the same nine sections, in the same order: Idea, Classification,
Functional Requirements, User Stories, Use Cases, Risks, Cost Estimate, Sprint
Plan, Test Cases. Export always reflects current state — if you've edited a
requirement or regenerated the sprint plan, re-exporting picks up the change
immediately, there's no stale cached copy.

## Nothing left unbuilt from the SRS sprint plan

All five sprints are done. Possible future work beyond the SRS's scope — not
promised anywhere in the document, just natural next steps: email delivery of
the exported file, a shareable read-only project link, rate limiting on the
generation endpoint, and the i18n/localization groundwork the SRS explicitly
deferred past Version 1.0.

## Running it locally

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# edit .env: set SECRET_KEY and ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```
API docs at `http://localhost:8000/docs` (FastAPI's built-in Swagger UI).

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App at `http://localhost:5173`.

### Getting an API key
The AI Processing Engine (`backend/app/ai_engine.py`) calls the Anthropic API as
the concrete "LLM Provider API" from the SRS architecture diagram. Get a key at
console.anthropic.com and put it in `backend/.env`. Without a key, everything
else works (register, login, project list) — only the generate step returns a
clear error instead of crashing (REQ-SUBMIT-04).

**Cost:** the API is pay-as-you-go (prepaid credits, no permanent free tier) —
check console.anthropic.com for any current signup credit. The default model is
Claude Haiku, the cheapest current option, which handles this structured-JSON
generation task well: roughly $0.004 per generation, so building and demoing
this project end-to-end costs well under $1 total. Override with the
`ANTHROPIC_MODEL` env var if you want to try a stronger model later.

## Testing

### Backend: 61 automated tests (`cd backend && pytest`)
Only the LLM call is mocked — routes, auth, ownership, the database, and the full
review/planning engines all run for real against a throwaway SQLite file. No API
key needed.

- `tests/test_review.py` (17 tests) — the review engine in isolation.
- `tests/test_planning.py` (10 tests) — the sprint-assignment algorithm: priority
  ordering, balanced chunk sizes, remainder handling, edge cases (1 sprint, more
  sprints than stories, 0 sprints rejected).
- `tests/test_api.py` (11 tests) — Sprint 2/3 request/response flow.
- `tests/test_sprint4.py` (23 tests) — cost estimate persistence, risk
  edit/delete with ownership checks, sprint plan generation/regeneration/moving
  stories, and the full admin surface: access control (401/403), listing users
  with correct project counts, disable/enable, **a disabled user's existing
  token stops working immediately** (not just "can't log in again" — verified
  as two separate assertions), and usage stats counting both successes and
  failures.
- `tests/test_export.py` (12 tests) — reads exported files back with real
  parsers (`pypdf`, `python-docx`), not just status-code checks: requirement
  IDs present in extracted text, the risk table has the right columns, section
  headings appear in the correct order, a project with no generated content at
  all still exports without crashing, and **export reflects an edit made right
  before downloading** — not a stale copy from generation time.

**Mutation-tested, not just passing by default:** across all three sessions, I
deliberately broke the ownership check, the duplicate threshold, the
flag-clearing-on-edit logic, the admin self-disable guard, the `is_active`
check at token-auth time, sprint-plan regeneration's delete-before-recreate
step, the sprint-assignment algorithm, requirement IDs in the PDF, the risk
table's mitigation column, export reading stale data, and section ordering —
eleven independent mutations across the whole project, confirmed the suite
fails every one. A suite that can't fail proves nothing.

**Three real bugs caught by testing, not just typos:**
1. The coverage checklist used `"log "` as a keyword for "Administration /
   monitoring", matching inside "log **in**" — any project with a login
   requirement was silently marked as already covering admin/monitoring with
   zero actual admin features. Same issue with `"message"` matching generic
   error messages as "notifications." Fixed in `review.py`.
2. The failure path in `create_project` logged the failed attempt but called
   `db.commit()` without rolling back first — which would have resurrected the
   half-created project the log was supposed to record as failed. Caught by
   the existing `test_generation_failure_returns_502_and_persists_nothing` test
   immediately after the Sprint 4 schema changes.
3. The original sprint-planning algorithm used round-robin assignment, which
   passed its own "spreads work evenly" test but **failed** a more direct test
   of REQ-SPRINT-02 ("High-priority items in earlier sprints") — round-robin
   deals every priority level into every sprint, so a High-priority story could
   land in the last sprint purely by position. Replaced with contiguous
   priority-sorted chunking, which satisfies both properties at once.

### End-to-end: real browser, real backend, real frontend build
Three headless-Chromium sessions:
- **Sprint 2/3 flow** (19 checks): register, generate, run review, verify exact
  flags/missing-areas shown, edit a flagged requirement and confirm the flag
  clears and score resets, override a priority, add/delete a requirement,
  reload and confirm edits persisted, log out, confirm a second user cannot
  open the first user's project.
- **Sprint 4 flow** (9 + 3 checks): generate a project with cost estimate
  visible, edit a risk's likelihood, edit a cost item's effort level, generate
  a 3-sprint plan and confirm all stories are placed, move a story between
  sprints, confirm a non-admin is redirected away from `/admin`; separately,
  promote a user via `make_admin.py`, confirm the Admin nav link appears,
  confirm the admin page shows correct usage stats and both users, and disable
  a user from the UI.
- **Sprint 5 flow** (7 checks): click the real "Download PDF" button, catch the
  actual browser download event, save the file to disk, and parse it with
  `pypdf` to confirm it's a genuine PDF containing the right requirement IDs
  (not just a 200 response) — then the same for "Download Word" with
  `python-docx`. Then edit a requirement, re-download, and confirm the new
  text appears in the freshly exported file.

All 38 browser checks passed, zero real console errors, zero unexpected HTTP
failures. The exported PDF was also rendered to an image and visually
inspected — proper headings, tables, bolded requirement IDs, not just
machine-parseable text.

### What's still unverified
No live LLM API key was available in this build environment, so the actual
network round-trip to Anthropic (`ai_engine.generate_draft`, `suggest_rewordings`)
is mocked everywhere above. The request/response contract, error handling
(REQ-SUBMIT-04), and JSON-parsing fallback are all covered — the one thing to
check yourself once you add a real key is that the live model reliably returns
JSON matching the expected shape.

## Tech stack (matches SRS Section 2.4)

- Backend: FastAPI, SQLAlchemy, SQLite (swap `DATABASE_URL` for PostgreSQL in production)
- Auth: JWT (python-jose) + bcrypt
- AI: Anthropic API (`anthropic` SDK)
- Frontend: React + Vite, React Router
