#!/usr/bin/env node
/**
 * generate-stories.mjs — vyrenderuje vizuálne Stories (1080×1920 PNG) z týždenných dát.
 *
 * Princíp: NEDUPLIKUJE kresliacu logiku. Poženie reálnu `docs/stories.html`
 * v headless Chromiu (Playwright), akurát presmeruje GitHub API + raw obsah
 * na lokálne súbory z tohto repa. Tým je jediný zdroj pravdy tá istá stránka,
 * ktorá beží aj naživo na recepty.sporacek.sk/stories.html.
 *
 * Výstup: tydne/<folder>/stories/<názov>.png (rovnaké názvy ako tlačidlá na stránke).
 *
 * Použitie:
 *   node tools/generate-stories.mjs                 # všetky týždne v tydne/
 *   node tools/generate-stories.mjs 2026-W29-lidl   # len konkrétny týždeň (aj viac)
 *
 * Vyžaduje: Playwright + Chromium (v tomto prostredí sú predinštalované).
 */
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, "..");
const require = createRequire(import.meta.url);

// Playwright je v tomto prostredí globálny (/opt/node22/lib/node_modules)
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (e) {
  try {
    ({ chromium } = require("/opt/node22/lib/node_modules/playwright"));
  } catch (e2) {
    console.error("Nenašiel som Playwright. Nainštaluj: npm i -g playwright");
    process.exit(1);
  }
}

const onlyWeeks = process.argv.slice(2);

function listWeeks() {
  return fs.readdirSync(path.join(REPO, "tydne"), { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
    .filter(name => onlyWeeks.length === 0 || onlyWeeks.includes(name))
    .sort();
}

async function main() {
  const weeks = listWeeks();
  if (weeks.length === 0) { console.error("Žiadne týždne v tydne/."); process.exit(1); }

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 2200 } });

  // presmeruj sieť na lokálne súbory
  await page.route("**/*", async (route) => {
    const url = route.request().url();
    try {
      if (url.includes("fonts.googleapis.com") || url.includes("fonts.gstatic.com")) return route.abort();
      if (url.includes("api.github.com") && url.includes("/contents/tydne")) {
        const dirs = fs.readdirSync(path.join(REPO, "tydne"), { withFileTypes: true })
          .filter(d => d.isDirectory()).map(d => ({ name: d.name, type: "dir" }));
        return route.fulfill({ contentType: "application/json", body: JSON.stringify(dirs) });
      }
      if (url.includes("api.github.com") && url.includes("/contents/fotky")) {
        const files = fs.readdirSync(path.join(REPO, "fotky"))
          .filter(f => f.endsWith(".jpg")).map(f => ({ name: f, type: "file", sha: "localsha00000000" }));
        return route.fulfill({ contentType: "application/json", body: JSON.stringify(files) });
      }
      const m = url.match(/raw\.githubusercontent\.com\/.*?\/main\/(.+)$/);
      if (m) {
        const rel = decodeURIComponent(m[1].split("?")[0]);
        const fp = path.join(REPO, rel);
        if (fs.existsSync(fp)) {
          const ext = path.extname(fp).toLowerCase();
          const ct = { ".json": "application/json", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".svg": "image/svg+xml", ".webp": "image/webp" }[ext] || "text/plain";
          return route.fulfill({ contentType: ct, body: fs.readFileSync(fp) });
        }
        return route.fulfill({ status: 404, body: "not found: " + rel });
      }
      return route.continue();
    } catch (err) {
      return route.fulfill({ status: 500, body: String(err) });
    }
  });

  await page.goto("file://" + path.join(REPO, "docs/stories.html"));
  await page.waitForSelector(".week-chip", { timeout: 20000 });

  let total = 0;
  for (const folder of weeks) {
    // klikni na správny week-chip a počkaj na dorenderovanie
    const picked = await page.evaluate((f) => {
      const chip = [...document.querySelectorAll(".week-chip")].find(c => c.textContent.trim() === f);
      if (!chip) return false;
      chip.click();
      return true;
    }, folder);
    if (!picked) { console.warn(`⚠ ${folder}: chip sa nenašiel, preskakujem`); continue; }

    try {
      await page.waitForFunction((f) => {
        const t = document.getElementById("pageTitle")?.textContent || "";
        return window.__storyNames && window.__storyNames.length > 0 &&
               document.querySelectorAll(".cv canvas").length === window.__storyNames.length;
      }, folder, { timeout: 30000 });
    } catch (e) {
      console.warn(`⚠ ${folder}: žiadne stories (chýba social.stories?), preskakujem`);
      continue;
    }
    await page.waitForTimeout(600);

    const slides = await page.evaluate(() => {
      const names = window.__storyNames || [];
      const cvs = [...document.querySelectorAll(".cv canvas")];
      return cvs.map((c, i) => ({ name: names[i], data: c.toDataURL("image/png") }));
    });

    const outDir = path.join(REPO, "tydne", folder, "stories");
    fs.mkdirSync(outDir, { recursive: true });
    for (const s of slides) {
      if (!s.name || !s.data) continue;
      fs.writeFileSync(path.join(outDir, s.name), Buffer.from(s.data.split(",")[1], "base64"));
      total++;
    }
    console.log(`✓ ${folder}: ${slides.length} slidov → tydne/${folder}/stories/`);
  }

  await browser.close();
  console.log(`Hotovo — ${total} PNG súborov.`);
}

main().catch((e) => { console.error(e); process.exit(1); });
