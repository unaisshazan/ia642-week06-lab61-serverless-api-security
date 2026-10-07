"""Build Distinguished Lab 6.1 PDF from live AWS evidence."""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

ROOT = Path(__file__).resolve().parent
EV = ROOT / "evidence"
OUT = ROOT.parent / "Ali_IA642_Week06_Lab6.1_Serverless_API_Security.pdf"
SUBMIT = ROOT.parent / "SUBMIT_Lab61"
SUBMIT.mkdir(exist_ok=True)
OUT2 = SUBMIT / OUT.name

NAVY = HexColor("#1F4E79")
LIGHT = HexColor("#E8EEF5")
CODE_BG = HexColor("#F5F7FA")
GREEN = HexColor("#1B5E20")
RED = HexColor("#B71C1C")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleMain", parent=styles["Title"], fontSize=13, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="SubCenter", parent=styles["Normal"], fontSize=9.5, alignment=TA_CENTER, spaceAfter=2))
styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=11.5, textColor=NAVY, spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=10, textColor=NAVY, spaceBefore=8, spaceAfter=3))
styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=8.4, leading=11, alignment=TA_JUSTIFY, spaceAfter=4))
styles.add(ParagraphStyle(name="Tiny", parent=styles["Normal"], fontSize=7.2, leading=9.2, alignment=TA_LEFT))
styles.add(ParagraphStyle(name="CellHead", parent=styles["Normal"], fontSize=7.6, leading=9.8, alignment=TA_LEFT, textColor=white, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Cell", parent=styles["Normal"], fontSize=7.3, leading=9.5, alignment=TA_LEFT, fontName="Helvetica"))
styles.add(ParagraphStyle(name="EvLabel", parent=styles["Normal"], fontSize=8.2, leading=10.5, textColor=NAVY, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=2))
styles.add(ParagraphStyle(name="CodeBlock", parent=styles["Code"], fontSize=6.6, leading=8.4, fontName="Courier", backColor=CODE_BG, spaceBefore=2, spaceAfter=6))
styles.add(ParagraphStyle(name="ItalicNote", parent=styles["Normal"], fontSize=8.0, leading=10.2, textColor=HexColor("#333333"), spaceAfter=6))


def P(text, style="Body"):
    return Paragraph(text.replace("\n", "<br/>"), styles[style])


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def read(name: str) -> str:
    return (EV / name).read_text(encoding="utf-8", errors="replace").strip()


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(HexColor("#666666"))
    canvas.drawString(0.7 * inch, 0.45 * inch, "IA 642 Lab 6.1 | Unais Ali | AWS us-east-1 Free Tier")
    canvas.drawRightString(7.8 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def make_table(headers, rows, col_widths):
    data = [[P(f"<b>{h}</b>", "CellHead") for h in headers]]
    for row in rows:
        data.append([P(c, "Cell") for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, HexColor("#102A43")),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#90A4AE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT]),
    ]))
    return t


def code_block(text: str, max_chars=3200):
    t = text.strip()
    if len(t) > max_chars:
        t = t[:max_chars] + "\n... [truncated]"
    return Preformatted(t, styles["CodeBlock"], maxLineLength=110)


identity = read("00_identity.json")
endpoint = read("02_endpoint.txt")
bola = read("03_bola.txt")
methods = read("04_methods_token.txt")
fixed = read("05_bola_fixed.txt")
leak = read("06_partD_leak.txt")
allow = read("06b_partD_fixed.txt")
headers = read("06_headers.txt")
teardown = read("07_teardown.txt")
dynamo = read("01b_dynamo_count.txt")
cognito = read("01d_cognito.txt")
diff_bola = read("diff_bola_fix.txt")
diff_d = read("diff_allowlist_headers.txt")

for tok in ["Date:", "Content-Type:", "Content-Length:", "Connection:", "x-content-type-options:",
            "content-security-policy:", "cache-control:", "strict-transport-security:", "Apigw-Requestid:"]:
    headers = headers.replace(" " + tok, "\n" + tok)

story = []
story.append(P("EASTERN MICHIGAN UNIVERSITY", "SubCenter"))
story.append(P("College of Engineering and Technology", "SubCenter"))
story.append(P("IA 642: Defensive Security", "TitleMain"))
story.append(P("<b>Week 06, Module 01 Lab 6.1: Breaking and Fixing a Serverless API on AWS</b>", "SubCenter"))
story.append(P("Cloud &amp; Application/API Security · Cognito + API Gateway + Lambda + DynamoDB", "SubCenter"))
story.append(Spacer(1, 6))

meta = [
    [P("<b>Student</b>", "Cell"), P("Unais Ali", "Cell"), P("<b>EID</b>", "Cell"), P("E02805019", "Cell")],
    [P("<b>Course</b>", "Cell"), P("IA 642 Defensive Security", "Cell"), P("<b>Lab</b>", "Cell"), P("6.1 (Week 06)", "Cell")],
    [P("<b>Region</b>", "Cell"), P("us-east-1 (Free Tier)", "Cell"), P("<b>Date</b>", "Cell"), P("07 October 2026", "Cell")],
    [P("<b>Account</b>", "Cell"), P("626672433625", "Cell"), P("<b>Prefix</b>", "Cell"), P("ia642-lab", "Cell")],
]
mt = Table(meta, colWidths=[1.1 * inch, 2.5 * inch, 0.9 * inch, 2.2 * inch])
mt.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("BACKGROUND", (0, 0), (0, -1), LIGHT),
    ("BACKGROUND", (2, 0), (2, -1), LIGHT),
]))
story.append(mt)
story.append(Spacer(1, 6))
story.append(P(
    "<i>Meridian Health Network is moving patient-facing billing APIs to a serverless tier. "
    "This lab deploys a deliberately flawed API on AWS Free Tier, proves OWASP API1:2023 BOLA "
    "and API3:2023 excessive data exposure, hardens to ASVS v5.0.0 (8.2.2, 8.2.3, 3.4.x), "
    "writes security requirements, and tears the stack down the same day.</i>",
    "ItalicNote",
))

