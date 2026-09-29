"""Extract public resource links from the OCC financial literacy directory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import csv
import logging

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DIRECTORY_URL = (
    "https://www.occ.gov/topics/consumers-and-communities/community-affairs/"
    "resource-directories/financial-literacy/index-financial-literacy-resource-directory.html"
)
ROBOTS_URL = "https://www.occ.gov/robots.txt"
USER_AGENT = "FinancialResourceIndexPortfolio/1.0 (+public educational directory)"
FIELDS = ("category", "resource_name", "url", "source_domain", "source_excerpt")
SAMPLE_FIELDS = FIELDS[:-1]
LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Resource:
    category: str
    resource_name: str
    url: str
    source_domain: str
    source_excerpt: str


def parse_directory(page_html: str, base_url: str = DIRECTORY_URL) -> list[Resource]:
    """Parse accordion sections without following or downloading linked resources."""
    soup = BeautifulSoup(page_html, "html.parser")
    headers = soup.select("h3.usa-accordion__heading")
    if not headers:
        raise ValueError("No directory sections found; the page layout may have changed")

    resources: list[Resource] = []
    seen: set[tuple[str, str, str]] = set()
    for header in headers:
        title = header.select_one("button .occgov-accordion__button--text")
        content = header.find_next_sibling("div", class_="usa-accordion__content")
        if title is None or content is None:
            raise ValueError("A directory section is missing its title or content")
        category = title.get_text(" ", strip=True)
        for paragraph in content.find_all("p"):
            anchor = paragraph.find("a", href=True)
            if anchor is None:
                continue
            url, _fragment = urldefrag(urljoin(base_url, anchor["href"].strip()))
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            name = anchor.get_text(" ", strip=True)
            if not name:
                continue
            key = (category.casefold(), name.casefold(), url)
            if key in seen:
                continue
            seen.add(key)
            resources.append(
                Resource(
                    category=category,
                    resource_name=name,
                    url=url,
                    source_domain=parsed.hostname or "",
                    source_excerpt=paragraph.get_text(" ", strip=True),
                )
            )
    if not resources:
        raise ValueError("No resources found; the directory layout may have changed")
    return resources


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_directory(timeout: float = 20) -> str:
    """Check robots.txt, then retrieve the one public directory page."""
    with _session() as session:
        robots_response = session.get(ROBOTS_URL, timeout=timeout)
        robots_response.raise_for_status()
        robots = RobotFileParser()
        robots.parse(robots_response.text.splitlines())
        if not robots.can_fetch(USER_AGENT, DIRECTORY_URL):
            raise PermissionError("The directory is disallowed by robots.txt")
        response = session.get(DIRECTORY_URL, timeout=timeout)
        response.raise_for_status()
        # OCC omits a charset in its Content-Type header; Requests otherwise
        # assumes ISO-8859-1 and corrupts punctuation in resource names.
        response.encoding = response.apparent_encoding or "utf-8"
        LOG.info("Fetched %s", response.url)
        return response.text


def write_csv(resources: list[Resource], path: Path, *, sample: bool = False) -> None:
    """Write the complete local index or a metadata-only public sample."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = SAMPLE_FIELDS if sample else FIELDS
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for resource in resources:
            data = asdict(resource)
            writer.writerow({field: data[field] for field in fields})


def representative_sample(resources: list[Resource], count: int) -> list[Resource]:
    """Pick distinct categories first so a short sample shows the directory's breadth."""
    chosen: list[Resource] = []
    used_categories: set[str] = set()
    used_resources: set[Resource] = set()
    for resource in resources:
        if resource.category not in used_categories:
            chosen.append(resource)
            used_resources.add(resource)
            used_categories.add(resource.category)
            if len(chosen) >= count:
                return chosen
    for resource in resources:
        if resource not in used_resources:
            chosen.append(resource)
            if len(chosen) >= count:
                break
    return chosen


def write_report(resources: list[Resource], path: Path) -> None:
    """Make a local report showing the indexing result and a few sample links."""
    path.parent.mkdir(parents=True, exist_ok=True)
    categories = len({resource.category for resource in resources})
    domains = len({resource.source_domain for resource in resources})
    urls = len({resource.url for resource in resources})
    rows = "\n".join(
        "<tr>"
        f"<td>{escape(resource.category)}</td>"
        f"<td>{escape(resource.resource_name)}</td>"
        f"<td>{escape(resource.source_domain)}</td>"
        f"<td><a href='{escape(resource.url, quote=True)}'>Source ↗</a></td>"
        "</tr>"
        for resource in representative_sample(resources, 12)
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Financial education resource index</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf3f8;color:#1b3548;font:16px/1.45 Arial,sans-serif}}
main{{max-width:1180px;margin:52px auto;padding:0 24px}}.eyebrow{{color:#247d91;font-size:12px;font-weight:700;letter-spacing:.15em;text-transform:uppercase}}
h1{{font-size:42px;letter-spacing:-.04em;margin:10px 0}}.intro{{color:#607889;margin:0 0 28px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}}
.card,.table{{background:#fff;border:1px solid #dce5ec;border-radius:14px;box-shadow:0 8px 25px #20384e0a}}.card{{padding:22px}}.label{{font-size:12px;color:#688092;text-transform:uppercase;letter-spacing:.07em;font-weight:700}}.number{{font-size:34px;font-weight:800;margin-top:8px}}
.table{{overflow:hidden}}h2{{font-size:20px;padding:24px;margin:0}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:16px 18px;border-top:1px solid #e6edf2;font-size:14px}}th{{background:#f6f9fb;color:#637b8c;text-transform:uppercase;font-size:12px;letter-spacing:.05em}}
tr:nth-child(even) td{{background:#fbfdfe}}a{{color:#247d91;text-decoration:none;font-weight:700}}footer{{color:#6c8493;font-size:12px;margin-top:18px}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}.table{{overflow:auto}}table{{min-width:800px}}}}
</style></head><body><main><div class="eyebrow">Independent portfolio project</div>
<h1>Financial education resource index</h1><p class="intro">Public directory → Python extraction → structured, source-linked data</p>
<div class="cards"><div class="card"><div class="label">Directory entries</div><div class="number">{len(resources)}</div></div>
<div class="card"><div class="label">Categories</div><div class="number">{categories}</div></div>
<div class="card"><div class="label">Unique URLs</div><div class="number">{urls}</div></div>
<div class="card"><div class="label">Source domains</div><div class="number">{domains}</div></div></div>
<section class="table"><h2>Sample records</h2><table><thead><tr><th>Category</th><th>Resource</th><th>Domain</th><th>Link</th></tr></thead><tbody>{rows}</tbody></table></section>
<footer>Independent index of publicly listed resources. External links are included for reference; no source organization endorses this project.</footer>
</main></body></html>"""
    path.write_text(document, encoding="utf-8")
