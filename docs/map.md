# Chapter map

Where each chapter's code lives. Chapters that build the running
service point at `roombook/`; the others have their own directory
because their code differs from the finished service.

## Part I — The Problem

1. **The Framework Ate the Business** — `ch01/`, the
   framework-shaped app (rules in routes and ORM models).
2. **Five Architectures, One Question** — no listing of its own;
   the five shapes it sketches are built in `architectures/`.
3. **Python Without a Compiler to Stop You** — `ch03/`: Protocol
   and ABC ports, the `runtime_checkable` trap, mypy catching a
   structural error.

## Part II — Thinking in Hexagons

4. **The Domain Owns Nothing** — `roombook/src/roombook/domain/`.
5. **Ports Are Protocols the Core Writes** — `ch05/` (a
   provider-shaped port and its rewrite), then
   `roombook/src/roombook/application/`.
6. **Adapters on Both Sides** —
   `roombook/src/roombook/adapters/inbound/http/` and
   `roombook/src/roombook/adapters/outbound/memory/`.
7. **The Dependency Rule, Enforced** — `ch07/violation/` and
   `ch07/fixed/`; the contracts in `roombook/pyproject.toml`; CI
   in `.github/workflows/ci.yml`.

## Part III — Building the Booking Service

8. **A Layout That Tells the Truth** — `roombook/` (tree,
   `pyproject.toml`).
9. **Modelling Bookings** — `roombook/src/roombook/domain/`.
10. **Use Cases and Application Services** —
    `roombook/src/roombook/application/`.
11. **Driving Adapters: HTTP, CLI and a Consumer** —
    `roombook/src/roombook/adapters/inbound/` (`http/`, `cli/`,
    `messaging/`, `jobs/`).
12. **Driven Adapters: SQLAlchemy 2 Without Letting It In** —
    `roombook/src/roombook/adapters/outbound/sqlalchemy/`,
    `.../outbound/payments/`, `roombook/migrations/`.
13. **Wiring: the Composition Root** —
    `roombook/src/roombook/composition.py`.

## Part IV — The Other Architectures, Built

14. **Clean Architecture in Python** — `architectures/clean/`,
    compared with `architectures/hexagonal/`.
15. **Onion Architecture in Python** — `architectures/onion/`.
16. **Layered and Vertical Slices** — `architectures/layered/`
    and `architectures/vertical_slice/`.
17. **Choosing Between Them** — `architectures/measure.py`,
    `architectures/add-max-length-rule.md`, the max-length rule
    commits, and `docs/outputs/architectures/`.

## Part V — Production Patterns

18. **Testing the Hexagon** — `roombook/tests/` (`unit/`,
    `contract/`, `integration/`, `e2e/`).
19. **Transactions and the Unit of Work** —
    `roombook/src/roombook/adapters/outbound/sqlalchemy/`.
20. **Errors That Cross Boundaries** —
    `roombook/src/roombook/domain/` and the error mapping in each
    driving adapter under `.../adapters/inbound/`.
21. **Events, the Outbox, and Messaging** —
    `roombook/src/roombook/adapters/outbound/outbox/` and
    `.../adapters/inbound/messaging/`.
22. **Observability Without Touching the Domain** —
    `roombook/src/roombook/adapters/outbound/observability/`.

## Part VI — Evolution

23. **When Not to Do Any of This** — no code.
24. **Migrating a Framework-Shaped App** — `ch24/step1/` to
    `ch24/step5/`, starting from `ch01/`.
25. **From One Hexagon to Many** — `ch25/` and
    `ch25/violation.patch`.

**Conclusion — The Whole Service** — `roombook/`.

## Appendices

- **A — The Architectures on One Page**: `architectures/*/`, one
  `pyproject.toml` contract per architecture.
- **B — import-linter Recipes**: the `[tool.importlinter]`
  sections of `architectures/*/pyproject.toml`,
  `ch07/*/pyproject.toml`, `ch24/step5/pyproject.toml`,
  `ch25/pyproject.toml` and `roombook/pyproject.toml`.

Recorded command output for every chapter directory lives in
`docs/outputs/<directory>/`; the first line of each file is the
command that produced it.
