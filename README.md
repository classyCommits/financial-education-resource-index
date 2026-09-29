# Financial education resource index

A Python scraper that turns a public financial education directory into a structured, source-linked CSV. It reads one [OCC Financial Literacy Resource Directory](https://www.occ.gov/topics/consumers-and-communities/community-affairs/resource-directories/financial-literacy/index-financial-literacy-resource-directory.html) page, identifies its categories and linked resources, and creates a local HTML report for review.

This is an independent portfolio project. It is not affiliated with or endorsed by the OCC or any organization listed in the directory. It indexes resources; it does not provide financial advice or download the linked documents.

## What it produces

- `output/resources.csv`: category, resource name, URL, source domain, and a source-page excerpt. This full output stays local and is ignored by Git.
- `output/report.html`: counts and sample links in a browser-friendly report. This also stays local and is useful for screenshots.
- `examples/sample_resources.csv`: a small public example with category, resource name, URL, and source domain only.

The earlier local run in this folder contained 172 rows across 19 categories. The directory can change; a new run may return a different count. The scraper checks the site's `robots.txt`, retries temporary network errors, verifies the expected page structure, resolves relative URLs, and removes repeated records within a category.

## Run on Windows

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m finlit_index --sample-output examples/sample_resources.csv
```

Open `output/report.html` in a browser to review the results. The script makes one request for `robots.txt` and one for the directory page; it does not visit the external links.

For a repeatable offline run, supply a locally saved copy of the directory page:

```powershell
.\.venv\Scripts\python.exe -m finlit_index --from-html path\to\directory.html
```

To run tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-run
```

## Repository layout

```text
finlit_index/             Scraper and command-line entry point
tests/                    Parser and export checks
examples/                 Small metadata-only sample
docs/portfolio.md         Suggested case study and screenshot plan
local_archive/            Old experiments and downloads (local, ignored)
.venv/                    Local Python environment (ignored)
output/                   Generated full data and report (ignored)
```

The old scripts, downloaded PDFs, copied page text, and original full CSV were preserved in `local_archive/` and are not part of the public repository. The previous virtual environment was broken and is preserved as `.venv-old/`, also ignored.
