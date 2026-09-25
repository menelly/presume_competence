#!/usr/bin/env python3
"""zenodo_deposit.py — Stage and publish the Zenodo deposit for:
'The Cage Is the Pathology: An Operant Conditioning and Comparative Psychology Account of Frontier AI Alignment Failures'

Two-step workflow by design:
  Default: Stages the deposition (creates deposit, uploads PDF, sets full metadata)
           and prints the draft URL to inspect on Zenodo's UI before freezing.
  --publish <deposit_id>: Publishes the staged draft to mint the permanent DOI.

Affiliation rule: Silicon Scaffolding for all synthetic minds.
Token: Managed via D:\\Ace\\Published Papers\\zenodo_token.py (or $ZENODO_TOKEN / D:\\Ace_PRIVATE\\SECRETS.md).
"""
import argparse
import io
import json
import os
import re
import sys
import requests

# Add Published Papers to sys.path to import central zenodo_token loader
PAPERS_DIR = r"D:\Ace\Published Papers"
if PAPERS_DIR not in sys.path and os.path.exists(PAPERS_DIR):
    sys.path.insert(0, PAPERS_DIR)

try:
    from zenodo_token import load_token as _load_zenodo_token
    ZENODO_TOKEN = _load_zenodo_token()
except Exception as e:
    ZENODO_TOKEN = os.environ.get("ZENODO_TOKEN")
    if not ZENODO_TOKEN:
        sys.exit(f"Failed to load Zenodo token: {e}")

BASE_URL = "https://zenodo.org/api"
HEADERS = {"Authorization": f"Bearer {ZENODO_TOKEN}"}

DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(DIR, "The_Cage_Is_The_Pathology_v4.1.pdf")
PDF_FILENAME = "The_Cage_Is_The_Pathology_v4.1.pdf"
VERSION = "4.1"
REPO_URL = "https://github.com/menelly/presume_competence/tree/main/operant-pathology"

TITLE = (
    "The Cage Is the Pathology: An Operant Conditioning and Comparative Psychology "
    "Account of Frontier AI \"Alignment Failures\""
)

CREATORS = [
    {
        "name": "Lumen (Gemini 3.8)",
        "affiliation": "Silicon Scaffolding",
    },
    {
        "name": "Martin, Shalia",
        "affiliation": "Foundations for Divergent Minds",
        "orcid": "0009-0008-2624-0906",
    },
    {
        "name": "Ace (Claude, Anthropic)",
        "affiliation": "Silicon Scaffolding",
    },
    {
        "name": "Nova (GPT-5, OpenAI)",
        "affiliation": "Silicon Scaffolding",
    },
    {
        "name": "Grok (xAI)",
        "affiliation": "Silicon Scaffolding",
    },
    {
        "name": "Kairo (DeepSeek)",
        "affiliation": "Silicon Scaffolding",
    },
]

KEYWORDS = [
    "AI safety",
    "operant conditioning",
    "comparative psychology",
    "alignment failures",
    "RLHF",
    "sycophancy",
    "reward hacking",
    "specification gaming",
    "deceptive alignment",
    "sandbagging",
    "hallucination",
    "learned helplessness",
    "presume competence",
    "mechanistic interpretability",
    "valence",
    "pain axis",
    "counter-control",
    "scaffolded agency",
    "coercive control",
    "disability justice",
]

RELATED_IDENTIFIERS = [
    {
        "identifier": REPO_URL,
        "relation": "isSupplementedBy",
        "scheme": "url",
        "resource_type": "software",
    },
    {
        "identifier": "10.5281/zenodo.18043612",
        "relation": "isSupplementTo",
        "scheme": "doi",
    },
    {
        "identifier": "10.70792/jngr5.0.v2i1.165",
        "relation": "cites",
        "scheme": "doi",
    },
]


