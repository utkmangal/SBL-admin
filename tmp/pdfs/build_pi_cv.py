from pathlib import Path
import html
import re

import pdfplumber


ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "tmp" / "pdfs" / "Sung-Hwan_Choi_CV_2026.pdf"
OUTPUT_PATH = ROOT / "pi-cv.html"
TOKENS_PATH = ROOT / "tokens.css"


def clean_text(value: str) -> str:
    # The source PDF uses typographic dashes for ranges. Keep the page portable
    # and use ASCII hyphens throughout the generated HTML.
    value = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u00ad", "")
    return re.sub(r"\s+", " ", value.strip())


with pdfplumber.open(PDF_PATH) as pdf:
    raw = "\n".join(page.extract_text(x_tolerance=2, y_tolerance=3) or "" for page in pdf.pages)

lines = [clean_text(line) for line in raw.splitlines()]
lines = [line for line in lines if line]

section_names = [
    "Contact Information",
    "Education",
    "Positions and Employment",
    "Administrative Appointments",
    "Honors and Awards",
    "Research Grants and Support",
    "Peer-Reviewed Publications",
]

section_positions = {name: lines.index(name) for name in section_names}


def segment(name: str) -> list[str]:
    start = section_positions[name] + 1
    following = [position for position in section_positions.values() if position > section_positions[name]]
    end = min(following) if following else len(lines)
    return lines[start:end]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def format_text(value: str) -> str:
    value = esc(value)
    for label in ("Address:", "Phone:", "Email:", "Project Title:", "Funding Agency:", "Role:"):
        value = value.replace(label, f'<strong class="field-label">{label}</strong>')
    return value


