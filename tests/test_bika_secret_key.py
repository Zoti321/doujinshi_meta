"""Regression: HMAC secret must match active open-source clients.

A trailing backtick was once appended by mistake (markdown fence bleed).
Wrong key → login returns code=200 without data/token, misread as bad password.
Canonical sources: hiczp PicaComicInherent.kt, pica-cli, niuhuan/pica-go.
"""

from __future__ import annotations

from doujinshi_meta.sources.bika import SECRET_KEY

# Ends with /*Cn — no trailing backtick. Length 63.
CANONICAL_SECRET_KEY = (
    r"~d}$Q7$eIni=V)9\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"
)


def test_secret_key_matches_canonical_clients() -> None:
    assert SECRET_KEY == CANONICAL_SECRET_KEY
    assert len(SECRET_KEY) == 63
    assert not SECRET_KEY.endswith("`")
