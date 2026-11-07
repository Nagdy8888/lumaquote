const fs = require('node:fs');
const { chromium } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const ROUTES = [
  ['overview', '/'],
  ['inbox', '/inbox'],
  ['new-request', '/requests/new'],
  ['quotations', '/quotations'],
  ['catalog', '/catalog'],
  ['connections', '/integrations'],
];
const VIEWPORTS = { desktop: { width: 1440, height: 1050 }, portrait: { width: 430, height: 932 } };

/** Sign in as the fixture staff user without recording the credentials anywhere. */
async function signIn(page, configuration) {
  await page.goto(configuration.url);
  await page.getByLabel('Staff email').fill(configuration.email);
  await page.getByLabel('Password', { exact: true }).fill(configuration.password);
  await page.getByRole('button', { name: 'Open workspace' }).click();
  await page.getByRole('heading', { name: 'A clearer path to every quote.' }).waitFor();
}

/** Review every top-level page (plus one populated conversation when configured) at desktop and portrait sizes: axe, overflow, tap targets, focus order and a screenshot. */
async function main() {
  const configuration = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch({ headless: true, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const deadline = setTimeout(() => void browser.close(), 120000);
  const report = { pages: {}, console: [] };
  try {
    for (const [size, viewport] of Object.entries(VIEWPORTS)) {
      const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
      const page = await context.newPage();
      page.on('pageerror', (error) => report.console.push(`${size}: pageerror ${error.message.slice(0, 100)}`));
      page.on('console', (message) => {
        if (message.type() === 'error') report.console.push(`${size}: console.error ${message.text().slice(0, 100)}`);
      });
      await signIn(page, configuration);
      const routes = configuration.conversation_id
        ? [...ROUTES, ['conversation', `/inbox/${configuration.conversation_id}`]]
        : ROUTES;
      for (const [name, route] of routes) {
        await page.goto(configuration.url + route);
        await page.locator('main, [role="main"]').first().waitFor();
        await page.waitForTimeout(700);
        const axe = await new AxeBuilder({ page }).analyze();
        const entry = {
          axe: axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
          horizontal_overflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
          main_landmarks: await page.locator('main, [role="main"]').count(),
          h1_count: await page.locator('h1').count(),
          small_targets: await page.evaluate(() =>
            [...document.querySelectorAll('a, button, input, select, textarea, [role="button"]')]
              .filter((el) => el.offsetParent !== null && !el.classList.contains('sr-only'))
              .map((el) => ({ box: el.getBoundingClientRect(), el }))
              .filter(({ box }) => box.width > 0 && (box.width < 24 || box.height < 24))
              .map(({ box, el }) => `${el.tagName.toLowerCase()} ${Math.round(box.width)}x${Math.round(box.height)} ${(el.getAttribute('aria-label') || el.textContent || el.name || el.type || '').trim().slice(0, 24)}`)),
          unnamed_controls: await page.evaluate(() =>
            [...document.querySelectorAll('a, button, input, select, textarea')]
              .filter((el) => el.offsetParent !== null && el.type !== 'hidden')
              .filter((el) => !(el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || (el.labels && el.labels.length) || el.textContent.trim() || el.getAttribute('title'))).length),
          focus_order_first_stops: [],
        };
        for (let i = 0; i < 6; i += 1) {
          await page.keyboard.press('Tab');
          entry.focus_order_first_stops.push(await page.evaluate(() => {
            const a = document.activeElement;
            return a ? `${a.tagName.toLowerCase()}:${(a.getAttribute('aria-label') || a.textContent || a.name || '').trim().slice(0, 28)}` : null;
          }));
        }
        report.pages[`${name}-${size}`] = entry;
        await page.screenshot({ path: `.local/review-${name}-${size}.png`, fullPage: true });
      }
      await context.close();
    }
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
