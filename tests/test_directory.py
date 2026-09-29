import csv

import pytest

from finlit_index.directory import parse_directory, representative_sample, write_csv, write_report


PAGE = """
<main>
  <h3 class="usa-accordion__heading"><button>
    <span class="occgov-accordion__button--text">Budgeting</span>
    <span class="icon-text">Show</span>
  </button></h3>
  <div class="usa-accordion__content">
    <p><a href="/guide#overview">Budget guide</a> helps readers plan.</p>
    <p><a href="/guide#overview">Budget guide</a> duplicate listing.</p>
    <p><a href="mailto:hello@example.org">Email us</a></p>
  </div>
  <h3 class="usa-accordion__heading"><button>
    <span class="occgov-accordion__button--text">Saving</span>
  </button></h3>
  <div class="usa-accordion__content">
    <p><a href="https://example.org/save">Beginner’s saving basics</a> for beginners.</p>
  </div>
</main>
"""


def test_parser_resolves_urls_and_deduplicates_within_category():
    resources = parse_directory(PAGE)
    assert len(resources) == 2
    assert resources[0].category == "Budgeting"
    assert resources[0].url == "https://www.occ.gov/guide"
    assert resources[0].source_domain == "www.occ.gov"
    assert resources[1].url == "https://example.org/save"
    assert resources[1].resource_name == "Beginner’s saving basics"
    assert resources[1].source_excerpt.endswith("for beginners.")


def test_parser_rejects_changed_layout():
    with pytest.raises(ValueError, match="No directory sections"):
        parse_directory("<main><p>No accordions here</p></main>")


def test_public_sample_omits_excerpt_and_report_escapes_html(tmp_path):
    resources = parse_directory(PAGE.replace("Budget guide", "&lt;script&gt;"))
    sample_path = tmp_path / "sample.csv"
    report_path = tmp_path / "report.html"
    write_csv(resources, sample_path, sample=True)
    write_report(resources, report_path)
    with sample_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert "source_excerpt" not in rows[0]
    report = report_path.read_text(encoding="utf-8")
    assert "&lt;script&gt;" in report
    assert "<script>" not in report
    assert [r.category for r in representative_sample(resources, 2)] == ["Budgeting", "Saving"]
