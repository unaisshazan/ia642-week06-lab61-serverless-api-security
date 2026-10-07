#!/usr/bin/env python3
"""IA642 Lab 6.1 report: midterm-style LaTeX (11pt, 1in margins), then pdflatex."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LAB_DIR = SCRIPT_DIR.parent
EV = SCRIPT_DIR / "evidence"
TEX_DIR = SCRIPT_DIR / "latex_build"
TEX_PATH = TEX_DIR / "lab61.tex"
PDF_OUT = LAB_DIR / "Ali_Usama_IA642_Week06_Lab6.1_Serverless_API_Security.pdf"
SUBMIT_DIR = LAB_DIR / "SUBMIT_Lab61"
SUBMIT_PDF = SUBMIT_DIR / PDF_OUT.name


def read_ev(name: str) -> str:
    p = EV / name
    if not p.is_file():
        return f"[missing: {name}]"
    raw = p.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = text.replace("\ufeff", "")
    # keep printable + common whitespace only (PowerShell evidence is ASCII)
    text = "".join(ch if (ch in "\n\t" or 32 <= ord(ch) <= 126) else " " for ch in text)
    return text.strip()


def verb(s: str) -> str:
    s = s.replace("\x00", "").replace("\ufeff", "")
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s)


def fmt_headers(raw: str) -> str:
    for tok in [
        "Date:",
        "Content-Type:",
        "Content-Length:",
        "Connection:",
        "x-content-type-options:",
        "content-security-policy:",
        "cache-control:",
        "strict-transport-security:",
        "Apigw-Requestid:",
    ]:
        raw = raw.replace(" " + tok, "\n" + tok)
    return raw.strip()


def listing(title: str, body: str) -> str:
    return "\n".join(
        [
            rf"\noindent\textbf{{{title}}}",
            r"\begin{lstlisting}",
            verb(body.strip()),
            r"\end{lstlisting}",
            "",
        ]
    )


def build_tex() -> str:
    role = read_ev("01_role_arn.txt")
    identity = read_ev("00_identity.json")
    endpoint = read_ev("02_endpoint.txt")
    dynamo = read_ev("01b_dynamo_count.txt")
    cognito = read_ev("01d_cognito.txt")
    lambda_arn = read_ev("01c_lambda_arn.txt")
    bola = read_ev("03_bola.txt")
    methods = read_ev("04_methods_token.txt")
    fixed = read_ev("05_bola_fixed.txt")
    leak = read_ev("06_partD_leak.txt")
    allow = read_ev("06b_partD_fixed.txt")
    headers = fmt_headers(read_ev("06_headers.txt"))
    teardown = read_ev("07_teardown.txt")
    diff_bola = read_ev("diff_bola_fix.txt")
    diff_d = read_ev("diff_allowlist_headers.txt")
    final_code = read_ev("fixed_app_final.py")

    preamble = r"""
