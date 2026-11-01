const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('@playwright/test');
const { hash } = require('./catalog.cjs');

const theme = {
  startOnLoad: false, securityLevel: 'strict', htmlLabels: false,
  deterministicIds: true, fontFamily: 'Arial, sans-serif', theme: 'base',
  themeVariables: {
    background: '#ffffff', primaryColor: '#f5eee8', primaryTextColor: '#202a29',
    primaryBorderColor: '#966242', lineColor: '#58645e', secondaryColor: '#edf3ee',
    tertiaryColor: '#f7f8f5', clusterBkg: '#f7f8f5', clusterBorder: '#bdc8c0',
    edgeLabelBackground: '#ffffff', fontSize: '16px', noteBkgColor: '#f5eee8',
    noteTextColor: '#202a29', noteBorderColor: '#966242',
  },
  flowchart: { curve: 'linear', useMaxWidth: true, nodeSpacing: 35, rankSpacing: 45 },
  sequence: { useMaxWidth: true, wrap: true, mirrorActors: false },
};

/** Bind generated assets to the pinned engine, theme and owned rendering/catalog implementation. */
function rendererIdentity() {
  const version = require('mermaid/package.json').version;
  const files = ['catalog.cjs', 'render.cjs', 'index.cjs'];
  return {
    version,
    hash: hash(JSON.stringify(theme) + version + files.map(file => fs.readFileSync(path.join(__dirname, file), 'utf8').replaceAll('\r\n', '\n')).join('\n')),
  };
}

/** Render trusted repository sources in local Chromium with external network requests denied; always close the browser. */
async function withRenderer(callback) {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1600, height: 1100 }, reducedMotion: 'reduce' });
    // The renderer never fetches external fonts, images or a hosted diagram service.
    await context.route('**/*', route => route.abort());
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    await page.setContent('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>LumaQuote diagrams</title></head><body></body></html>');
    await page.addScriptTag({ path: require.resolve('mermaid/dist/mermaid.min.js') });
    return await callback(page);
  } finally {
    await browser.close();
  }
}

/** Parse/render one diagram and inspect its real SVG for accessibility, visible bounds and unsafe embedded content. */
async function renderDiagram(page, id, source, preview) {
  const rendered = await page.evaluate(/** Render only repository-owned source and inspect its DOM result. */ async function renderLocalDiagram(input) {
    // Input is repository-owned source, not customer text or a provider response.
    window.mermaid.initialize({ ...input.theme, deterministicIDSeed: input.id });
    await window.mermaid.parse(input.source);
    const result = await window.mermaid.render(`luma_${input.id.replaceAll('-', '_')}`, input.source);
    document.body.innerHTML = result.svg;
    const svg = document.querySelector('svg');
    if (!svg || !svg.querySelector('title')?.textContent || !svg.querySelector('desc')?.textContent) {
      throw new Error('Diagram must have accessible title and description.');
    }
    if (svg.querySelector('script, foreignObject') || [...svg.querySelectorAll('*')].some(node =>
      [...node.attributes].some(attribute => /^on/i.test(attribute.name) ||
        (['href', 'src'].includes(attribute.localName) && /^(?:https?:|javascript:)/i.test(attribute.value))))) {
      throw new Error('Unexpected executable or external SVG content.');
    }
    const bounds = svg.viewBox.baseVal;
    if (!(bounds.width > 0 && bounds.height > 0) || bounds.width > 6000 || bounds.height > 6000) {
      throw new Error('Diagram has empty or excessive rendering bounds; split the view.');
    }
    // An explicit background preserves contrast in Markdown viewers using a dark theme.
    svg.style.backgroundColor = '#ffffff';
    return { svg: svg.outerHTML, width: Number(bounds.width.toFixed(2)), height: Number(bounds.height.toFixed(2)) };
  }, { id, source, theme });
  if (preview) {
    fs.mkdirSync(path.dirname(preview), { recursive: true });
    await page.locator('svg').screenshot({ path: preview });
  }
  return rendered;
}

module.exports = { rendererIdentity, withRenderer, renderDiagram };