# --- Overview ---
story.append(P("1. Lab Overview and Architecture", "H1"))
story.append(P(
    "Stack: Amazon Cognito user pool (alice/bob) issues JWTs; API Gateway HTTP API validates "
    "iss/aud/signature via a JWT authorizer; Lambda (Python 3.12) reads DynamoDB table "
    "<font face='Courier'>ia642-lab-accounts</font>. Authentication was correct from minute one; "
    "authorization and field-level filtering were not. All resources used Free Tier / always-free "
    "controls and were deleted after capture.",
))
story.append(P("Evidence #1 — Caller identity (sts get-caller-identity)", "EvLabel"))
story.append(code_block(identity))
story.append(P(f"Evidence — Seeded DynamoDB rows: <font face='Courier'>{esc(dynamo)}</font>; Cognito: <font face='Courier'>{esc(cognito)}</font>", "Tiny"))

# --- Part A ---
story.append(P("2. Part A — Deploy the Vulnerable API", "H1"))
story.append(P(
    "Deployed IAM role <font face='Courier'>ia642-lab-role</font>, DynamoDB table with accounts 1001 (alice) "
    "and 1002 (bob), Lambda <font face='Courier'>vuln_app.handler</font> (returns any item to any authenticated "
    "caller), Cognito pool/client with USER_PASSWORD_AUTH, and API Gateway route "
    "<font face='Courier'>GET /accounts/{id}</font> with JWT authorizer.",
))
story.append(P("Evidence #2 — API endpoint", "EvLabel"))
story.append(code_block(endpoint))

# --- Part B ---
story.append(P("3. Part B — Attack It (BOLA)", "H1"))
story.append(P(
    "Without a token the authorizer returns 401 (authentication works). With alice's valid IdToken, "
    "GET /accounts/1001 succeeds. GET /accounts/1002 also succeeds and returns Bob's balance and "
    "card_last4. That is OWASP <b>API1:2023 Broken Object Level Authorization</b> — an authorization "
    "failure, not an authentication failure.",
))
story.append(P("Evidence #3 — Auth check, happy path, and BOLA leak", "EvLabel"))
story.append(code_block(bola))

story.append(P("Critical Thinking #1 — Authentication vs authorization", "H2"))
story.append(P(
    "<b>Authentication</b> answers “who are you?” The Cognito JWT authorizer verified alice's signature, "
    "issuer, audience, and token_use before the Lambda ran. <b>Authorization</b> answers “what may you "
    "access?” The vulnerable handler never compared <font face='Courier'>item.owner</font> to "
    "<font face='Courier'>cognito:username</font>, so any authenticated principal could read any "
    "account_id. Stronger authentication (longer passwords, MFA, shorter expiry) would still issue a "
    "valid alice token; Alice would still request 1002 and still receive Bob's PHI/billing data. "
    "Only object-level authorization at a trusted server layer closes API1/BOLA.",
))

story.append(P("Evidence #4 — Methods, tamper, claims", "EvLabel"))
story.append(P(
    "POST/DELETE return 404 because only GET (and HEAD for header checks) is routed — unused methods "
    "are not silently accepted (ASVS v5.0.0-4.1.4). A corrupted JWT signature returns 401 "
    "(ASVS v5.0.0-9.1.1). Decoded claims show token_use=id, aud=client id, iss=Cognito pool, "
    "cognito:username=alice (ASVS v5.0.0-9.2.2 / 9.2.3).",
))
story.append(code_block(methods))

