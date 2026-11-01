const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { existingFile, fingerprint, embeddedBlock, replaceEmbedded } = require('./catalog.cjs');

/** Verify temporary fixture cleanup without deleting any application data or developer work. */
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'luma-diagram-test-'));
  t.after(/** Remove only the verified owned temporary fixture directory. */ function cleanupFixture() {
    const target = fs.realpathSync(root), temporary = fs.realpathSync(os.tmpdir());
    if (!target.startsWith(temporary + path.sep) || !path.basename(target).startsWith('luma-diagram-test-')) {
      throw new Error('Refusing cleanup outside the owned diagram fixture.');
    }
    fs.rmSync(target, { recursive: true, force: true });
  });
  fs.mkdirSync(path.join(root, 'docs/diagrams'), { recursive: true });
  fs.writeFileSync(path.join(root, 'docs/diagrams/example.mmd'), 'flowchart LR\n A --> B\n');
  fs.writeFileSync(path.join(root, 'contract.py'), 'value = 1\n');
  return { root, entry: { id: 'example', title: 'Example contract', bindings: ['contract.py'] } };
}

test('a source or bound-code change invalidates freshness independently', function freshness(t) {
  /** Exercise source/code fingerprints with real fixture files rather than matching instruction wording. */
  const { root, entry } = fixture(t);
  const initial = fingerprint(root, entry, 'renderer-v1');
  fs.writeFileSync(path.join(root, 'contract.py'), 'value = 1\r\n');
  assert.deepEqual(initial.bindings, fingerprint(root, entry, 'renderer-v1').bindings);
  fs.writeFileSync(path.join(root, 'contract.py'), 'value = 2\n');
  const changed = fingerprint(root, entry, 'renderer-v1');
  assert.equal(initial.source_sha256, changed.source_sha256);
  assert.notDeepEqual(initial.bindings, changed.bindings);
  fs.appendFileSync(path.join(root, 'docs/diagrams/example.mmd'), ' B --> C\n');
  assert.notEqual(changed.source_sha256, fingerprint(root, entry, 'renderer-v1').source_sha256);
});

test('owned embeds preserve prose and reject missing or duplicated markers', function embeds() {
  /** Prevent generated diagram updates from silently replacing unrelated guide content. */
  const entry = { id: 'example', title: 'Example contract' };
  const block = embeddedBlock(entry, 'flowchart LR\n A --> B', 'docs/reference/EXAMPLE.md');
  assert.match(block, /\.\.\/diagrams\/rendered\/example\.svg/);
  const current = 'Before\n<!-- diagram:example:start -->old<!-- diagram:example:end -->\nAfter';
  assert.equal(replaceEmbedded(current, entry, block), `Before\n${block}\nAfter`);
  assert.throws(() => replaceEmbedded('Missing', entry, block), /Missing or duplicate/);
  assert.throws(() => replaceEmbedded(current + current, entry, block), /Missing or duplicate/);
});

test('catalog bindings cannot escape the repository root', function boundaries(t) {
  /** Reject traversal/absolute paths before reading arbitrary local files. */
  const { root } = fixture(t);
  assert.throws(() => existingFile(root, path.resolve(root, 'contract.py')), /repository-relative/);
  assert.throws(() => existingFile(root, '../'), /outside the repository|not a file/);
  assert.equal(existingFile(root, 'contract.py'), path.join(root, 'contract.py'));
});

test('state label statement delimiters cannot silently create extra nodes', function stateLabels(t) {
  /** Catch the observed render-valid stray-node regression before it enters a guide. */
  const { root, entry } = fixture(t);
  fs.writeFileSync(path.join(root, 'docs/diagrams/example.mmd'), 'stateDiagram-v2\n A --> B: Edit; preserve draft\n');
  assert.throws(() => fingerprint(root, entry, 'renderer-v1'), /statement delimiters/);
});
