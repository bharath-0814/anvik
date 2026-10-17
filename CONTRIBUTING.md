# Contributing to Anvik

Thank you for your interest in contributing to **Anvik**, the UPI Fraud-Ring Graph Investigator developed for the **Code-e-Manipal Hackathon**.

To maintain codebase integrity, code quality, and alignment across team members, please review our contribution guidelines.

---

## 1. Team Ownership Boundaries

Anvik follows a strict 6-member team ownership structure (see [`AGENTS.md`](AGENTS.md)):

- **Members 1 & 2 (Piyush)**: Owns frontend development, UI/UX architecture, Cytoscape.js graph canvas, timeline scrubber, and report rendering.
- **Member 3 (Bharath)**: Sole owner of backend development, FastAPI services, Turso libSQL schema and repository, NetworkX graph engine, fraud detection rules, and priority scoring.
- **Member 4 (Aryan)**: Synthetic dataset QA, schema conformance, referential integrity verification, and ground-truth validation.
- **Member 5 (Shivam)**: Synthetic dataset engineering, entity synthesis, and fraud ring topology seeding.
- **Member 6**: Demonstrations, presentation storytelling, and deliverables.

> [!WARNING]
> Respect designated member ownership boundaries. Never modify backend engine logic or frontend component architecture without coordination with the designated owner.

---

## 2. Development Workflow

### Branch Conventions
- `main`: Production-ready, deployable branch.
- `feat/<feature-name>`: New feature implementations.
- `fix/<issue-name>`: Bug fixes and issue patches.
- `chore/<task-name>`: Dependency updates, CI/CD, and repository maintenance.

### Conventional Commits
Please format commit messages according to the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat(scope): add new feature`
- `fix(scope): resolve bug`
- `test(scope): add unit or integration tests`
- `docs(scope): update documentation`
- `chore(scope): configuration or repository hygiene`

---

## 3. Testing & Quality Verification

All pull requests must pass local tests and automated GitHub Actions CI before merging:

### Backend Testing (Python / pytest)
```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Execute test suite (88 unit and integration tests)
pytest backend/tests
```

### Frontend Testing & Build (Node / Vite)
```bash
cd frontend

# Run unit tests (13 tests)
npm test

# Verify production compilation
npm run build
```

---

## 4. Security & Compliance Checklist

Before submitting a Pull Request:
1. **Zero Credentials**: Verify no `.env` files, API tokens, passwords, or cloud credentials are staged (`git status`).
2. **Synthetic Data Only**: Verify that all test cases and fixtures utilize artificial, synthetic entities.
3. **Documentation Framework**: Preserve placeholder files in `docs/*.md` until formal documentation phases.
