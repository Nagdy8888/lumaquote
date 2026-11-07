const fs = require('node:fs');
const { chromium } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

/** Patterns that must never appear on a page captured for LinkedIn: credentials, tokens, emails and phone numbers (same set as the capture-mode mask). */
const PRIVATE = [
  /\bsk-[A-Za-z0-9_-]{16,}/, /\blsv2_[A-Za-z0-9_-]{16,}/, /\bEAA[A-Za-z0-9]{20,}/, /\beyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}/,
  /[\w.+-]+@[\w-]+\.[\w.-]+/, /\+\d[\d \-().]{7,18}\d/, /(?<![\w-])\d{10,15}(?![\w-])/,
];
const VIEWPORTS = { desktop: { width: 1440, height: 1050 }, portrait: { width: 390, height: 844 } };
const ROUTES = [
  ['overview', '/'],
  ['inbox', '/inbox'],
  ['quotations', '/quotations'],
  ['catalog', '/catalog'],
  ['connections', '/integrations'],
  ['new-request', '/requests/new'],
  ['not-found', '/does-not-exist'],
];
const SCREENSHOTS = '.local/ui-review';
let step = 'start';

/** Sign in as the fixture staff user without recording the credentials anywhere. */
async function signIn(page, configuration) {
  await page.goto(configuration.url);
  await page.getByLabel('Staff email').fill(configuration.email);
  await page.getByLabel('Password', { exact: true }).fill(configuration.password);
  await page.getByRole('button', { name: 'Open workspace' }).click();
  await page.getByRole('heading', { name: 'A clearer path to every quote.' }).waitFor();
}

/** Collect console errors and uncaught page errors (text truncated) so the test can require none. */
function watchConsole(page, label, sink) {
  page.on('pageerror', (error) => sink.push(`${label}: pageerror ${error.message.slice(0, 120)}`));
  page.on('console', (message) => {
    if (message.type() === 'error') sink.push(`${label}: console.error ${message.text().slice(0, 120)}`);
  });
}

/** Measure Navigation Timing and the largest contentful paint of the page as loaded (milliseconds, rounded). */
async function measure(page) {
  return page.evaluate(() => new Promise((resolve) => {
    const nav = performance.getEntriesByType('navigation')[0];
    let lcp = null;
    try {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        lcp = entries[entries.length - 1].startTime;
      }).observe({ type: 'largest-contentful-paint', buffered: true });
    } catch { /* LCP is not available in this browser build */ }
    setTimeout(() => resolve({
      dom_content_loaded_ms: Math.round(nav.domContentLoadedEventEnd),
      load_ms: Math.round(nav.loadEventEnd),
      lcp_ms: lcp === null ? null : Math.round(lcp),
    }), 300);
  }));
}

/** Review one loaded view: axe (ids and impact only), overflow, landmarks, names, target sizes, timing, a screenshot, then capture-mode privacy. */
async function reviewView(page, key, report, extra = {}) {
  step = `review ${key}`;
  await page.locator('main, [role="main"]').first().waitFor();
  await page.waitForTimeout(800);
  const axe = await new AxeBuilder({ page }).analyze();
  const entry = {
    axe: axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
    horizontal_overflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
    main_landmarks: await page.locator('main, [role="main"]').count(),
    h1_count: await page.locator('h1').count(),
    unnamed_controls: await page.evaluate(() =>
      [...document.querySelectorAll('a, button, input, select, textarea')]
        .filter((el) => el.offsetParent !== null && el.type !== 'hidden')
        .filter((el) => !(el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || (el.labels && el.labels.length) || el.textContent.trim() || el.getAttribute('title'))).length),
    small_targets: await page.evaluate(() =>
      [...document.querySelectorAll('a, button, input, select, textarea, [role="button"]')]
        .filter((el) => el.offsetParent !== null && !el.classList.contains('sr-only'))
        .map((el) => ({ box: el.getBoundingClientRect(), el }))
        .filter(({ box }) => box.width > 0 && (box.width < 24 || box.height < 24))
        .map(({ box, el }) => `${el.tagName.toLowerCase()} ${Math.round(box.width)}x${Math.round(box.height)} ${(el.getAttribute('aria-label') || el.textContent || el.name || el.type || '').trim().slice(0, 24)}`)),
    timing: await measure(page),
    ...extra,
  };
  await page.screenshot({ path: `${SCREENSHOTS}/${key}.png`, fullPage: true });
  const normalText = await page.locator('body').innerText();
  await page.getByRole('button', { name: 'Capture mode' }).click();
  await page.waitForTimeout(300);
  const capturedText = await page.locator('body').innerText();
  entry.capture = {
    private_matches: PRIVATE.map((pattern, index) => (pattern.test(capturedText) ? `pattern ${index}` : null)).filter(Boolean),
    text_length: capturedText.length,
    normal_mode_private_patterns: PRIVATE.filter((pattern) => pattern.test(normalText)).length,
    masked_email: capturedText.includes('[email]'),
    masked_phone: capturedText.includes('[phone]'),
  };
  report.views[key] = entry;
}

