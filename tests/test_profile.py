"""Tests for the cv.tex profile parser (runs against the real resume)."""
import json
from pathlib import Path

import pytest

from apply_jobs_mcp.profile import load_profile

TEX = Path("/home/adarsh_gupta/Documents/resumes/resume_tex/cv.tex")
pytestmark = pytest.mark.skipif(not TEX.exists(), reason="resume tex not present")


def test_name_and_contact():
    p = load_profile(TEX)
    assert p.name == "Adarsh Gupta"
    assert "adarshguptatiger2006@gmail.com" in p.contact.emails
    assert any(ph.startswith("+91") for ph in p.contact.phones)
    labels = [l["label"] for l in p.contact.links]
    assert any("linkedin.com" in label for label in labels)
    assert any("github.com/AdarshGuptaa" in label for label in labels)
    assert any("leetcode.com" in label for label in labels)


def test_education():
    p = load_profile(TEX)
    assert len(p.education) == 1
    e = p.education[0]
    assert e.institution == "Atal Bihari Vajpayee IIITM Gwalior"
    assert e.dates == "August 2024 -- May 2028"
    assert e.cgpa == 8.20
    assert "Data Structures" in e.coursework
    assert "Computer Networks" in e.coursework


def test_skills_groups():
    p = load_profile(TEX)
    assert set(p.skills) == {
        "Languages",
        "Frameworks & Tools",
        "Cloud & DevOps",
        "Systems & Hardware",
    }
    assert "Rust" in p.skills["Languages"]
    assert "eBPF" in p.skills["Systems & Hardware"]
    assert "Spring Boot" in p.skills["Frameworks & Tools"]


def test_open_source_prs():
    p = load_profile(TEX)
    assert p.open_source[0].organization == "kornia-rs"
    urls = [e.link["url"] for e in p.open_source[0].entries if e.link]
    assert any(url.endswith("pull/934") for url in urls)
    assert any(url.endswith("pull/687") for url in urls)


def test_projects():
    p = load_profile(TEX)
    names = {pr.name for pr in p.projects}
    assert names == {"Password Mine", "PlasmaWall", "Smart Windshield"}
    pw = next(pr for pr in p.projects if pr.name == "PlasmaWall")
    assert pw.link and pw.link["url"].endswith("plasmawall")
    assert pw.tech.startswith("Rust")


def test_metrics():
    p = load_profile(TEX)
    joined = " ".join(p.metrics)
    assert "7×" in joined
    assert "6×" in joined
    assert "300+" in joined
    assert "800ms" in joined


def test_profile_roundtrip_json():
    p = load_profile(TEX)
    d = p.to_dict()
    json.dumps(d, indent=2)
    assert d["name"] == "Adarsh Gupta"
