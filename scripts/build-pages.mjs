#!/usr/bin/env node
/**
 * build-pages.mjs — generates the GitHub Pages site for qa-agent-skills.
 *
 * Scans skills/<name>/SKILL.md, parses the YAML frontmatter (`name` and
 * `description` are required by the Agent Skills spec), and emits a single
 * landing page with one card per skill. Chrome and color tokens are copied
 * from pages/ verbatim so the look matches the other DwonnG project sites.
 *
 * The script is intentionally dependency-free so it runs anywhere Node 20+
 * is available (local terminal, GitHub Actions, etc.) without an install
 * step. The "YAML" parser only handles the simple key: value frontmatter
 * the spec actually uses; anything fancier should switch to a real lib.
 *
 * Output layout (relative to repo root):
 *   _site/
 *     index.html            ← landing page with the indexed skill grid
 *     404.html              ← matching 404 chrome
 *     styles.css, app.js, favicon.svg  (copied from pages/)
 *     data/skills.json      ← machine-readable mirror of the dashboard data
 */

import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const SKILLS_DIR = join(ROOT, "skills");
const PAGES_DIR = join(ROOT, "pages");
const OUT = join(ROOT, "_site");

// Project pages are served from <user>.github.io/<repo>/ so every absolute
// link in the chrome needs to be prefixed. Override with PAGES_BASE for
// local preview at "/" if you ever serve it without the prefix.
const PAGES_BASE = process.env.PAGES_BASE ?? "/qa-agent-skills";
const REPO_URL = "https://github.com/DwonnG/qa-agent-skills";

function ensureDir(dir) {
  mkdirSync(dir, { recursive: true });
}

function resetOutput() {
  if (existsSync(OUT)) {
    rmSync(OUT, { recursive: true, force: true });
  }
  ensureDir(OUT);
}

// Minimal YAML frontmatter reader. Pulls the leading `---` block, splits on
// the first colon per line, and returns a flat string map. Multi-line scalars
// and lists aren't needed for SKILL.md frontmatter — keep this dumb on
// purpose. If a future skill needs nested metadata, switch to a real parser.
function parseFrontmatter(source) {
  const match = source.match(/^---\s*\n([\s\S]*?)\n---/u);
  if (!match) return null;
  const out = {};
  for (const rawLine of match[1].split("\n")) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const colon = line.indexOf(":");
    if (colon < 0) continue;
    const key = line.slice(0, colon).trim();
    let value = line.slice(colon + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    out[key] = value;
  }
  return out;
}

function loadSkills() {
  if (!existsSync(SKILLS_DIR)) return [];
  const entries = readdirSync(SKILLS_DIR, { withFileTypes: true });
  const skills = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const skillMd = join(SKILLS_DIR, entry.name, "SKILL.md");
    if (!existsSync(skillMd)) continue;
    const source = readFileSync(skillMd, "utf8");
    const meta = parseFrontmatter(source);
    if (!meta?.name || !meta?.description) {
      console.warn(`[build-pages] skipping ${entry.name}: missing name/description in frontmatter`);
      continue;
    }
    skills.push({
      slug: entry.name,
      name: meta.name,
      description: meta.description,
      allowedTools: meta["allowed-tools"] ?? null,
      // Best-effort byte size lets us hint at "depth" of a skill on the card
      // without parsing the whole file — small skills are quick wins, big
      // ones tend to have reference/ subdirectories full of detail.
      sizeBytes: statSync(skillMd).size,
    });
  }
  return skills.sort((a, b) => a.name.localeCompare(b.name));
}

