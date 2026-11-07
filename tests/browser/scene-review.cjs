const fs = require('node:fs');
const { chromium } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

/** Patterns that must never appear on a page captured for LinkedIn: credentials, tokens, emails and phone numbers. */
const PRIVATE = [
  /\bsk-[A-Za-z0-9_-]{16,}/, /\blsv2_[A-Za-z0-9_-]{16,}/, /\bEAA[A-Za-z0-9]{20,}/, /\beyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}/,
  /[\w.+-]+@[\w-]+\.[\w.-]+/, /\+\d[\d \-().]{7,18}\d/, /(?<![\w-])\d{10,15}(?![\w-])/,
];

/** Sign in as the fixture staff user without recording the credentials anywhere. */
async function signIn(page, configuration) {
  await page.goto(configuration.url);
  await page.getByLabel('Staff email').fill(configuration.email);
  await page.getByLabel('Password', { exact: true }).fill(configuration.password);
  await page.getByRole('button', { name: 'Open workspace' }).click();
  await page.getByRole('heading', { name: 'A clearer path to every quote.' }).waitFor();
}

/** Run axe on the current page and keep only rule ids and impact, never page content. */
async function axeViolations(page) {
  const result = await new AxeBuilder({ page }).analyze();
  return result.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length }));
}

/** Review the optional 3D scene: lazy loading, keyboard use, motion preference, performance and capture privacy. */
async function main() {
  const configuration = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch({ headless: true, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const report = { viewport: {}, motion: {}, reduced: {}, keyboard: {}, performance: {}, privacy: {}, console: [] };
  const deadline = setTimeout(() => void browser.close(), 80000);
  try {
    // 1. Full-motion desktop run, with network and performance observation from navigation onward.
    const context = await browser.newContext({ viewport: { width: 1440, height: 1050 }, reducedMotion: 'no-preference' });
    const page = await context.newPage();
    page.on('pageerror', (error) => report.console.push('pageerror: ' + error.message.slice(0, 120)));
    page.on('console', (message) => {
      if (message.type() === 'error') report.console.push('console.error: ' + message.text().slice(0, 120));
    });
    const scripts = [];
    page.on('response', async (response) => {
      if (response.request().resourceType() === 'script') {
        const length = Number(response.headers()['content-length'] || 0);
        scripts.push({ name: new URL(response.url()).pathname.split('/').pop(), length, at: Date.now() });
      }
    });
    await page.addInitScript(() => {
      window.__long = [];
      window.__raf = 0;
      new PerformanceObserver((list) => list.getEntries().forEach((e) => window.__long.push(Math.round(e.duration)))).observe({ entryTypes: ['longtask'] });
    });
    const start = Date.now();
    await signIn(page, configuration);
    const canvas = page.locator('.lighting-scene canvas');
    await canvas.waitFor({ timeout: 20000 });
    report.performance.scene_visible_ms_after_sign_in_submit = Date.now() - start;
    await page.waitForTimeout(1500);
    report.motion.canvas_count = await page.locator('canvas').count();
    report.motion.webgl_context = await page.evaluate(() => {
      const element = document.querySelector('.lighting-scene canvas');
      return !!(element && (element.getContext('webgl2') || element.getContext('webgl')));
    });
    report.motion.fallback_visible = await page.locator('.lighting-fallback').count();
    report.motion.canvas_box = await canvas.boundingBox();
    report.motion.scene_chunk_requested = scripts.some((s) => /LightingScene|three|fiber/i.test(s.name));
    report.performance.script_requests = scripts.map((s) => ({ name: s.name, length: s.length })).slice(0, 40);
    report.performance.long_tasks_ms = await page.evaluate(() => window.__long);
    const nav = await page.evaluate(() => {
      const entry = performance.getEntriesByType('navigation')[0];
      return { dom_content_loaded_ms: Math.round(entry.domContentLoadedEventEnd), load_ms: Math.round(entry.loadEventEnd) };
    });
    report.performance.navigation = nav;
    report.performance.js_heap_mb = await page.evaluate(() => (performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null));
    // Idle cost: the scene uses frameloop="demand", so an untouched scene should paint almost nothing.
    report.performance.idle_frames_in_2s = await page.evaluate(
      () => new Promise((resolve) => {
        let frames = 0;
        const t0 = performance.now();
        (function tick() {
          frames += 1;
          if (performance.now() - t0 < 2000) requestAnimationFrame(tick); else resolve(frames);
        })();
      }),
    );
    report.viewport.desktop_axe = await axeViolations(page);

    // 2. Keyboard: the temperature radio group is the scene's only keyboard-operable control.
    const radios = page.locator('.temperature-controls input[type="radio"]');
    report.keyboard.radio_count = await radios.count();
    report.keyboard.canvas_tabindex = await canvas.getAttribute('tabindex');
    report.keyboard.canvas_aria_label = (await canvas.getAttribute('aria-label')) || (await page.locator('.lighting-scene [aria-label]').first().getAttribute('aria-label'));
    await radios.first().focus();
    const before = await radios.evaluateAll((nodes) => nodes.map((n) => n.checked));
    await page.keyboard.press('ArrowRight');
    const after = await radios.evaluateAll((nodes) => nodes.map((n) => n.checked));
    report.keyboard.arrow_key_changes_selection = JSON.stringify(before) !== JSON.stringify(after);
    report.keyboard.focus_outline_visible = await page.evaluate(() => {
      const active = document.activeElement;
      const style = active ? getComputedStyle(active) : null;
      const swatch = active && active.nextElementSibling ? getComputedStyle(active.nextElementSibling) : null;
      return { tag: active && active.tagName, outline: style && style.outlineStyle + ' ' + style.outlineWidth, swatch_outline: swatch && swatch.outlineStyle };
    });
    await page.keyboard.press('Tab');
    report.keyboard.tab_after_radios_leaves_scene = await page.evaluate(() => !document.activeElement.closest('.lighting-scene'));
    await radios.first().focus();
    await page.screenshot({ path: '.local/scene-review-focus.png', clip: { x: 0, y: 0, width: 1440, height: 760 } });

    // 3. Capture privacy: the page as it would be screen-recorded.
    const text = await page.locator('body').innerText();
    report.privacy.matches = PRIVATE.map((pattern, index) => (pattern.test(text) ? 'pattern ' + index : null)).filter(Boolean);
    report.privacy.text_length = text.length;
    report.privacy.mentions_synthetic_label = /illustrative/i.test(text);

    // 4. Portrait and reduced-motion variants.
    await page.setViewportSize({ width: 430, height: 932 });
    await page.waitForTimeout(600);
    report.viewport.portrait_axe = await axeViolations(page);
    report.viewport.portrait_horizontal_overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    await context.close();

    const reducedContext = await browser.newContext({ viewport: { width: 1440, height: 1050 }, reducedMotion: 'reduce' });
    const reducedPage = await reducedContext.newPage();
    await signIn(reducedPage, configuration);
    await reducedPage.waitForTimeout(1200);
    report.reduced.canvas_count = await reducedPage.locator('canvas').count();
    report.reduced.fallback_visible = await reducedPage.locator('.lighting-fallback').count();
    report.reduced.axe = await axeViolations(reducedPage);
    await reducedContext.close();
  } finally {
    clearTimeout(deadline);
    await browser.close();
  }
  fs.writeFileSync(configuration.report, JSON.stringify(report, null, 2));
  process.stdout.write(JSON.stringify({ ok: true }));
}

main().catch((error) => {
  process.stderr.write(String(error && error.stack ? error.stack : error).slice(0, 2000));
  process.exit(1);
});