\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
\sloppy\emergencystretch=4em
\usepackage{array,booktabs,tabularx,enumitem,parskip,ragged2e,titlesec,microtype,xcolor,listings,needspace,xurl,fancyhdr,graphicx,float,seqsplit}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\hypersetup{pdfauthor={Unais Ali and Hafiz Usama}, pdftitle={IA 642 Lab 6.1 Serverless API Security}}
\definecolor{tblhead}{HTML}{1F4E79}
\definecolor{codebg}{HTML}{F7FAFC}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.28}
\setlist[itemize]{leftmargin=1.2em,itemsep=0.25em,topsep=0.3em}
\setlist[enumerate]{leftmargin=1.3em,itemsep=0.3em,topsep=0.3em}
\newcolumntype{Y}{>{\RaggedRight\arraybackslash}X}
\newcolumntype{P}[1]{>{\RaggedRight\arraybackslash}p{#1}}
\titleformat{name=\section,numberless}{\large\bfseries\color{tblhead}}{}{0em}{}
\titleformat{name=\subsection,numberless}{\normalsize\bfseries\color{tblhead}}{}{0em}{}
\lstset{
  basicstyle=\ttfamily\footnotesize,
  backgroundcolor=\color{codebg},
  frame=single,
  rulecolor=\color{tblhead},
  breaklines=true,
  breakatwhitespace=false,
  columns=fullflexible,
  keepspaces=true,
  showstringspaces=false,
  aboveskip=0.45em,
  belowskip=0.45em,
  xleftmargin=2pt,
  xrightmargin=2pt,
  literate=*{\\}{{\textbackslash\allowbreak}}1
}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[L]{\footnotesize Ali \& Usama | IA 642 Lab 6.1}
\fancyfoot[R]{\footnotesize Page \thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0.4pt}
\begin{document}
\begin{center}
{\LARGE\bfseries IA 642 Defensive Security}\\[0.25em]
{\Large Week 06, Module 01 --- Lab 6.1}\\[0.15em]
{\large Breaking and Fixing a Serverless API on AWS}\\[0.15em]
{\normalsize Cloud \& Application/API Security (Free Tier)}\\[0.3em]
\end{center}

\begin{tabularx}{\textwidth}{@{}l Y l Y@{}}
\toprule
\textbf{Group members} & Unais Ali & \textbf{EID} & E02805019 \\
 & Hafiz Usama &  & E02574092 \\
\textbf{Course} & IA 642 Defensive Security & \textbf{Lab} & 6.1 (Week 06) \\
\textbf{Date} & October 7, 2026 & \textbf{Region} & us-east-1 \\
\textbf{AWS account} & 626672433625 & \textbf{Prefix} & \texttt{ia642-lab} \\
\textbf{GitHub} & \multicolumn{3}{Y@{}}{\url{https://github.com/unaisshazan/ia642-week06-lab61-serverless-api-security}} \\
\textbf{Live frontend} & \multicolumn{3}{Y@{}}{\url{http://ia642-lab-frontend-626672433625.s3-website-us-east-1.amazonaws.com}} \\
\bottomrule
\end{tabularx}

\vspace{0.55em}
\section*{Lab overview}
Meridian Health Network is moving patient-facing account/billing APIs to a serverless tier.
This lab deploys a deliberately flawed stack on AWS Free Tier (Cognito + API Gateway HTTP API +
Lambda + DynamoDB), proves OWASP API1:2023 Broken Object Level Authorization (BOLA) and
API3:2023 Broken Object Property Level Authorization (excessive data exposure), hardens the
handler to ASVS v5.0.0 requirements 8.2.2, 8.2.3, and 3.4.x, writes backlog-ready security
requirements, and tears every resource down the same day.

\section*{Environment and tooling}
\begin{itemize}
  \item \textbf{Identity:} AWS CLI configured for account 626672433625 (root sandbox); verified with
        \texttt{aws sts get-caller-identity} before create/delete.
  \item \textbf{Region / prefix:} \texttt{us-east-1}, resource prefix \texttt{ia642-lab}.
  \item \textbf{Runtime:} Python 3.12 Lambda; Cognito USER\_PASSWORD\_AUTH users \texttt{alice}/\texttt{bob};
        DynamoDB on-demand table \texttt{ia642-lab-accounts} (accounts 1001/1002).
  \item \textbf{Automation:} Windows runner \texttt{run\_lab61.ps1} (JSON via \texttt{file://} paths);
        evidence under \texttt{evidence/}.
  \item \textbf{Public repo:} code, evidence captures, frontend, and report PDF (no AWS access keys):
        \url{https://github.com/unaisshazan/ia642-week06-lab61-serverless-api-security}
  \item \textbf{Live frontend demo:} Cognito login + GET \texttt{/accounts/\{id\}} against the Free Tier API:
        \url{http://ia642-lab-frontend-626672433625.s3-website-us-east-1.amazonaws.com}
  \item \textbf{Safety / cost:} Free Tier / always-free when torn down same day; no AWS secrets committed.
\end{itemize}
"""

    body: list[str] = []

    body.append(r"\section*{Part A --- Deploy the vulnerable API}")
    body.append(
        r"Created an IAM execution role trusted only by \texttt{lambda.amazonaws.com}, seeded DynamoDB "
        r"with alice/bob ownership rows, deployed intentionally vulnerable \texttt{vuln\_app.handler} "
        r"(returns any item to any authenticated caller), Cognito user pool/client, and API Gateway "
        r"route \texttt{GET /accounts/\{id\}} with JWT authorizer. Authentication is enforced at the edge; "
        r"authorization is not."
    )
    body.append(listing("Evidence \#1 --- IAM role ARN (create-role)", role))
    body.append(
        listing(
            "Supporting deploy artifacts",
            f"{identity}\n{dynamo}\n{cognito}\nlambda={lambda_arn}",
        )
    )
    body.append(listing("Evidence \#2 --- API endpoint URL", endpoint))

    body.append(r"\section*{Part B --- Attack it (BOLA)}")
    body.append(
        r"No token yields HTTP 401 (JWT authorizer works). Alice's valid IdToken reads her own account "
        r"1001 successfully. The same token reading Bob's account 1002 also succeeds and returns Bob's "
        r"balance and \texttt{card\_last4}. That is OWASP \textbf{API1:2023 BOLA}: authentication succeeded; "
        r"object-level authorization never ran."
    )
    body.append(listing("Evidence \#3 --- 401 check, happy path, and BOLA leak", bola))

    body.append(r"\subsection*{Critical thinking \#1 --- Authentication vs authorization}")
    body.append(
        r"\textbf{Authentication} answers ``who are you?'' The Cognito JWT authorizer verified Alice's "
        r"signature, issuer, audience, and \texttt{token\_use} before Lambda executed. "
        r"\textbf{Authorization} answers ``what may you access?'' The vulnerable handler never compared "
        r"\texttt{item[``owner'']} to \texttt{cognito:username}, so any authenticated principal could "
        r"request any \texttt{account\_id}. Stronger authentication (longer passwords, MFA, shorter expiry) "
        r"would still issue a valid Alice token; she would still request 1002 and still receive Bob's "
        r"billing data. Only server-side object-level authorization closes API1/BOLA."
    )

    body.append(
        r"POST/DELETE return 404 because only GET (plus HEAD for header probes) is routed---unused "
        r"methods are not silently accepted (ASVS v5.0.0-4.1.4). A corrupted JWT signature returns 401 "
        r"(ASVS v5.0.0-9.1.1). Decoded claims show \texttt{token\_use=id}, correct \texttt{aud}, Cognito "
        r"\texttt{iss}, and \texttt{cognito:username=alice} (ASVS v5.0.0-9.2.2 / 9.2.3)."
    )
    body.append(listing("Evidence \#4 --- HTTP methods, tampered token, decoded claims", methods))

    body.append(r"\section*{Map findings to ASVS 5.0}")
    body.append(
        "\n".join(
            [
                r"{\footnotesize",
                r"\begin{tabularx}{\textwidth}{@{}P{3.1cm} P{2.6cm} Y c@{}}",
                r"\toprule",
                r"\rowcolor{tblhead}\textcolor{white}{\textbf{Observation}} & "
                r"\textcolor{white}{\textbf{ASVS 5.0}} & "
                r"\textcolor{white}{\textbf{Requirement (paraphrased)}} & "
                r"\textcolor{white}{\textbf{L}} \\",
                r"\midrule",
                r"3.1 no-token $\rightarrow$ 401 & v5.0.0-8.2.1 / JWT authz & Unauthenticated callers blocked & 1 \\",
                r"3.3 Alice read Bob (BOLA) & v5.0.0-8.2.2 & Data-specific access only with explicit permission (IDOR/BOLA) & 1 \\",
                r"Enforcement server-side & v5.0.0-8.3.1 & Authz at trusted service layer, not client & 1 \\",
                r"POST/DELETE $\rightarrow$ 404 & v5.0.0-4.1.4 & Only explicitly supported HTTP methods & 3 \\",
                r"Tampered token $\rightarrow$ 401 & v5.0.0-9.1.1 & Validate signature/MAC before trust & 1 \\",
                r"aud / token\_use checked & v5.0.0-9.2.2 / 9.2.3 & Correct token type and audience & 2 \\",
                r"Full item returned (Part D) & v5.0.0-8.2.3 & Expose only authorized fields & 2 \\",
                r"HSTS / nosniff / CSP & v5.0.0-3.4.1 / 3.4.4 / 3.4.3 & Browser security headers & 1 \\",
                r"\bottomrule",
                r"\end{tabularx}}",
            ]
        )
    )
    # Need colortbl for rowcolor
    # I'll add \usepackage{colortbl} to preamble - fix below when writing file

    body.append(r"\section*{Part C --- Fix BOLA and add security headers}")
    body.append(
        r"Object-level check: if \texttt{item.get(``owner'')} $\neq$ caller, return HTTP 403. "
        r"Alice still reads 1001 (200); Bob's 1002 is denied (403). This is ASVS v5.0.0-8.2.2."
    )
    body.append(listing("Code diff --- BOLA fix (vuln\_app.py $\rightarrow$ fixed\_app\_bola\_only.py)", diff_bola))
    body.append(listing("Evidence \#5 --- Post-fix retest (200 / 403)", fixed))
    body.append(
        r"Responses also carry ASVS V3 headers: \texttt{Strict-Transport-Security} (3.4.1), "
        r"\texttt{X-Content-Type-Options: nosniff} (3.4.4), restrictive "
        r"\texttt{Content-Security-Policy} (3.4.3/3.4.6), and \texttt{Cache-Control: no-store}."
    )
    body.append(listing("Evidence \#6 --- Response headers (curl -sI)", headers))

    body.append(r"\subsection*{Critical thinking \#2 --- ASVS levels vs severity}")
    body.append(
        r"ASVS Level 1/2/3 is an \textbf{assurance target} for how comprehensively an application should "
        r"be verified, not a ranking of how damaging a failed control is. HSTS (3.4.1) and object-level "
        r"authorization (8.2.2) can both appear at L1 because both are baseline expectations for many apps, "
        r"yet their business impact differs. Organizations choose L1/L2/L3 from data sensitivity, threat "
        r"model, and regulation. Meridian handles PHI under HIPAA: a billing API that can exfiltrate another "
        r"patient's account is a reportable privacy incident. Meridian should target at least L2 for any "
        r"PHI-touching API (and L3 for high-assurance clinical systems), treat 8.2.2 and 8.2.3 as release "
        r"blockers, and still ship L1 browser headers because the same origin feeds a web portal---without "
        r"pretending headers equal object authorization in risk."
    )

    body.append(r"\section*{Security requirements table}")
    body.append(
        "\n".join(
            [
                r"{\footnotesize",
                r"\begin{tabularx}{\textwidth}{@{}c P{4.4cm} P{2.3cm} Y@{}}",
                r"\toprule",
                r"\rowcolor{tblhead}",
                r"\textcolor{white}{\textbf{ID}} & "
                r"\textcolor{white}{\textbf{Security requirement (testable)}} & "
                r"\textcolor{white}{\textbf{ASVS}} & "
                r"\textcolor{white}{\textbf{Verification}} \\",
                r"\midrule",
                r"SR-1 & Every endpoint returning a user-owned object MUST verify the authenticated caller owns that object before returning it. & v5.0.0-8.2.2 & User A requests user B's object $\rightarrow$ 403; owner $\rightarrow$ 200. \\",
                r"SR-2 & All API responses rendered by a browser MUST include HSTS, nosniff, and a restrictive CSP. & v5.0.0-3.4.1 / 3.4.4 / 3.4.3 & \texttt{curl -I} asserts the three headers on every 2xx. \\",
                r"SR-3 & Account-read routes MUST accept only explicitly configured HTTP methods (GET; HEAD only if required). POST/PUT/PATCH/DELETE MUST not be auto-mapped. & v5.0.0-4.1.4 & Probe with POST/DELETE using a valid token; expect 404/405. \\",
                r"SR-4 & API Gateway MUST reject JWTs with invalid signatures, wrong aud, wrong iss, or wrong token\_use before Lambda executes. & v5.0.0-9.1.1 / 9.2.2 / 9.2.3 & Corrupted signature $\rightarrow$ 401; decode valid claims and assert aud/iss/token\_use. \\",
                r"\bottomrule",
                r"\end{tabularx}}",
            ]
        )
    )

    body.append(r"\section*{Tear down}")
    body.append(
        r"Deleted API Gateway API, Lambda, DynamoDB table, Cognito user pool, IAM inline policy and role. "
        r"Confirmation queries for prefix \texttt{ia642-lab} returned empty lists."
    )
    body.append(listing("Evidence \#7 --- Empty teardown confirmation", teardown))

    body.append(r"\section*{Part D --- Graded challenge (excessive data exposure)}")
    body.append(r"\subsection*{1. Vulnerability class}")
    body.append(
        r"Returning the whole DynamoDB item is OWASP API Top 10 (2023) "
        r"\textbf{API3:2023 Broken Object Property Level Authorization} (excessive data exposure). "
        r"Corresponding ASVS field-level requirement: \textbf{v5.0.0-8.2.3}---return only properties the "
        r"consumer is authorized to see."
    )
    body.append(r"\subsection*{2. Exploit}")
    body.append(
        r"After the BOLA ownership fix, sensitive attributes were added to account 1001 via "
        r"\texttt{dynamodb update-item} (\texttt{internal\_note=VIP-PHI-REVIEW}, "
        r"\texttt{fraud\_score=0.91}). Alice's authorized GET still leaked them because the handler "
        r"serialized \texttt{item} wholesale:"
    )
    body.append(listing("Part D exploit --- authorized owner, still leaking fields", leak))

    body.append(r"\subsection*{3. Allow-list fix}")
    body.append(
        r"Response built from \texttt{ALLOWED\_FIELDS = (``account\_id'', ``balance'', ``card\_last4'')} "
        r"only. After redeploy, \texttt{internal\_note} and \texttt{fraud\_score} disappear. An allow-list "
        r"is safer than a deny-list because new sensitive columns added later are excluded by default; a "
        r"blocklist must be updated every time the schema grows and will miss fields nobody remembered to ban."
    )
    body.append(listing("Part D fixed output --- allow-list", allow))
    body.append(listing("Code diff --- allow-list + security headers", diff_d))

    body.append(r"\subsection*{4. Least privilege}")
    body.append(
        r"Section 2.2 granted the Lambda role broad DynamoDB actions on \texttt{Resource ``*''}. "
        r"To satisfy least privilege: (a) grant only \texttt{dynamodb:GetItem} for a read-only API; "
        r"(b) set \texttt{Resource} to the specific table ARN "
        r"\texttt{arn:aws:dynamodb:us-east-1:626672433625:table/ia642-lab-accounts} "
        r"(plus index ARNs if needed); (c) omit PutItem/UpdateItem/Scan/Query unless required. "
        r"That control belongs to ASVS \textbf{V15 Secure Coding \& Architecture} (least-privilege / "
        r"secure cloud IAM configuration), with related trust-boundary themes in V1---not to browser headers."
    )

    body.append(r"\section*{Final hardened handler}")
    body.append(listing("fixed\_app\_final.py (BOLA + allow-list + ASVS headers)", final_code))

    body.append(
        r"\vspace{0.4em}\noindent\textbf{Conclusion.} Authentication alone did not protect Meridian's "
        r"accounts. Object-level authorization (8.2.2) stopped cross-patient reads; field allow-listing "
        r"(8.2.3 / API3) stopped schema leakage; method restriction, JWT validation, and security headers "
        r"completed the ASVS map. Written SRs turn these fixes into backlog-ready acceptance tests. "
        r"Stack torn down same day --- Free Tier cost remains \$0."
    )
    body.append(r"\end{document}")

    # Fix preamble: add colortbl
    preamble = preamble.replace(
        r"\usepackage{array,booktabs,tabularx,enumitem,parskip,ragged2e,titlesec,microtype,xcolor,listings,needspace,xurl,fancyhdr,graphicx,float,seqsplit}",
        r"\usepackage{array,booktabs,tabularx,enumitem,parskip,ragged2e,titlesec,microtype,xcolor,colortbl,listings,needspace,xurl,fancyhdr,graphicx,float,seqsplit}",
    )

    return preamble + "\n".join(body)


def compile_pdf() -> int:
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    SUBMIT_DIR.mkdir(parents=True, exist_ok=True)
    TEX_PATH.write_text(build_tex(), encoding="utf-8")

    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        candidate = Path(r"C:\Users\unais\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe")
        if candidate.is_file():
            pdflatex = str(candidate)
        else:
            print("pdflatex not found", file=sys.stderr)
            return 1

    for pass_no in (1, 2):
        proc = subprocess.run(
            [
                pdflatex,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(TEX_DIR),
                str(TEX_PATH.name),
            ],
            cwd=str(TEX_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            print(proc.stdout[-6000:] if proc.stdout else "", file=sys.stderr)
            print(proc.stderr[-2000:] if proc.stderr else "", file=sys.stderr)
            log = TEX_DIR / "lab61.log"
            if log.is_file():
                print(log.read_text(encoding="utf-8", errors="replace")[-5000:], file=sys.stderr)
            return proc.returncode
        print(f"pdflatex pass {pass_no} OK")

    built = TEX_DIR / "lab61.pdf"
    shutil.copy2(built, PDF_OUT)
    shutil.copy2(built, SUBMIT_PDF)

    # refresh submit evidence/code
    for name in ("evidence", "code"):
        src = SCRIPT_DIR / name
        dst = SUBMIT_DIR / name
        if dst.exists():
            shutil.rmtree(dst)
        if src.is_dir():
            shutil.copytree(src, dst)

    pages = "?"
    try:
        import pypdf

        pages = str(len(pypdf.PdfReader(str(PDF_OUT)).pages))
    except Exception:
        pass
    print(f"Wrote: {PDF_OUT}")
    print(f"Submit: {SUBMIT_PDF}")
    print(f"Size:  {PDF_OUT.stat().st_size:,} bytes")
    print(f"Pages: {pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(compile_pdf())
