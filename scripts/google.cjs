const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');

/** Run only the selected project's clasp operations without shell interpolation or credential output. */
function main() {
  const operation = process.argv[2];
  const configPath = path.join(root, '.clasp.json');
  if (!fs.existsSync(configPath)) throw new Error('Link the intended Apps Script project first; see docs/MORNING_ACTIONS.md.');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  if (!/^[A-Za-z0-9_-]{20,150}$/.test(config.scriptId)) throw new Error('Invalid project mapping.');
  const argumentsByOperation = {
    status: ['status'], push: ['push'],
    initialize: ['run-function', 'initializeSyntheticWorkbook', '--params', JSON.stringify([config.parentId]), '--json'],
    'install-trigger': ['run-function', 'installSupplierEditTrigger', '--json'],
  };
  const args = argumentsByOperation[operation];
  if (!args) throw new Error('Choose status, push, initialize, or install-trigger.');
  const executable = path.join(root, 'node_modules/@google/clasp/build/src/index.js');
  const result = spawnSync(process.execPath, [executable, ...args], { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 60000 });
  if (result.error || result.status !== 0) throw new Error(`clasp ${operation} did not complete; check account authorization and the project mapping.`);
  if (operation === 'initialize' || operation === 'install-trigger') {
    let value;
    try { value = JSON.parse(result.stdout); } catch { throw new Error('clasp execution returned an unrecognized result; no successful execution is claimed.'); }
    fs.mkdirSync(path.join(root, '.local'), { recursive: true });
    fs.writeFileSync(path.join(root, '.local', `clasp-${operation}-result.json`), JSON.stringify(value, null, 2));
    if (value.error) throw new Error(`Google returned an application-level error for ${operation}; private details are in .local/clasp-${operation}-result.json.`);
    console.log(`Apps Script ${operation} completed without a reported execution error.`);
  } else console.log(result.stdout.trim());
}
/** Report only safe actionable status; never include the child environment, OAuth token, or raw provider errors. */
try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
