const fs = require('node:fs');
const path = require('node:path');
const { hash, readCatalog, fingerprint, embeddedBlock, replaceEmbedded } = require('./catalog.cjs');
const { rendererIdentity, withRenderer, renderDiagram } = require('./render.cjs');
const root = path.resolve(__dirname, '../..');

/** Generate or verify all canonical sources, exact guide embeds and source/code-bound SVG assets; check mode never repairs files. */
async function main() {
  const mode = process.argv[2];
  if (!['render', 'check'].includes(mode)) throw new Error('Choose diagrams render or check.');
  const entries = readCatalog(root), renderer = rendererIdentity();
  const directory = path.join(root, 'docs/diagrams/rendered');
  const manifestPath = path.join(directory, 'manifest.json');
  const previous = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {};
  const manifest = { version: 1, mermaid_version: renderer.version, diagrams: {} };
  await withRenderer(/** Process the bounded inventory sequentially so graph IDs and guide writes remain deterministic. */ async function processDiagrams(page) {
    for (const entry of entries) {
      const input = fingerprint(root, entry, renderer.hash);
      for (const guide of entry.embeds) {
        const file = path.join(root, guide), current = fs.readFileSync(file, 'utf8');
        const expected = replaceEmbedded(current, entry, embeddedBlock(entry, input.source, guide));
        if (mode === 'render') fs.writeFileSync(file, expected);
        else if (current !== expected) throw new Error(`Stale Mermaid/preview embed: ${guide} (${entry.id})`);
      }
      const output = path.join(directory, `${entry.id}.svg`);
      if (mode === 'check') {
        const stored = previous.diagrams?.[entry.id];
        if (!stored || stored.source_sha256 !== input.source_sha256 || stored.renderer_sha256 !== input.renderer_sha256 ||
            JSON.stringify(stored.bindings) !== JSON.stringify(input.bindings) || !fs.existsSync(output) ||
            hash(fs.readFileSync(output)) !== stored.svg_sha256) {
          throw new Error(`Stale or missing diagram asset/binding: ${entry.id}. Review code and run npm run diagrams:render.`);
        }
      }
      const result = await renderDiagram(page, entry.id, input.source,
        mode === 'render' ? path.join(root, '.local/diagram-previews', `${entry.id}.png`) : null);
      if (mode === 'render') {
        fs.mkdirSync(directory, { recursive: true });
        fs.writeFileSync(output, result.svg);
      }
      manifest.diagrams[entry.id] = {
        source_sha256: input.source_sha256, renderer_sha256: input.renderer_sha256,
        bindings: input.bindings, svg_sha256: hash(mode === 'render' ? result.svg : fs.readFileSync(output)),
        width: result.width, height: result.height,
      };
      console.log(`${mode === 'render' ? 'Rendered' : 'Verified'}: ${entry.id}`);
    }
  });
  if (mode === 'render') fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  else if (previous.mermaid_version !== renderer.version || Object.keys(previous.diagrams || {}).length !== entries.length) {
    throw new Error('Diagram manifest engine/inventory does not match current catalog.');
  }
  console.log(`Passed: ${entries.length} locally rendered Mermaid diagrams, guide embeds and SVG freshness checks.`);
}

/** Report bounded rendering failures without logging local environment or private application data. */
if (require.main === module) main().catch(function failed(error) { console.error(error.message.slice(0, 1200)); process.exitCode = 1; });

module.exports = { main };
