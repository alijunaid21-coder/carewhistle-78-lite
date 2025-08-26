#!/usr/bin/env bash
# Set up GitHub project and issues based on Carewhistle implementation spec.
# Requires GitHub CLI (gh) authenticated with repo access.
# Usage: ./scripts/gh_project_setup.sh <owner/repo> <project-name>

set -euo pipefail
REPO=${1:?"repo (owner/name) required"}
PROJECT_NAME=${2:-"Carewhistle Production MVP"}

echo "Creating project $PROJECT_NAME in $REPO..."
PROJECT_ID=$(gh project create "$PROJECT_NAME" --owner "${REPO%%/*}" --format json | jq -r '.id')

echo "Project created with ID $PROJECT_ID";

create_issue(){
  local title="$1"; shift
  local body="$1"; shift
  echo "Creating issue: $title"
  gh issue create --repo "$REPO" --title "$title" --body "$body" >/dev/null
}

create_issue "1. Architecture & Data" "- [ ] Multi-tenant model
- [ ] Company Code generation (5-8 chars)
- [ ] Reporter uses Company Code only
- [ ] SQLite (dev) & Postgres (prod) via SQLAlchemy
- [ ] Optional MongoDB for audit logs/attachments
- [ ] Data models for companies, users, reports, messages, notifications, settings, content_blocks, media, audit_log
- [ ] Fernet encryption with key rotation
- [ ] Secrets only from environment
- [ ] Secure sessions & CSRF tokens"

create_issue "2. Security Controls – ISO/IEC 27001" "- [ ] Org policies & DPAs
- [ ] Risk assessment & DPIA
- [ ] Staff confidentiality & training
- [ ] Cloud facility statements
- [ ] RBAC, MFA, SSO
- [ ] TLS everywhere, HSTS
- [ ] Ops security, logging, rate limiting
- [ ] Secure development & code scanning
- [ ] Backups & DR
- [ ] Supplier security, incident & change mgmt"

create_issue "3. GDPR / UK-GDPR" "- [ ] Controller/Processor roles
- [ ] Lawful basis & DPIA
- [ ] ROPA maintenance
- [ ] Data subject rights workflow
- [ ] Privacy notice
- [ ] Retention & minimisation
- [ ] International transfers & SCCs
- [ ] Breach notification process
- [ ] Essential cookies only / consent banner"

create_issue "4. Public Site" "- [ ] Navigation: Home, How it works, Make a Report, Plans & Pricing
- [ ] Hero tagline
- [ ] Long-form marketing copy
- [ ] £149.99/year pricing with Stripe/PayPal buttons
- [ ] Contact info and optional YouTube embed
- [ ] Whistle-with-wings icon"

create_issue "5. Reporting" "- [ ] Company Code input
- [ ] Subject, Category, Description
- [ ] Actions taken textarea
- [ ] Feedback option yes/no
- [ ] Memorable word & preferred contact
- [ ] Anonymous vs confidential mode
- [ ] Math CAPTCHA
- [ ] Case Code generation & PIN hashing
- [ ] Reporter follow-up portal"

create_issue "6. Admin Portal" "- [ ] Sidebar & navigation
- [ ] Overview dashboards with Chart.js
- [ ] Companies CRUD & analytics
- [ ] Users CRUD with MFA option
- [ ] Reports CRUD & assignment
- [ ] Messages: admin↔reporter and admin↔manager threads
- [ ] Notifications
- [ ] Media uploads & hero selection
- [ ] Content management & versioning
- [ ] Settings (non-secret) and Audit log"

create_issue "7. Manager Portal" "- [ ] Sidebar with Overview, Reports, Messages, Notifications
- [ ] Company-only dashboards
- [ ] Assigned report views
- [ ] Admin-manager chat
- [ ] Notification feed"

create_issue "8. Email & Notifications" "- [ ] SMTP integration
- [ ] Event-based emails (new report, assignment, etc.)
- [ ] Branded templates with opt-out
- [ ] In-app notifications mirroring email events"

create_issue "9. Payments" "- [ ] Stripe subscription & webhook
- [ ] PayPal smart buttons & webhook
- [ ] Admin subscriptions page"

create_issue "10. SSO & MFA" "- [ ] Google/Microsoft OAuth with allow-list
- [ ] Admin TOTP MFA with recovery codes"

create_issue "11. UX / Accessibility" "- [ ] Tailwind theme & responsive layouts
- [ ] Chart.js integration
- [ ] ARIA labels, focus states, AA contrast"

create_issue "12. Ops, Logs, Backups" "- [ ] Structured logging & rotation
- [ ] Nightly encrypted backups & restore tests
- [ ] Uptime & error monitoring
- [ ] Rate limiting & WAF"

create_issue "13. Deployment & Hardening" "- [ ] Gunicorn behind Nginx with TLS 1.2+
- [ ] HSTS, Secure/HTTPOnly cookies
- [ ] Alembic migrations for Postgres
- [ ] Static uploads under /static/uploads"

create_issue "14. QA / Acceptance Tests" "- [ ] Company code uniqueness
- [ ] Public report flow with CAPTCHA
- [ ] Reporter portal chat
- [ ] Manager assignment & chat
- [ ] Demo data charts
- [ ] Email and notification tests
- [ ] Payment sandbox
- [ ] Settings toggles
- [ ] Encryption key rotation
- [ ] Backup/restore, rate limit, CSRF, password hash, MFA"

create_issue "15. Documentation" "- [ ] Admin Guide
- [ ] Security Overview
- [ ] GDPR pack (DPIA, ROPA, Privacy Policy, DPA template, sub-processor list, retention schedule)"

echo "All issues created. Add them to project manually or via gh automation." 
