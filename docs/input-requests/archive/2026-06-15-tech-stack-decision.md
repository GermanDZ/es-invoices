---
title: "Tech stack decision for FacturaSimple (AD-5)"
created: "2026-06-15T10:00:00Z"
created_by: "openup-next (T-006, architect hat)"
status: processed
run_id: "T-006-it5"
related_task: "T-006"
answered_at: "2026-06-15T12:10:00Z"
---

# Input Request — Tech Stack Decision (AD-5)

## Context

**Iteration 5 (Elaboration), task T-006** — authoring the architecture notebook
(`docs/architecture-notebook.md`). Everything that the stated constraints force
is decided and recorded: modular monolith (AD-1), isolated versioned compliance
module (AD-2), swappable AEAT submission interface (AD-3, adapter pending the
T-007 spike), **EU data residency on a European cloud provider (AD-4, accepted)**,
and a relational datastore / PostgreSQL recommendation (AD-6).

The one load-bearing decision left open is **AD-5: the application tech stack**.
During T-006 you chose to **defer it to founder expertise** — a solo build
succeeds or fails on what the one builder knows best, which only you can supply.
The notebook stays `status: draft` until this is answered; T-006 is paused on it.

**Selection criteria the architecture imposes** (apply to whatever you pick):
mature **XML + XAdES / XML-DSig signing** support (Verifactu records must be
signed), reliable **PDF generation**, **EU-hostable** (AD-4), and — decisive —
**your own fluency**.

## Questions

### Q1: Primary language + web framework
**Type**: text
**Example**: "TypeScript + Next.js/Node", "Python + Django", "PHP + Laravel", "C# + ASP.NET Core", "Ruby on Rails"

What language and web framework do you want to build FacturaSimple in? Pick what
you are most productive in that can meet the criteria above.

**Answer**: **Python + Django.** Mature XML signing (`signxml` for XAdES/XML-DSig),
reliable PDF generation (WeasyPrint / ReportLab), EU-hostable on any provider
(AD-4), and founder fluency. Meets all imposed criteria.

### Q2: Datastore confirmation
**Type**: multiple-choice
**Accepts**: one option

- [x] `PostgreSQL` - Confirm the AD-6 recommendation (relational, ACID, EU-hostable).
- [ ] `MySQL/MariaDB` - Relational alternative (e.g. if your stack defaults to it).
- [ ] `Other / let the stack default decide` - Specify in the answer.

**Answer**: **PostgreSQL** — confirms the AD-6 recommendation. Pairs cleanly with
Django (first-class `django.db.backends.postgresql` support).

### Q3: Anything that further constrains the stack?
**Type**: text
**Example**: "Must reuse an existing Facturae PHP library", "team also knows Go", "prefer managed DB only"

Optional — any existing code, library, hosting account, or skill that should
steer or veto a choice.

**Answer**: None supplied — no additional constraint.

## Instructions for Respondent

1. Fill in the **Answer** section under each question.
2. Change `status: pending` → `status: answered` in the frontmatter.
3. Save the file.
4. Re-run `/openup-next` — it will resume T-006, fold your answers into AD-5/AD-6,
   flip the architecture notebook to `approved`, and complete the task.