# --- ASVS map ---
story.append(P("4. Map Findings to ASVS 5.0", "H1"))
story.append(make_table(
    ["Observation", "ASVS 5.0", "What it requires", "L"],
    [
        ["3.1 no-token → 401", "v5.0.0-8.2.1 / JWT authz", "Unauthenticated callers cannot reach protected objects", "1"],
        ["3.3 Alice read Bob (BOLA)", "v5.0.0-8.2.2", "Data-specific access restricted to consumers with explicit permission (IDOR/BOLA)", "1"],
        ["Enforcement server-side", "v5.0.0-8.3.1", "Authorization at trusted service layer, not client-controlled", "1"],
        ["POST/DELETE → 404", "v5.0.0-4.1.4", "Only explicitly supported HTTP methods allowed", "3"],
        ["Tampered token → 401", "v5.0.0-9.1.1", "Self-contained tokens validated by signature before trust", "1"],
        ["aud / token_use checked", "v5.0.0-9.2.2 / 9.2.3", "Accept only correct token type and own audience", "2"],
        ["Full item returned (Part D)", "v5.0.0-8.2.3", "Responses expose only authorized fields (field-level)", "2"],
        ["HSTS / nosniff / CSP", "v5.0.0-3.4.1 / 3.4.4 / 3.4.3", "Browser-facing security headers on API responses", "1"],
    ],
    [1.55 * inch, 1.25 * inch, 3.35 * inch, 0.35 * inch],
))

# --- Part C ---
story.append(P("5. Part C — Fix BOLA and Add Security Headers", "H1"))
story.append(P(
    "One-line ownership check: if <font face='Courier'>item.get(\"owner\") != caller</font> return 403. "
    "Alice still reads 1001 (200); Bob's 1002 is denied (403). Diff vs vulnerable app:",
))
story.append(P("Code diff — BOLA fix (ASVS v5.0.0-8.2.2)", "EvLabel"))
story.append(code_block(diff_bola))
story.append(P("Evidence #5 — Post-fix retest", "EvLabel"))
story.append(code_block(fixed))

story.append(P(
    "Then added ASVS V3 headers on every response: Strict-Transport-Security (3.4.1), "
    "X-Content-Type-Options: nosniff (3.4.4), Content-Security-Policy (3.4.3/3.4.6), Cache-Control: no-store.",
))
story.append(P("Evidence #6 — Response headers (curl -sI)", "EvLabel"))
story.append(code_block(headers))

story.append(P("Critical Thinking #2 — ASVS levels vs severity", "H2"))
story.append(P(
    "ASVS Level 1/2/3 is an <b>assurance target</b> for how comprehensively an application should be "
    "verified, not a ranking of how bad a failed control is. HSTS (3.4.1) and object-level authz "
    "(8.2.2) can both appear at L1 because both are baseline expectations for many apps, yet their "
    "business impact differs wildly. Organizations choose L1/L2/L3 from data sensitivity, threat "
    "model, and regulatory posture. Meridian handles PHI under HIPAA: a mobile billing API that can "
    "exfiltrate another patient's account is a reportable privacy incident. Meridian should target "
    "at least L2 for any PHI-touching API (and L3 for high-assurance clinical systems), treat 8.2.2 "
    "and 8.2.3 as release blockers, and still ship L1 browser headers because the same origin feeds "
    "a web portal — without pretending headers equal object authz in risk.",
))

# --- SR table ---
story.append(P("6. Security Requirements Table", "H1"))
story.append(make_table(
    ["ID", "Security requirement (testable)", "ASVS", "Verification"],
    [
        [
            "SR-1",
            "Every endpoint returning a user-owned object MUST verify the authenticated caller owns that object before returning it.",
            "v5.0.0-8.2.2",
            "Automated test: user A requests user B's object → expect 403; owner request → 200.",
        ],
        [
            "SR-2",
            "All API responses rendered by a browser MUST include HSTS, nosniff, and a restrictive CSP.",
            "v5.0.0-3.4.1 / 3.4.4 / 3.4.3",
            "curl -I (or -sD) asserts the three headers on every 2xx from the API origin.",
        ],
        [
            "SR-3",
            "Account-read routes MUST accept only explicitly configured HTTP methods (GET; HEAD only if required for header probes). POST, PUT, PATCH, DELETE MUST not be auto-mapped.",
            "v5.0.0-4.1.4",
            "Probe with POST/DELETE (and others) using a valid token; expect 404/405, never a successful write path.",
        ],
        [
            "SR-4",
            "API Gateway MUST reject JWTs with invalid signatures, wrong aud, wrong iss, or wrong token_use before Lambda executes.",
            "v5.0.0-9.1.1 / 9.2.2 / 9.2.3",
            "Send corrupted signature and alternate token types; expect 401. Decode valid claims and assert aud/iss/token_use.",
        ],
    ],
    [0.45 * inch, 2.85 * inch, 1.15 * inch, 2.25 * inch],
))