function esc(value) {
  return String(value)
    .replace(/&/gu, "&amp;")
    .replace(/</gu, "&lt;")
    .replace(/>/gu, "&gt;")
    .replace(/"/gu, "&quot;")
    .replace(/'/gu, "&#39;");
}

function formatKb(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

// SKILL.md descriptions are written for agent routing and typically end with
// a "Use when ..." clause that doubles the length without telling a human
// what the skill does. For the catalog card we strip that tail so the
// preview stays a single sentence about the "what". The full description
// is still authoritative in SKILL.md (linked from the card CTA).
function shortDescription(description) {
  const useWhen = description.search(/\.\s+Use\s+(when|this\s+skill)\b/iu);
  if (useWhen > 0) return description.slice(0, useWhen + 1).trim();
  // Fall back to the first sentence if the description is still long.
  if (description.length > 220) {
    const period = description.indexOf(". ");
    if (period > 0 && period < 240) return description.slice(0, period + 1);
  }
  return description;
}

function renderSkillCard(skill) {
  const sourceHref = `${REPO_URL}/blob/main/skills/${encodeURIComponent(skill.slug)}/SKILL.md`;
  return `
    <a class="suite-card suite-card--idle" href="${esc(sourceHref)}" target="_blank" rel="noopener noreferrer">
      <div class="suite-card-head">
        <h3>${esc(skill.name)}</h3>
        <span class="status-chip status-chip--idle">${esc(formatKb(skill.sizeBytes))}</span>
      </div>
      <p class="suite-card-desc">${esc(shortDescription(skill.description))}</p>
      <p class="suite-cta">View SKILL.md <span class="arrow">&rarr;</span></p>
    </a>
  `;
}

function renderHeroMetrics(skills) {
  const totalBytes = skills.reduce((a, s) => a + s.sizeBytes, 0);
  // Use the portfolio's .metrics / .metric* tokens so spacing, borders, and
  // typography match the qa-automation-lab dashboard exactly.
  return `
    <div class="metrics" aria-label="Catalog summary">
      <div class="metric">
        <span class="metric-value">${skills.length}</span>
        <span class="metric-label">Skills</span>
      </div>
      <div class="metric">
        <span class="metric-value">${formatKb(totalBytes)}</span>
        <span class="metric-label">SKILL.md</span>
      </div>
      <div class="metric">
        <span class="metric-value">Spec</span>
        <span class="metric-label">agentskills.io</span>
      </div>
    </div>
  `;
}

function renderDashboard(skills) {
  return baseLayout({
    title: "qa-agent-skills",
    body: `
      <header class="hero">
        <div class="hero-inner">
          <div class="hero-intro">
            <div class="hero-mark" aria-hidden="true">QA</div>
            <span class="status-badge status-badge--ok">
              <span class="status-dot"></span>
              <span>${skills.length} skills indexed</span>
            </span>
          </div>
          <h1 class="hero-title">qa-agent-skills</h1>
          <p class="hero-lead">
            A catalog of reusable, spec-compliant
            <a href="https://agentskills.io/specification" target="_blank" rel="noopener noreferrer">Agent Skills</a>
            for QA workflows &mdash; ticket triage, release verification,
            test generation, code review, and more. Drop them into Claude
            Code, Codex, or any spec-compatible runner.
          </p>
          <div class="hero-actions">
            <a class="btn btn--primary" href="${REPO_URL}" target="_blank" rel="noopener noreferrer">
              <span>View on GitHub</span>
              <span class="btn-aside">main</span>
            </a>
            <a class="btn btn--ghost" href="https://agentskills.io/specification" target="_blank" rel="noopener noreferrer">Spec &rarr;</a>
          </div>
          ${renderHeroMetrics(skills)}
        </div>
      </header>

      <main id="main">
        <section class="section" id="skills">
          <div class="section-head">
            <p class="eyebrow"><span class="eyebrow-num">01</span> Catalog</p>
            <h2>Available skills</h2>
            <p class="section-desc">
              Each card opens the skill&rsquo;s <code>SKILL.md</code> on GitHub.
              Skills follow the Agent Skills spec: YAML frontmatter declares
              <code>name</code> and <code>description</code>, the body
              documents the workflow, and <code>references/</code> holds
              deep links.
            </p>
          </div>
          <div class="suite-grid">
            ${skills.map(renderSkillCard).join("\n")}
          </div>
        </section>

        <section class="section" id="install">
          <div class="section-head">
            <p class="eyebrow"><span class="eyebrow-num">02</span> Install</p>
            <h2>Add a skill to your runner</h2>
          </div>
          <div class="about-card">
            <p>
              Clone the repo and symlink (or copy) the skill directories into
              the runner&rsquo;s skills path. For Claude Code, that&rsquo;s
              <code>~/.claude/skills/</code>; for Codex, <code>~/.codex/skills/</code>.
            </p>
            <pre><code>git clone ${REPO_URL}.git
ln -s "$(pwd)/qa-agent-skills/skills/qa-workflow" ~/.claude/skills/qa-workflow</code></pre>
            <p>
              Skill names must stay in lowercase kebab-case, and the directory
              name must exactly match the <code>name</code> in
              <code>SKILL.md</code>. See <a href="${REPO_URL}/blob/main/README.md" target="_blank" rel="noopener noreferrer">README</a>
              for contribution rules.
            </p>
          </div>
        </section>
      </main>

      <footer class="footer">
        <p>
          Built by
          <a href="https://dwonng.github.io" target="_blank" rel="noopener noreferrer">Dwonn Goodwin</a>
          &middot; MIT licensed &middot;
          <a href="${REPO_URL}" target="_blank" rel="noopener noreferrer">source</a>
          &middot; data:
          <a href="${PAGES_BASE}/data/skills.json">skills.json</a>
        </p>
      </footer>
    `,
  });
}

function render404() {
  return baseLayout({
    title: "404 · qa-agent-skills",
    body: `
      <main class="detail" id="main" style="text-align: center">
        <header class="detail-head" style="margin-top: 2rem">
          <p class="eyebrow"><span class="eyebrow-num">404</span> Not found</p>
          <h1>This page isn&rsquo;t in the catalog</h1>
          <p class="lede" style="margin-left: auto; margin-right: auto; max-width: 50ch">
            The page you were looking for isn&rsquo;t here. The catalog and
            the source repo are linked below.
          </p>
          <div class="hero-actions" style="justify-content: center">
            <a class="btn btn--primary" href="${PAGES_BASE}/">Back to catalog</a>
            <a class="btn btn--ghost" href="${REPO_URL}" target="_blank" rel="noopener noreferrer">View on GitHub</a>
          </div>
        </header>
      </main>
    `,
  });
}

function baseLayout({ title, body }) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="color-scheme" content="light dark" />
    <title>${esc(title)}</title>
    <meta name="description" content="qa-agent-skills — a catalog of reusable QA skills for AI agents." />
    <link rel="icon" type="image/svg+xml" href="${PAGES_BASE}/favicon.svg" />
    <meta name="theme-color" content="#0a0a0d" media="(prefers-color-scheme: dark)" />
    <meta name="theme-color" content="#f6f7fa" media="(prefers-color-scheme: light)" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap"
      rel="stylesheet"
    />
    <script>
      (function () {
        try {
          var saved = localStorage.getItem("theme");
          var systemLight = window.matchMedia("(prefers-color-scheme: light)").matches;
          var theme = saved || (systemLight ? "light" : "dark");
          document.documentElement.setAttribute("data-theme", theme);
        } catch (_) {
          document.documentElement.setAttribute("data-theme", "dark");
        }
      })();
    </script>
    <link rel="stylesheet" href="${PAGES_BASE}/styles.css" />
  </head>
  <body>
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-glow bg-glow--a" aria-hidden="true"></div>
    <div class="bg-glow bg-glow--b" aria-hidden="true"></div>
    <div class="bg-glow bg-glow--c" aria-hidden="true"></div>
    <div class="bg-glow bg-glow--d" aria-hidden="true"></div>

    <a class="skip-link" href="#main">Skip to content</a>

    <nav class="top-nav" aria-label="Site">
      <a class="nav-brand" href="${PAGES_BASE}/">
        <span class="nav-brand-mark" aria-hidden="true">QA</span>
        <span>agent-skills</span>
      </a>
      <div class="nav-links">
        <a href="${PAGES_BASE}/#skills">Skills</a>
        <a href="${PAGES_BASE}/#install">Install</a>
        <a href="${REPO_URL}" target="_blank" rel="noopener noreferrer">GitHub</a>
      </div>
    </nav>

    ${body}

    <button class="theme-toggle" type="button" aria-label="Toggle color theme" title="Toggle color theme">
      <svg class="theme-toggle__icon theme-toggle__sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
      </svg>
      <svg class="theme-toggle__icon theme-toggle__moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    </button>

    <script src="${PAGES_BASE}/app.js" defer></script>
  </body>
</html>
`;
}

function copyChromeAssets() {
  for (const filename of ["styles.css", "app.js", "favicon.svg"]) {
    const src = join(PAGES_DIR, filename);
    if (!existsSync(src)) {
      throw new Error(`Missing chrome asset: ${src}`);
    }
    cpSync(src, join(OUT, filename));
  }
}

function main() {
  resetOutput();
  const skills = loadSkills();
  copyChromeAssets();
  writeFileSync(join(OUT, "index.html"), renderDashboard(skills));
  writeFileSync(join(OUT, "404.html"), render404());
  ensureDir(join(OUT, "data"));
  writeFileSync(
    join(OUT, "data", "skills.json"),
    JSON.stringify(
      {
        generated_at: new Date().toISOString(),
        repo: REPO_URL,
        count: skills.length,
        skills,
      },
      null,
      2,
    ),
  );
  console.log(`[build-pages] indexed ${skills.length} skills into ${OUT}`);
}

main();
