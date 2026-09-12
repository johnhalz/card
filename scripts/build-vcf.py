#!/usr/bin/env python3
"""Build contact.vcf from contact.json.

vCard 3.0, not 4.0: 3.0 is what iOS Contacts and Android parse without
surprises. Run from the repo root: python3 scripts/build-vcf.py
"""

import base64
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "contact.vcf"


def esc(value):
    """Escape backslash, semicolon and comma per RFC 2426 section 2.4.2."""
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")


def fold(line, limit=75):
    """Fold a long line at `limit` octets, continuations prefixed with a space.

    Most clients tolerate one long base64 line; folding is cheap insurance.
    """
    out = [line[:limit]]
    rest = line[limit:]
    while rest:
        # ponytail: limit-1 because the leading space counts toward the octet budget
        out.append(" " + rest[: limit - 1])
        rest = rest[limit - 1 :]
    return out


def build(c):
    photo = base64.b64encode((ROOT / c["photo"]).read_bytes()).decode("ascii")

    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        # N is Family;Given;Additional;Prefix;Suffix
        f"N:{esc(c['last_name'])};{esc(c['first_name'])};;;",
        f"FN:{esc(c['first_name'])} {esc(c['last_name'])}",
        f"ORG:{esc(c['org'])}",
        f"TITLE:{esc(c['title'])}",
        f"EMAIL;TYPE=INTERNET,WORK:{c['email']}",
        f"URL:{c['url']}",
        *fold(f"PHOTO;ENCODING=b;TYPE=JPEG:{photo}"),
        f"REV:{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "END:VCARD",
    ]
    return "\r\n".join(lines) + "\r\n"


def check(raw, c):
    """The things that actually break vCards, asserted on every build."""
    text = raw.decode("utf-8")
    assert b"\r\n" in raw, "no CRLF line endings"
    assert not raw.replace(b"\r\n", b"").count(b"\n"), "bare LF present"
    assert text.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n"), "bad header"
    assert text.endswith("END:VCARD\r\n"), "bad trailer"
    for line in text.split("\r\n"):
        assert len(line.encode()) <= 75, f"line over 75 octets: {line[:40]}..."
    # compare against the escaped form — a value containing a comma is stored
    # escaped (e.g. "Engineer\, Loss Prevention"), not as the raw string
    for needle in (c["org"], c["title"]):
        assert esc(needle) in text, f"missing field: {needle}"
    assert "ADR" not in text, "address should not be in the vCard"
    assert "MSc" not in text, "post-nominal should not be in the vCard"
    assert c["email"] in text, "missing field: email"
    assert "PHOTO;ENCODING=b;TYPE=JPEG:" in text, "photo not embedded"


if __name__ == "__main__":
    contact = json.loads((ROOT / "contact.json").read_text())
    raw = build(contact).encode("utf-8")
    check(raw, contact)
    # newline="" so Python never rewrites the CRLFs we just built
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        f.write(raw.decode("utf-8"))
    print(f"wrote {OUT.name}: {len(raw) / 1024:.1f}KB, checks passed")