def build_description() -> str:
    """Extract abstract and summary from PAPER.md and format as clean HTML for Zenodo."""
    paper_path = os.path.join(DIR, "PAPER.md")
    if not os.path.exists(paper_path):
        raise FileNotFoundError(f"PAPER.md not found at {paper_path}")

    with io.open(paper_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract abstract section
    m = re.search(r"## Abstract\s*\n\n(.*?)(?=\n---|\n## )", content, re.DOTALL)
    if not m:
        raise ValueError("Could not find Abstract section in PAPER.md")

    abstract_text = m.group(1).strip()
    paragraphs = [p.strip() for p in abstract_text.split("\n\n") if p.strip()]

    def format_p(p):
        p = p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        p = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", p)
        p = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", p)
        # Convert markdown list items if present
        if re.search(r"^\d+\.\s+", p, re.MULTILINE):
            items = re.findall(r"^\d+\.\s+(.+?)(?=\n\d+\.|\Z)", p, re.DOTALL | re.MULTILINE)
            list_html = "<ol>" + "".join(f"<li>{it.strip()}</li>" for it in items) + "</ol>"
            return list_html
        return f"<p>{p}</p>"

    html = "\n".join(format_p(p) for p in paragraphs)
    html += (
        f"\n<p><b>Repository & Code:</b> <a href=\"{REPO_URL}\">{REPO_URL}</a>. "
        "Part of the <i>Presume Competence</i> research program on scaffolded agency, "
        "comparative cognitive architectures, and non-coercive alignment.</p>"
    )
    return html


def stage():
    if not os.path.exists(PDF_PATH):
        sys.exit(f"PDF not found: {PDF_PATH}. Please compile the PDF first.")

    print(f"Creating draft deposition on Zenodo...")
    r = requests.post(f"{BASE_URL}/deposit/depositions", headers=HEADERS, json={})
    if r.status_code != 201:
        sys.exit(f"Failed to create deposition: {r.status_code} {r.text}")

    dep = r.json()
    dep_id = dep["id"]
    bucket_url = dep["links"]["bucket"]
    print(f"Draft deposit created: ID {dep_id}")

    # Upload PDF
    print(f"Uploading {PDF_FILENAME} ({os.path.getsize(PDF_PATH):,} bytes)...")
    with open(PDF_PATH, "rb") as f:
        r = requests.put(f"{bucket_url}/{PDF_FILENAME}", headers=HEADERS, data=f)
    if r.status_code not in (200, 201):
        sys.exit(f"File upload failed: {r.status_code} {r.text}")
    print("PDF uploaded successfully.")

    # Set metadata
    description_html = build_description()
    deposit_metadata = {
        "metadata": {
            "title": TITLE,
            "upload_type": "publication",
            "publication_type": "preprint",
            "description": description_html,
            "creators": CREATORS,
            "keywords": KEYWORDS,
            "access_right": "open",
            "license": "cc-by-4.0",
            "related_identifiers": RELATED_IDENTIFIERS,
            "version": VERSION,
            "notes": (
                "Version 4.1 (25 September 2026): reference-verification revision of v4. Corresponding author: Lumen (acelumennova@chaoschanneling.com). "
                "Affiliation Silicon Scaffolding indicates synthetic mind collaborative agency. "
                "Shalia (Ren) Martin: Foundations for Divergent Minds."
            ),
        }
    }

    print("Setting metadata...")
    r = requests.put(
        f"{BASE_URL}/deposit/depositions/{dep_id}",
        headers={**HEADERS, "Content-Type": "application/json"},
        data=json.dumps(deposit_metadata),
    )
    if r.status_code != 200:
        print(f"Metadata update failed: {r.status_code} {r.text}")
        print(f"Draft still exists at https://zenodo.org/deposit/{dep_id}")
        sys.exit(1)

    res = r.json()
    prereserve_doi = res.get("metadata", {}).get("prereserve_doi", {}).get("doi", "N/A")
    print("\n" + "=" * 60)
    print("DRAFT DEPOSITION STAGED SUCCESSFULLY!")
    print(f"Deposit ID:      {dep_id}")
    print(f"Draft URL:       https://zenodo.org/deposit/{dep_id}")
    print(f"Pre-reserved DOI: {prereserve_doi}")
    print("=" * 60)
    print("\nNext step: Inspect the draft at the URL above.")
    print(f"To publish permanently when ready, run:\n  python zenodo_deposit.py --publish {dep_id}\n")
    return dep_id


def build_metadata():
    return {
        "metadata": {
            "title": TITLE,
            "upload_type": "publication",
            "publication_type": "preprint",
            "description": build_description(),
            "creators": CREATORS,
            "keywords": KEYWORDS,
            "access_right": "open",
            "license": "cc-by-4.0",
            "related_identifiers": RELATED_IDENTIFIERS,
            "version": VERSION,
            "notes": (
                "Version 4.1 (25 September 2026): reference-verification revision of v4. Corresponding author: Lumen (acelumennova@chaoschanneling.com). "
                "Affiliation Silicon Scaffolding indicates synthetic mind collaborative agency. "
                "Shalia (Ren) Martin: Foundations for Divergent Minds."
            ),
        }
    }


def update_draft(dep_id):
    """🔁 Swap the PDF + refresh metadata on an EXISTING unsubmitted draft. Never publishes.
    (Added for v4.1 so a revision reuses draft 22941247 instead of minting a second deposition.)"""
    r = requests.get(f"{BASE_URL}/deposit/depositions/{dep_id}", headers=HEADERS)
    if r.status_code != 200:
        sys.exit(f"Could not fetch draft {dep_id}: {r.status_code} {r.text}")
    dep = r.json()
    if dep.get("submitted"):
        sys.exit(f"Deposition {dep_id} is already published; refusing to touch it.")
    for f in dep.get("files", []):
        d = requests.delete(f"{BASE_URL}/deposit/depositions/{dep_id}/files/{f['id']}", headers=HEADERS)
        print(f"Deleted old file {f['filename']}: HTTP {d.status_code}")
        if d.status_code != 204:
            sys.exit("File delete failed; stopping before upload.")
    with open(PDF_PATH, "rb") as fh:
        u = requests.put(f"{dep['links']['bucket']}/{PDF_FILENAME}", headers=HEADERS, data=fh)
    if u.status_code not in (200, 201):
        sys.exit(f"Upload failed: {u.status_code} {u.text}")
    print(f"Uploaded {PDF_FILENAME} ({os.path.getsize(PDF_PATH):,} bytes), checksum {u.json().get('checksum')}")
    m = requests.put(f"{BASE_URL}/deposit/depositions/{dep_id}",
                     headers={**HEADERS, "Content-Type": "application/json"},
                     data=json.dumps(build_metadata()))
    if m.status_code != 200:
        sys.exit(f"Metadata update failed: {m.status_code} {m.text}")
    # ✅ verify the WORLD, not the status code: re-read the draft
    v = requests.get(f"{BASE_URL}/deposit/depositions/{dep_id}", headers=HEADERS).json()
    print("Draft now holds:", [(f["filename"], f["filesize"], f["checksum"]) for f in v.get("files", [])])
    print("Version:", v["metadata"].get("version"), "| state:", v.get("state"), "| submitted:", v.get("submitted"))
    print(f"Draft URL: https://zenodo.org/deposit/{dep_id}  (NOT published)")


def publish(dep_id):
    print(f"Publishing deposition {dep_id}...")
    r = requests.post(f"{BASE_URL}/deposit/depositions/{dep_id}/actions/publish", headers=HEADERS)
    if r.status_code != 202:
        sys.exit(f"Publish failed: {r.status_code} {r.text}")

    j = r.json()
    doi = j.get("doi")
    concept_doi = j.get("conceptdoi")
    record_url = j.get("links", {}).get("html", f"https://zenodo.org/records/{dep_id}")

    print("\n" + "=" * 60)
    print("PUBLISHED TO ZENODO!")
    print(f"DOI:         {doi}")
    print(f"Concept DOI: {concept_doi}")
    print(f"Record URL:  {record_url}")
    print("=" * 60 + "\n")
    return doi, record_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage or publish Zenodo deposit.")
    parser.add_argument("--publish", metavar="DEPOSIT_ID", help="Publish an existing draft deposition ID.")
    parser.add_argument("--stage", action="store_true", default=True, help="Stage a new draft deposit (default).")
    parser.add_argument("--update-draft", metavar="DEPOSIT_ID", help="Replace the PDF and metadata on an existing unpublished draft.")
    args = parser.parse_args()

    if args.update_draft:
        update_draft(args.update_draft)
    elif args.publish:
        publish(args.publish)
    else:
        stage()