def compact_entries(source: list[str], extra_starters: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            entries.append(("item", " ".join(current).strip()))
            current.clear()

    for line in source:
        is_bullet = line.startswith("•")
        is_number = bool(re.match(r"^\d+\.\s", line))
        is_year = bool(re.match(r"^(?:19|20)\d{2}(?:\s|-|$)", line))
        is_subhead = line.startswith(extra_starters)
        if is_bullet or is_number or is_year or is_subhead:
            flush()
            if is_subhead:
                entries.append(("subhead", line))
                continue
            current.append(line.lstrip("• ").strip())
        else:
            current.append(line)
    flush()
    return entries


def render_entries(source: list[str], extra_starters: tuple[str, ...] = ()) -> str:
    chunks: list[str] = []
    for kind, value in compact_entries(source, extra_starters):
        if kind == "subhead":
            chunks.append(f'<h3 class="subsection-title">{esc(value)}</h3>')
        else:
            chunks.append(f'<article class="record-item">{format_text(value)}</article>')
    return "\n".join(chunks)


def render_publications(source: list[str]) -> str:
    chunks: list[str] = []
    current: list[str] = []

    def flush_publication() -> None:
        if not current:
            return
        text = " ".join(current).strip()
        match = re.match(r"^(\d+)\.\s*(.*)$", text)
        if match:
            number, body = match.groups()
            chunks.append(
                f'<article class="publication"><span class="publication-number">{esc(number)}</span>'
                f'<p>{format_text(body)}</p></article>'
            )
        else:
            chunks.append(f'<p class="publication-note">{format_text(text)}</p>')
        current.clear()

    for line in source:
        if line.startswith("Selected "):
            flush_publication()
            chunks.append(f'<h3 class="subsection-title">{esc(line)}</h3>')
        elif not current and re.match(r"^(?:19|20)\d{2}(?:\s*-\s*(?:19|20)\d{2})?$", line):
            flush_publication()
            chunks.append(f'<h4 class="year-heading">{esc(line)}</h4>')
        elif re.match(r"^\d{1,3}\.\s", line):
            flush_publication()
            current.append(line)
        else:
            current.append(line)
    flush_publication()
    return "\n".join(chunks)


profile_lines = lines[1:section_positions["Contact Information"]]
contact_entries = compact_entries(segment("Contact Information"))
contact_html = "\n".join(
    f'<p class="contact-line">{format_text(value)}</p>' for kind, value in contact_entries if kind == "item"
)

education_html = render_entries(segment("Education"))
positions_html = render_entries(segment("Positions and Employment"))
admin_html = render_entries(segment("Administrative Appointments"))
honors_html = render_entries(segment("Honors and Awards"))
grants_html = render_entries(
    segment("Research Grants and Support"),
    ("As Principal Investigator (PI)", "As Co-Principal Investigator (Co-PI)"),
)
publications_html = render_publications(segment("Peer-Reviewed Publications"))

profile_bullets = [line.lstrip("• ").strip() for line in profile_lines[2:] if line.startswith("•")]
profile_html = "\n".join(f'<li>{esc(value)}</li>' for value in profile_bullets)
name = profile_lines[1]
metrics_html = '''
        <div class="metrics" aria-label="Google Scholar metrics">
          <div class="metric"><strong>4,619</strong><span>Total citations</span></div>
          <div class="metric"><strong>38</strong><span>h-index</span></div>
          <div class="metric"><strong>109</strong><span>i10-index</span></div>
          <p class="metrics-note"><a href="https://scholar.google.com/citations?user=sT5UBXwAAAAJ&amp;hl=en" target="_blank" rel="noopener">Google Scholar profile</a></p>
        </div>'''

tokens_css = '''/* Hallmark · macrostructure: Long Document · tone: editorial · anchor hue: cool blue · theme: Almanac · enrichment: none · nav: N3 · footer: Ft4 */
:root {
  color-scheme: light dark;
  --color-paper: oklch(97% 0.008 230);
  --color-paper-2: oklch(93% 0.012 230);
  --color-surface: oklch(99% 0.006 230);
  --color-rule: oklch(84% 0.012 230);
  --color-muted: oklch(46% 0.012 230);
  --color-ink: oklch(21% 0.012 230);
  --color-accent: oklch(40% 0.14 245);
  --color-focus: oklch(55% 0.15 245);
  --color-on-accent: oklch(97% 0.008 230);
  --font-display: "DM Serif Display", ui-serif, serif;
  --font-body: "Pretendard", "IBM Plex Sans", ui-sans-serif, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;
  --space-3xs: 0.125rem;
  --space-2xs: 0.25rem;
  --space-xs: 0.5rem;
  --space-sm: 0.75rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2.5rem;
  --space-2xl: 4rem;
  --space-3xl: 6rem;
  --radius-control: 0.5rem;
  --radius-panel: 1rem;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --dur-micro: 120ms;
  --dur-short: 220ms;
  --dur-long: 420ms;
  --z-sticky: 200;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-paper: oklch(15% 0.01 230);
    --color-paper-2: oklch(20% 0.012 230);
    --color-surface: oklch(18% 0.011 230);
    --color-rule: oklch(31% 0.012 230);
    --color-muted: oklch(73% 0.012 230);
    --color-ink: oklch(94% 0.008 230);
    --color-accent: oklch(75% 0.11 245);
    --color-focus: oklch(78% 0.12 245);
    --color-on-accent: oklch(15% 0.01 230);
  }
}
'''
TOKENS_PATH.write_text(tokens_css, encoding="utf-8")

html_document = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Curriculum vitae of Sung-Hwan Choi, D.D.S., Ph.D.">
  <title>Sung-Hwan Choi</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="tokens.css">
  <style>
    /* Hallmark · macrostructure: Long Document · tone: editorial · anchor hue: cool blue */
    :root {{
      --bg: var(--color-paper);
      --surface: var(--color-surface);
      --surface-soft: var(--color-paper-2);
      --ink: var(--color-ink);
      --muted: var(--color-muted);
      --line: var(--color-rule);
      --accent: var(--color-accent);
      --max: 1380px;
      --radius: var(--radius-panel);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; overflow-x: clip; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-body); line-height: 1.6; overflow-x: clip; }}
    a {{ color: var(--accent); }}
    a:focus-visible, button:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 3px; }}
    .skip-link {{ position: absolute; left: 1rem; top: -4rem; padding: .65rem .85rem; background: var(--accent); color: var(--color-on-accent); border-radius: var(--radius-control); z-index: var(--z-sticky); }}
    .skip-link:focus {{ top: 1rem; }}
    .page {{ width: min(calc(100% - 2rem), var(--max)); margin: 0 auto; padding: 2rem 0 4rem; }}
    .topbar {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: 1.25rem; }}
    .wordmark {{ color: var(--accent); font-family: var(--font-mono); font-size: .78rem; font-weight: 500; letter-spacing: .12em; text-transform: uppercase; }}
    .actions {{ display: flex; gap: .6rem; }}
    .action {{ border: 1px solid var(--line); border-radius: var(--radius-control); padding: .55rem .85rem; background: var(--surface); color: var(--ink); font: inherit; text-decoration: none; cursor: pointer; white-space: nowrap; transition: color var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out), transform var(--dur-micro) var(--ease-out); }}
    .action:hover {{ border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }}
    .action:active {{ transform: translateY(0); }}
    .hero {{ display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(260px, .75fr); gap: 1.5rem; padding: clamp(1.5rem, 4vw, 3.5rem); border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); }}
    .hero h1 {{ max-width: 13ch; min-width: 0; overflow-wrap: anywhere; margin: 0; font-family: var(--font-display); font-size: clamp(2.7rem, 7vw, 5.5rem); font-style: normal; line-height: .98; letter-spacing: -.045em; }}
    .hero h1 span {{ color: var(--accent); }}
    .hero-subtitle {{ margin: 1.25rem 0 0; color: var(--muted); font-size: clamp(1rem, 1.6vw, 1.2rem); max-width: 42rem; }}
    .hero-list {{ margin: 1.4rem 0 0; padding: 0; list-style: none; color: var(--muted); }}
    .hero-list li {{ margin-top: .5rem; padding-left: 1.2rem; position: relative; }}
    .hero-list li::before {{ content: ""; width: .42rem; height: .42rem; position: absolute; left: 0; top: .65rem; border-radius: 50%; background: var(--accent); }}
    .metrics {{ display: flex; flex-wrap: wrap; align-items: end; gap: 1.25rem; margin-top: 1.75rem; padding-top: 1.1rem; border-top: 1px solid var(--line); }}
    .metric {{ display: grid; gap: .15rem; min-width: 8rem; }}
    .metric strong {{ font-family: var(--font-display); font-size: clamp(1.9rem, 4vw, 2.65rem); font-weight: 400; line-height: 1; letter-spacing: -.03em; color: var(--ink); }}
    .metric span, .metrics-note {{ color: var(--muted); font-family: var(--font-mono); font-size: .72rem; letter-spacing: .02em; }}
    .metrics-note {{ flex-basis: 100%; margin: .1rem 0 0; }}
    .metrics-note a {{ color: var(--accent); }}
    .contact {{ align-self: end; padding: 1.25rem; border: 1px solid var(--line); background: var(--surface-soft); border-radius: var(--radius); }}
    .contact h2 {{ margin: 0 0 .8rem; font-family: var(--font-mono); font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
    .contact-line {{ margin: .45rem 0; color: var(--muted); font-size: .92rem; overflow-wrap: anywhere; }}
    .contact-line:first-of-type {{ color: var(--ink); }}
    .contents {{ position: sticky; top: 1rem; z-index: var(--z-sticky); margin: 1rem 0 2rem; padding: .65rem .75rem; border: 1px solid var(--line); border-radius: var(--radius-control); background: var(--surface); }}
    .contents ul {{ display: flex; gap: .5rem 1.15rem; margin: 0; padding: 0 .25rem; list-style: none; overflow-x: auto; }}
    .contents a {{ display: block; padding: .35rem 0; color: var(--muted); font-size: .78rem; text-decoration: none; white-space: nowrap; transition: color var(--dur-short) var(--ease-out); }}
    .contents a:hover {{ color: var(--accent); }}
    .cv-grid {{ display: grid; grid-template-columns: 15rem minmax(0, 1fr); gap: clamp(1.5rem, 5vw, 5rem); align-items: start; }}
    .rail {{ position: sticky; top: 4.5rem; }}
    .rail h2 {{ margin: 0 0 .75rem; font-family: var(--font-mono); font-size: .82rem; color: var(--accent); letter-spacing: .1em; text-transform: uppercase; }}
    .rail p {{ margin: 0; color: var(--muted); font-size: .9rem; }}
    .rail-nav {{ display: grid; gap: .4rem; margin-top: 1.25rem; }}
    .rail-nav a {{ color: var(--muted); font-family: var(--font-mono); font-size: .78rem; text-decoration: none; white-space: nowrap; transition: color var(--dur-short) var(--ease-out); }}
    .rail-nav a:hover {{ color: var(--accent); }}
    .cv-section {{ scroll-margin-top: 6rem; padding: 2.4rem 0; border-top: 1px solid var(--line); }}
    .cv-section:first-child {{ padding-top: 0; border-top: 0; }}
    .section-heading {{ display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; margin-bottom: 1.25rem; }}
    .section-heading h2 {{ margin: 0; font-family: var(--font-display); font-size: clamp(1.55rem, 3vw, 2.3rem); font-style: normal; letter-spacing: -.025em; }}
    .section-heading p {{ margin: 0; color: var(--muted); font-family: var(--font-mono); font-size: .78rem; }}
    .subsection-title {{ margin: 2rem 0 .8rem; color: var(--accent); font-family: var(--font-mono); font-size: .88rem; letter-spacing: .02em; }}
    .year-heading {{ margin: 1.7rem 0 .75rem; font-family: var(--font-display); font-size: 1.1rem; font-style: normal; color: var(--ink); }}
    .record-item {{ padding: .95rem 0; border-top: 1px solid var(--line); color: var(--muted); }}
    .record-item:first-of-type {{ border-top: 0; padding-top: 0; }}
    .field-label {{ color: var(--ink); font-weight: 700; }}
    .publication {{ display: grid; grid-template-columns: 2.5rem minmax(0, 1fr); gap: .75rem; padding: .8rem 0; border-top: 1px solid var(--line); }}
    .publication-number {{ color: var(--accent); font-variant-numeric: tabular-nums; font-weight: 750; }}
    .publication p {{ margin: 0; color: var(--muted); }}
    .publication-note {{ color: var(--muted); }}
    .source-note {{ margin-top: 2rem; padding: 1rem 1.1rem; border: 1px solid var(--line); border-radius: var(--radius-control); background: var(--surface-soft); color: var(--muted); font-size: .88rem; }}
    .footer {{ margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--line); color: var(--muted); font-size: .82rem; }}
    @media (max-width: 860px) {{
      .page {{ width: min(calc(100% - 1.25rem), var(--max)); padding-top: 1rem; }}
      .hero {{ grid-template-columns: 1fr; }}
      .hero h1 {{ max-width: 16ch; }}
      .contact {{ max-width: 34rem; }}
      .cv-grid {{ grid-template-columns: 1fr; }}
      .rail {{ display: none; }}
    }}
    @media (max-width: 560px) {{
      .topbar {{ align-items: flex-start; }}
      .actions .action:last-child {{ display: none; }}
      .hero {{ padding: 1.25rem; }}
      .hero h1 {{ font-size: clamp(2.55rem, 15vw, 4.8rem); }}
      .contents {{ top: .5rem; }}
      .section-heading {{ display: block; }}
      .section-heading p {{ margin-top: .35rem; }}
      .publication {{ grid-template-columns: 1.8rem minmax(0, 1fr); gap: .55rem; }}
    }}
    @media print {{
      :root {{ color-scheme: light; }}
      body {{ background: var(--color-paper); }}
      .page {{ width: 100%; padding: 0; }}
      .topbar, .contents, .rail, .actions {{ display: none; }}
      .hero {{ border: 0; padding: 0 0 1rem; border-radius: 0; }}
      .hero h1 {{ font-size: 3.7rem; }}
      .cv-grid {{ display: block; }}
      .cv-section {{ break-inside: avoid; }}
      .source-note {{ display: none; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#cv-content">Skip to CV content</a>
  <main class="page">
    <header class="topbar">
      <div class="wordmark">Symbiotic Biomaterials Lab</div>
      <div class="actions">
        <a class="action" href="index.html">Back to portal</a>
        <button class="action" type="button" onclick="window.print()">Print / save PDF</button>
      </div>
    </header>

    <section class="hero" aria-labelledby="cv-title">
      <div>
        <h1 id="cv-title">Sung-Hwan <span>Choi</span></h1>
        <p class="hero-subtitle">Curriculum Vitae · D.D.S., Ph.D.</p>
        <ul class="hero-list">{profile_html}</ul>
        {metrics_html}
      </div>
      <aside class="contact" aria-labelledby="contact-title">
        <h2 id="contact-title">Contact information</h2>
        {contact_html}
      </aside>
    </section>

    <nav class="contents" aria-label="CV sections">
      <ul>
        <li><a href="#education">Education</a></li>
        <li><a href="#positions">Positions</a></li>
        <li><a href="#appointments">Appointments</a></li>
        <li><a href="#honors">Honors</a></li>
        <li><a href="#grants">Grants</a></li>
        <li><a href="#publications">Publications</a></li>
      </ul>
    </nav>

    <div class="cv-grid" id="cv-content">
      <aside class="rail">
        <h2>Curriculum vitae</h2>
        <p>Academic appointments, research support, and selected peer-reviewed publications.</p>
        <nav class="rail-nav" aria-label="CV section navigation">
          <a href="#education">Education</a>
          <a href="#positions">Positions</a>
          <a href="#appointments">Appointments</a>
          <a href="#honors">Honors</a>
          <a href="#grants">Grants</a>
          <a href="#publications">Publications</a>
        </nav>
      </aside>

      <div>
        <section class="cv-section" id="education">
          <div class="section-heading"><h2>Education</h2></div>
          {education_html}
        </section>
        <section class="cv-section" id="positions">
          <div class="section-heading"><h2>Positions and employment</h2></div>
          {positions_html}
        </section>
        <section class="cv-section" id="appointments">
          <div class="section-heading"><h2>Administrative appointments</h2></div>
          {admin_html}
        </section>
        <section class="cv-section" id="honors">
          <div class="section-heading"><h2>Honors and awards</h2></div>
          {honors_html}
        </section>
        <section class="cv-section" id="grants">
          <div class="section-heading"><h2>Research grants and support</h2><p>PI and Co-PI projects</p></div>
          {grants_html}
        </section>
        <section class="cv-section" id="publications">
          <div class="section-heading"><h2>Peer-reviewed publications</h2></div>
          {publications_html}
        </section>
      </div>
    </div>
    <footer class="footer">Sung-Hwan Choi · Yonsei University College of Dentistry</footer>
  </main>
</body>
</html>
'''

OUTPUT_PATH.write_text(html_document, encoding="utf-8")
print(f"Wrote {OUTPUT_PATH}")
print(f"Pages: {len(raw.split(chr(12))) if chr(12) in raw else 'source extracted'}")
print(f"Characters: {len(raw)}")
