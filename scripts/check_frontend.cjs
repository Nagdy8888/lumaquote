/** Check inline contracts, dependency direction, and import cycles in the actual frontend source. */
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const root = path.resolve(__dirname, '../app/frontend/src');

/** Enumerate source files while ignoring generated API declarations owned by the schema generator. */
function sources(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(function visit(entry) {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? sources(target) : /\.[cm]?[jt]sx?$/.test(entry.name) && entry.name !== 'generated.ts' ? [target] : [];
  });
}

/** Find the closest stable authored name for a documented function/class contract. */
function definitionName(node) {
  if (ts.isFunctionDeclaration(node) || ts.isClassDeclaration(node) || ts.isMethodDeclaration(node)) return node.name?.getText();
  if (ts.isConstructorDeclaration(node)) return 'constructor';
  if (ts.isFunctionExpression(node) && node.name) return node.name.getText();
  if (ts.isArrowFunction(node) && ts.isVariableDeclaration(node.parent)) return node.parent.name.getText();
  return undefined;
}

/** Resolve only local TypeScript modules; third-party packages and CSS are outside the source import graph. */
function resolveImport(file, specifier) {
  if (!specifier.startsWith('.') && !specifier.startsWith('@/')) return null;
  const base = specifier.startsWith('@/') ? path.join(root, specifier.slice(2)) : path.resolve(path.dirname(file), specifier);
  return [base, `${base}.ts`, `${base}.tsx`, path.join(base, 'index.ts'), path.join(base, 'index.tsx')].find(candidate => fs.existsSync(candidate) && fs.statSync(candidate).isFile() && /\.tsx?$/.test(candidate)) ?? null;
}

/** Inspect definitions and dependencies, returning actionable file/line failures without arbitrary file-size limits. */
function inspect(file) {
  const source = ts.createSourceFile(file, fs.readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true);
  const errors = [], imports = [];
  /** Recursively inspect authored declarations and collect local dependency edges. */
  function walk(node) {
    const name = definitionName(node);
    if (name && ts.getJSDocCommentsAndTags(node).length === 0) {
      const position = source.getLineAndCharacterOfPosition(node.getStart(source));
      errors.push(`${path.relative(root, file)}:${position.line + 1}: ${name} needs an inline JSDoc contract`);
    }
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      const specifier = node.moduleSpecifier.text;
      if (file.includes(`${path.sep}shared${path.sep}`) && specifier.startsWith('@/features/')) errors.push(`${file}: shared code cannot import feature implementation`);
      const resolved = resolveImport(file, specifier);
      if (resolved) imports.push(resolved);
    }
    ts.forEachChild(node, walk);
  }
  walk(source);
  return { errors, imports };
}

/** Reject circular imports and missing contracts so the growing UI remains navigable and locally understandable. */
function main() {
  const files = sources(root), graph = new Map(), errors = [];
  for (const file of files) { const result = inspect(file); graph.set(file, result.imports); errors.push(...result.errors); }
  const visited = new Set(), active = new Set();
  /** Walk the module graph and report an actual cycle only when an active ancestor is re-entered. */
  function visit(file, ancestors = []) {
    if (active.has(file)) { errors.push(`Import cycle: ${[...ancestors, file].map(value => path.relative(root, value)).join(' -> ')}`); return; }
    if (visited.has(file)) return;
    active.add(file);
    for (const dependency of graph.get(file) ?? []) visit(dependency, [...ancestors, file]);
    active.delete(file); visited.add(file);
  }
  for (const file of files) visit(file);
  if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
  else console.log(`Frontend contracts and import checks passed for ${files.length} modules.`);
}
main();
