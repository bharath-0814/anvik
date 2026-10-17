# Security Policy

## 1. Scope & System Identity

**Anvik** is an investigative decision-support system built for the **Code-e-Manipal Hackathon (PS 16)** to detect coordinated UPI fraud topologies across synthetic financial interactions.

---

## 2. Synthetic Data Exclusivity

- **100% Synthetic Records**: Anvik exclusively processes synthetic transaction, account, device, and complaint datasets.
- **Zero Real Banking Connectivity**: The platform does not connect to live banking core switches, live payment gateways, production NPCI UPI switches, or real customer accounts.
- **No Personal Identifiable Information (PII)**: All virtual payment addresses (VPAs), account numbers, names, phone numbers, and hardware IDs are generated artificially for benchmark testing. Any resemblance to real entities or live accounts is purely coincidental.

---

## 3. Zero Credential & Secret Management

- **Zero Committed Secrets**: No live API keys, database passwords, private cryptographic keys, or production authorization tokens are ever committed to this repository.
- **Defense-in-Depth Git Exclusions**: All environment files (`.env*`), private keys (`*.pem`, `*.key`), database files (`*.sqlite3`, `*.db`), and deployment states (`.vercel/`) are strictly excluded via multi-layered `.gitignore` policies.
- **Production Secret Injection**: Cloud deployments (Vercel, Turso) utilize isolated, runtime environment variables with token masking in system logs.

---

## 4. Investigative Ethics & Decision Support

- **Analytical Decision-Support Only**: Anvik is an investigative aid designed to surface anomalies and explainable leads for human review. It is not an automated judicial tool.
- **No Inherent Proof of Guilt**: Flagged accounts, shared device clusters, and converging complaint paths represent deterministic investigative hypotheses for further verification by forensic personnel.

---

## 5. Reporting a Vulnerability

If you discover a security vulnerability or potential privacy issue in this repository, please report it responsibly:

1. **Do not open a public GitHub issue.**
2. Send a detailed report to the core maintainers via GitHub Security Advisories or direct email to the backend owner:
   - **Bharath (Member 3)**: [bharathg0814@gmail.com](mailto:bharathg0814@gmail.com)
3. Include relevant proof-of-concept steps, affected endpoints, and suggested remediations.
4. The team will acknowledge receipt within 24 hours and coordinate a coordinated fix.
