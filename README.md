# IA 642 Lab 6.1 — Breaking and Fixing a Serverless API on AWS

**Course:** IA 642 Defensive Security (Eastern Michigan University)  
**Authors:** Unais Ali (E02805019), Hafiz Usama (E02574092)

## Live frontend

http://ia642-lab-frontend-626672433625.s3-website-us-east-1.amazonaws.com

Sign in as `alice` / `Passw0rd!`, then call account `1001` (200) and `1002` (403 after BOLA fix).

## Contents

| Path | Description |
|------|-------------|
| `evidence/` | Captured Ev #1–#7, diffs, hardened handler |
| `code/` | `vuln_app.py`, BOLA-only fix, final allow-list + headers |
| `frontend/` | Browser demo UI (Cognito + API Gateway) |
| `run_lab61.ps1` | End-to-end Free Tier deploy / attack / harden / teardown |
| `build_lab61_latex.py` | LaTeX report builder |
| `Ali_Usama_IA642_Week06_Lab6.1_Serverless_API_Security.pdf` | Graded report |

## Report PDF

[`Ali_Usama_IA642_Week06_Lab6.1_Serverless_API_Security.pdf`](./Ali_Usama_IA642_Week06_Lab6.1_Serverless_API_Security.pdf)

## Security note

This repository contains lab evidence and demo passwords used only in a disposable Free Tier sandbox. **No AWS access keys or long-lived credentials are committed.**