# --- Teardown ---
story.append(P("7. Tear Down", "H1"))
story.append(P(
    "Deleted API Gateway API, Lambda, DynamoDB table, Cognito user pool, IAM inline policy and role. "
    "Confirmation queries for prefix <font face='Courier'>ia642-lab</font> returned empty lists.",
))
story.append(P("Evidence #7 — Empty confirmation", "EvLabel"))
story.append(code_block(teardown))

# --- Part D ---
story.append(P("8. Part D — Graded Challenge (Excessive Data Exposure)", "H1"))
story.append(P(
    "<b>1. Vulnerability class.</b> Returning the whole DynamoDB item is OWASP API Top 10 (2023) "
    "<b>API3:2023 Broken Object Property Level Authorization</b> (excessive data exposure). "
    "Corresponding ASVS field-level requirement: <b>v5.0.0-8.2.3</b> — the service must return only "
    "properties the consumer is authorized to see.",
))
story.append(P(
    "<b>2. Exploit.</b> After the BOLA fix (ownership correct), sensitive attributes were added to "
    "account 1001 via <font face='Courier'>update-item</font> "
    "(<font face='Courier'>internal_note=VIP-PHI-REVIEW</font>, "
    "<font face='Courier'>fraud_score=0.91</font>). Alice's authorized GET still leaked them because "
    "the handler serialized <font face='Courier'>item</font> wholesale:",
))
story.append(P("Part D exploit output (authorized owner, still leaking fields)", "EvLabel"))
story.append(code_block(leak))

story.append(P(
    "<b>3. Allow-list fix.</b> Response built from "
    "<font face='Courier'>ALLOWED_FIELDS = (\"account_id\", \"balance\", \"card_last4\")</font> "
    "only. After redeploy, internal_note and fraud_score disappear. An allow-list is safer than a "
    "deny-list because new sensitive columns added later are excluded by default; a blocklist must "
    "be updated every time schema grows and will miss fields nobody remembered to ban.",
))
story.append(P("Part D fixed output (allow-list)", "EvLabel"))
story.append(code_block(allow))
story.append(P("Code diff — allow-list + security headers", "EvLabel"))
story.append(code_block(diff_d))

story.append(P(
    "<b>4. Least privilege.</b> Section 2.2 granted the Lambda role broad "
    "<font face='Courier'>dynamodb:GetItem/PutItem/Query/UpdateItem</font> on "
    "<font face='Courier'>Resource \"*\"</font>. Change to: (a) only "
    "<font face='Courier'>dynamodb:GetItem</font> if the function is read-only; (b) "
    "<font face='Courier'>Resource</font> set to the specific table ARN "
    "<font face='Courier'>arn:aws:dynamodb:us-east-1:626672433625:table/ia642-lab-accounts</font> "
    "(and index ARNs if needed); (c) deny or omit PutItem/UpdateItem/Scan for a read API. "
    "That control belongs to ASVS <b>V1 Encoding and Sanitization / architecture of trust boundaries</b> "
    "and especially <b>V15 Secure Coding and Architecture</b> least-privilege and secure configuration "
    "of cloud IAM — not to browser headers.",
))

story.append(P("9. Final Code Artifact", "H1"))
story.append(P("Hardened handler shipped as Evidence <font face='Courier'>fixed_app_final.py</font>:", "Body"))
story.append(code_block(read("fixed_app_final.py")))

story.append(P(
    "<b>Conclusion.</b> Authentication alone did not protect Meridian's accounts. Object-level "
    "authorization (8.2.2) stopped cross-patient reads; field allow-listing (8.2.3 / API3) stopped "
    "schema leakage; method restriction, JWT validation, and security headers completed the ASVS "
    "map. Written SRs turn these fixes into backlog-ready acceptance tests. Stack torn down same day "
    "— Free Tier cost remains $0.",
))

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=letter,
    leftMargin=0.7 * inch,
    rightMargin=0.7 * inch,
    topMargin=0.55 * inch,
    bottomMargin=0.65 * inch,
)
doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)

# copy to submit pack + evidence zip listing
import shutil
shutil.copy2(OUT, OUT2)
ev_dir = SUBMIT / "evidence"
if ev_dir.exists():
    shutil.rmtree(ev_dir)
shutil.copytree(EV, ev_dir)
code_dir = SUBMIT / "code"
if code_dir.exists():
    shutil.rmtree(code_dir)
shutil.copytree(ROOT / "code", code_dir)
print(f"Wrote {OUT}")
print(f"Submit pack: {SUBMIT}")
print(f"Pages built OK size={OUT.stat().st_size}")
