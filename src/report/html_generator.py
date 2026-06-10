from __future__ import annotations

from pathlib import Path
import json
from html import escape


def _format_year_or_date(paper: dict[str, object]) -> str:
    if paper.get("published_date"):
        return str(paper["published_date"])
    if paper.get("year"):
        return str(paper["year"])
    return "Unknown date"


def generate_html(
    papers: list[dict[str, object]],
    output_path: str | Path,
    topics: list[str],
    source_labels: list[tuple[str, str]],
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(papers, ensure_ascii=False)
    topic_options = "\n".join(
        f'<option value="{escape(topic)}">{escape(topic.title())}</option>' for topic in topics
    )
    source_buttons = "\n".join(
        f'<button class="tab" data-source="{escape(source)}">{escape(label)}</button>'
        for source, label in source_labels
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paper Index</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f4ef;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --border: #d7d2c8;
      --accent: #0f766e;
      --accent-soft: #d9f0ee;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.08), transparent 30%),
        linear-gradient(180deg, #faf8f2, var(--bg));
    }}
    header {{
      padding: 32px 20px 16px;
      max-width: 1200px;
      margin: 0 auto;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 3vw, 3rem);
    }}
    .subtle {{
      color: var(--muted);
      margin: 0;
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 20px 32px;
    }}
    .controls {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin: 20px 0 18px;
    }}
    .controls input, .controls select {{
      width: 100%;
      border: 1px solid var(--border);
      background: var(--panel);
      border-radius: 12px;
      padding: 12px 14px;
      font: inherit;
    }}
    .tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 18px 0 22px;
    }}
    .tab {{
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      border-radius: 999px;
      padding: 10px 14px;
      font: inherit;
      cursor: pointer;
    }}
    .tab.active {{
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }}
    .meta {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      color: var(--muted);
      margin: 14px 0 18px;
      flex-wrap: wrap;
    }}
    .grid {{
      display: grid;
      gap: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px 18px;
      box-shadow: 0 4px 20px rgba(31, 41, 55, 0.04);
    }}
    .card h2 {{
      margin: 0 0 8px;
      font-size: 1.05rem;
      line-height: 1.35;
    }}
    .card h2 a {{
      color: inherit;
      text-decoration: none;
    }}
    .card h2 a:hover {{
      color: var(--accent);
      text-decoration: underline;
    }}
    .authors, .date {{
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }}
    .empty {{
      padding: 30px;
      text-align: center;
      color: var(--muted);
      background: rgba(255,255,255,0.7);
      border: 1px dashed var(--border);
      border-radius: 18px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Paper Index</h1>
    <p class="subtle">Local-first browsing of paper metadata from OpenAlex, arXiv, Semantic Scholar, and optional Google Scholar.</p>
  </header>
  <main>
    <div class="controls">
      <input id="titleSearch" type="search" placeholder="Search title">
      <input id="authorSearch" type="search" placeholder="Search author">
      <select id="topicFilter">
        <option value="all">All topics</option>
        {topic_options}
      </select>
      <select id="sortOrder">
        <option value="oldest">Oldest first</option>
        <option value="newest">Newest first</option>
      </select>
    </div>
    <div class="tabs">
      <button class="tab active" data-source="all">All</button>
      {source_buttons}
    </div>
    <div class="meta">
      <div id="countLabel">0 papers</div>
      <div id="statusLabel">Ready</div>
    </div>
    <div id="grid" class="grid"></div>
  </main>
  <script>
    const PAPERS = {payload};
    const state = {{
      source: "all",
      topic: "all",
      sort: "oldest",
      title: "",
      author: "",
    }};

    const grid = document.getElementById("grid");
    const countLabel = document.getElementById("countLabel");
    const statusLabel = document.getElementById("statusLabel");
    const titleSearch = document.getElementById("titleSearch");
    const authorSearch = document.getElementById("authorSearch");
    const topicFilter = document.getElementById("topicFilter");
    const sortOrder = document.getElementById("sortOrder");
    const tabs = Array.from(document.querySelectorAll(".tab"));

    function normalize(value) {{
      return (value || "").toString().toLowerCase();
    }}

    function matchesTokenField(field, value) {{
      if (!value || value === "all") return true;
      return normalize(field).split(",").map((part) => part.trim()).includes(value);
    }}

    function paperDateValue(paper) {{
      const raw = paper.published_date || (paper.year ? String(paper.year) : "");
      return raw ? new Date(raw).getTime() || Number(raw) : Number.MAX_SAFE_INTEGER;
    }}

    function sortPapers(items) {{
      return items.sort((a, b) => {{
        const left = paperDateValue(a);
        const right = paperDateValue(b);
        return state.sort === "newest" ? right - left : left - right;
      }});
    }}

    function render() {{
      const filtered = sortPapers(PAPERS.filter((paper) => {{
        if (state.source !== "all" && !matchesTokenField(paper.source, state.source)) return false;
        if (state.topic !== "all" && !matchesTokenField(paper.topic, state.topic)) return false;
        if (state.title && !normalize(paper.title).includes(state.title)) return false;
        if (state.author) {{
          const authors = Array.isArray(paper.authors) ? paper.authors.join(" ") : "";
          if (!normalize(authors).includes(state.author)) return false;
        }}
        return true;
      }}));

      countLabel.textContent = `${{filtered.length}} paper${{filtered.length === 1 ? "" : "s"}}`;
      statusLabel.textContent = `Showing ${{state.source}} / ${{state.topic}} / ${{state.sort}}`;
      grid.innerHTML = "";

      if (!filtered.length) {{
        grid.innerHTML = '<div class="empty">No papers match the current filters.</div>';
        return;
      }}

      for (const paper of filtered) {{
        const card = document.createElement("article");
        card.className = "card";

        const title = document.createElement("h2");
        const link = paper.url ? document.createElement("a") : document.createElement("span");
        if (paper.url) {{
          link.href = paper.url;
          link.target = "_blank";
          link.rel = "noreferrer";
        }}
        link.textContent = paper.title;
        title.appendChild(link);

        const authors = document.createElement("p");
        authors.className = "authors";
        authors.textContent = Array.isArray(paper.authors) && paper.authors.length
          ? paper.authors.join(", ")
          : "Unknown authors";

        const date = document.createElement("p");
        date.className = "date";
        date.textContent = "Publication date or year: " + (paper.published_date || paper.year || "Unknown");

        card.appendChild(title);
        card.appendChild(authors);
        card.appendChild(date);
        grid.appendChild(card);
      }}
    }}

    tabs.forEach((button) => {{
      button.addEventListener("click", () => {{
        tabs.forEach((tab) => tab.classList.remove("active"));
        button.classList.add("active");
        state.source = button.dataset.source;
        render();
      }});
    }});

    titleSearch.addEventListener("input", (event) => {{
      state.title = normalize(event.target.value);
      render();
    }});
    authorSearch.addEventListener("input", (event) => {{
      state.author = normalize(event.target.value);
      render();
    }});
    topicFilter.addEventListener("change", (event) => {{
      state.topic = event.target.value;
      render();
    }});
    sortOrder.addEventListener("change", (event) => {{
      state.sort = event.target.value;
      render();
    }});

    render();
  </script>
</body>
</html>
"""
    path.write_text(html)
    return path
