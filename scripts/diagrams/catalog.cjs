const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

/** Return a stable UTF-8/byte digest for source and generated artifact integrity. */
function hash(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

/** Resolve an existing repository file and reject traversal or symlinks outside the repository. */
function existingFile(root, relative) {
  if (path.isAbsolute(relative)) throw new Error('Diagram paths must be repository-relative.');
  const target = path.resolve(root, relative);
  const inside = path.relative(fs.realpathSync(root), fs.realpathSync(target));
  if (!inside || inside.startsWith('..') || path.isAbsolute(inside) || !fs.statSync(target).isFile()) {
    throw new Error(`Diagram file is outside the repository or is not a file: ${relative}`);
  }
  return target;
}

/** Read the fixed diagram inventory, checking identities, owned paths, embeds and actual code bindings. */
function readCatalog(root) {
  const catalog = JSON.parse(fs.readFileSync(path.join(root, 'docs/diagrams/catalog.json'), 'utf8'));
  if (catalog.version !== 1 || !Array.isArray(catalog.diagrams) || !catalog.diagrams.length) {
    throw new Error('Unsupported or empty diagram catalog.');
  }
  const ids = new Set();
  for (const entry of catalog.diagrams) {
    if (!/^[a-z][a-z0-9-]+$/.test(entry.id) || ids.has(entry.id)) throw new Error('Duplicate or invalid diagram ID.');
    ids.add(entry.id);
    if (!entry.title || !entry.scope || !entry.bindings?.length || !entry.embeds?.length) {
      throw new Error(`Missing diagram purpose, bindings or embed: ${entry.id}`);
    }
    existingFile(root, `docs/diagrams/${entry.id}.mmd`);
    for (const file of [...entry.bindings, ...entry.embeds]) existingFile(root, file);
  }
  const actual = fs.readdirSync(path.join(root, 'docs/diagrams')).filter(file => file.endsWith('.mmd'));
  if (actual.length !== ids.size || actual.some(file => !ids.has(file.slice(0, -4)))) {
    throw new Error('Every canonical Mermaid source must appear exactly once in the catalog.');
  }
  return catalog.diagrams;
}

/** Describe source/code freshness separately from stored SVG bytes; no hash proves a diagram is semantically correct. */
function fingerprint(root, entry, rendererHash) {
  const source = fs.readFileSync(existingFile(root, `docs/diagrams/${entry.id}.mmd`), 'utf8').replaceAll('\r\n', '\n').trim();
  if (/^(sequenceDiagram|stateDiagram)/.test(source) && source.split('\n').some(line => /->/.test(line) && line.includes(';'))) {
    throw new Error(`Avoid statement delimiters in state/sequence labels: ${entry.id}`);
  }
  const bindings = Object.fromEntries(entry.bindings.map(file => [file, hash(fs.readFileSync(existingFile(root, file), 'utf8').replaceAll('\r\n', '\n'))]));
  return { source, source_sha256: hash(source), bindings, renderer_sha256: rendererHash };
}

/** Build one deterministic native Mermaid/details and static SVG block relative to its owning guide. */
function embeddedBlock(entry, source, guide) {
  const prefix = path.posix.relative(path.posix.dirname(guide), 'docs/diagrams');
  const base = prefix ? `${prefix}/` : '';
  return `<!-- diagram:${entry.id}:start -->\n` +
    `![${entry.title}](${base}rendered/${entry.id}.svg)\n\n` +
    `[Open full-size SVG](${base}rendered/${entry.id}.svg) · [Editable Mermaid](${base}${entry.id}.mmd)\n\n` +
    `<details>\n<summary>Mermaid source</summary>\n\n\`\`\`mermaid\n${source}\n\`\`\`\n\n</details>\n` +
    `<!-- diagram:${entry.id}:end -->`;
}

/** Replace only one explicitly owned block; absence or ambiguity requires a deliberate documentation edit. */
function replaceEmbedded(document, entry, block) {
  const start = `<!-- diagram:${entry.id}:start -->`;
  const end = `<!-- diagram:${entry.id}:end -->`;
  const first = document.indexOf(start), last = document.indexOf(end);
  if (first < 0 || last < first || document.indexOf(start, first + 1) !== -1 || document.indexOf(end, last + 1) !== -1) {
    throw new Error(`Missing or duplicate diagram embed markers: ${entry.id}`);
  }
  return document.slice(0, first) + block + document.slice(last + end.length);
}

module.exports = { hash, existingFile, readCatalog, fingerprint, embeddedBlock, replaceEmbedded };