/** Walk Tab from the top of the inbox and record how many presses reach the skip link, the conversation list, the composer and the approval control. */
async function keyboardPass(page, configuration, report) {
  step = 'keyboard pass';
  await page.goto(`${configuration.url}/inbox/${configuration.conversation_id}`);
  await page.getByRole('button', { name: 'Review approval' }).waitFor();
  await page.waitForTimeout(800);
  const reached = {};
  const stops = [];
  for (let press = 1; press <= 120; press += 1) {
    await page.keyboard.press('Tab');
    const stop = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      return {
        label: (el.getAttribute('aria-label') || el.textContent || el.name || '').trim().slice(0, 30),
        skip: el.classList.contains('skip-link'),
        list: !!el.closest('nav[aria-label="Customer conversations"]'),
        composer: !!el.closest('.composer') && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT'),
        approval: el.tagName === 'BUTTON' && el.textContent.trim() === 'Review approval',
      };
    });
    stops.push(stop && stop.label);
    for (const name of ['skip', 'list', 'composer', 'approval']) {
      if (stop && stop[name] && reached[name] === undefined) reached[name] = press;
    }
    if (['skip', 'list', 'composer', 'approval'].every((name) => reached[name] !== undefined)) break;
  }
  report.keyboard = { tab_presses_to: reached, first_stops: stops.slice(0, 8) };
}

/** Prove a live stream is open, then that a change made in a second signed-in browser appears here, and record how long it took. */
async function livePass(browser, page, configuration, report) {
  step = 'live pass';
  const requests = [];
  page.on('request', (request) => {
    if (request.url().includes('/api/events')) requests.push(request.url().split('?')[0]);
  });
  const started = Date.now();
  await page.goto(`${configuration.url}/inbox/${configuration.conversation_id}`);
  report.live = { live_label_seen: false, events_requests: 0, cross_tab_ms: null };
  try {
    await page.locator('.live-state[data-live="true"]').waitFor({ timeout: 15000 });
    report.live.live_label_seen = true;
    report.live.live_label_ms = Date.now() - started;
    report.live.live_label_text = (await page.locator('.live-state').innerText()).trim();
  } catch { /* recorded as not seen */ }
  const second = await (await browser.newContext({ viewport: VIEWPORTS.desktop, reducedMotion: 'reduce' })).newPage();
  watchConsole(second, 'second-tab', report.console);
  await signIn(second, configuration);
  await second.goto(`${configuration.url}/inbox/${configuration.conversation_id}`);
  await second.getByPlaceholder('Add a note for your team…').waitFor();
  const note = `Cross-tab check ${Date.now()}`;
  await second.getByPlaceholder('Add a note for your team…').fill(note);
  const clicked = Date.now();
  await second.getByRole('button', { name: 'Add note' }).click();
  try {
    await page.getByText(note).first().waitFor({ timeout: 12000 });
    report.live.cross_tab_ms = Date.now() - clicked;
  } catch { /* recorded as null */ }
  report.live.events_requests = requests.length;
  await second.context().close();
}

/** Sign in once per viewport, review every route and the populated conversation states, then run the keyboard and live passes on desktop. */
async function main() {
  const configuration = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  fs.mkdirSync(SCREENSHOTS, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const deadline = setTimeout(() => void browser.close(), 230000);
  const report = { views: {}, console: [], keyboard: null, live: null };
  try {
    for (const [size, viewport] of Object.entries(VIEWPORTS)) {
      const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
      const page = await context.newPage();
      watchConsole(page, size, report.console);
      await signIn(page, configuration);
      for (const [name, route] of ROUTES) {
        await page.goto(configuration.url + route);
        await reviewView(page, `${name}-${size}`, report);
      }
      const portrait = viewport.width <= 680;
      const conversation = `${configuration.url}/inbox/${configuration.conversation_id}`;
      const sections = portrait
        ? [['conversation', null], ['quotation', 'Quotation'], ['approval-open', 'Quotation']]
        : [['conversation', null], ['approval-open', null]];
      for (const [name, section] of sections) {
        step = `setup conversation-${name}-${size}`;
        await page.goto(conversation);
        // The unselected panel is display:none in portrait, so role queries cannot see it; wait on the element instead.
        await page.locator('.quotation-panel').waitFor({ state: 'attached' });
        if (section) await page.getByRole('radio', { name: new RegExp(`^${section}`) }).click();
        if (name === 'approval-open') {
          await page.getByRole('button', { name: 'Review approval' }).click();
          await page.getByRole('region', { name: 'Confirm approval' }).waitFor();
        }
        const text = await page.locator('body').innerText();
        await reviewView(page, `conversation-${name}-${size}`, report, {
          fixture_email_visible_in_normal_mode: text.includes(configuration.fixture_email),
        });
      }
      await context.close();
    }
    const context = await browser.newContext({ viewport: VIEWPORTS.desktop, reducedMotion: 'reduce' });
    const page = await context.newPage();
    watchConsole(page, 'desktop-flows', report.console);
    await signIn(page, configuration);
    await keyboardPass(page, configuration, report);
    await livePass(browser, page, configuration, report);
    await context.close();
  } finally {
    clearTimeout(deadline);
    await browser.close();
  }
  fs.writeFileSync(configuration.report, JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(`[${step}] ${error.message.slice(0, 1500)}`);
  process.exit(1);
});
