const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');

/** Run the documented real checks, persist private logs, and stop at the first failing gate. */
function main() {
  const full = process.argv.includes('--full');
  const npm = process.env.npm_execpath;
  if (!npm) throw new Error('Use npm run verify or npm run verify:full so the actual package-manager entrypoint is known.');
  const directory = path.join(root, '.local', 'checks');
  fs.mkdirSync(directory, { recursive: true });
  const commands = ['lint:python', 'check:architecture', 'check:frontend', 'test:diagrams', 'diagrams:check', 'typecheck', full ? 'test:python' : 'test:unit', 'test:ui', ...(full?['test:browser']:[]), 'build'];
  const summary = [];
  for (const command of commands) {
    const start = Date.now();
    // Real Auth/Storage/sandbox/process-restart coverage needs a separate bounded integration-suite budget.
    const timeout = command === 'test:python' ? 420000 : 180000;
    const result = spawnSync(process.execPath, [npm, 'run', command], { cwd: root, encoding: 'utf8', windowsHide: true, timeout });
    const log = `${command.replaceAll(':', '-')}.log`;
    fs.writeFileSync(path.join(directory, log), (result.stdout ?? '') + (result.stderr ?? ''));
    const passed = !result.error && result.status === 0;
    summary.push({ command: `npm run ${command}`, status: passed ? 'Passed' : 'Failed', seconds: Number(((Date.now()-start)/1000).toFixed(2)), timeout_seconds: timeout / 1000, error_code: result.error?.code ?? null, local_log: `.local/checks/${log}` });
    console.log(`${passed ? 'Passed' : 'Failed'}: ${command}`);
    fs.writeFileSync(path.join(directory, 'summary.json'), JSON.stringify({ scope: full ? 'Local full foundation checks' : 'Offline checks', results: summary }, null, 2));
    if (!passed) throw new Error(`Check failed: ${command}. Inspect its ignored local log before continuing.`);
  }
}
/** Keep failure output bounded; full logs remain local and are reviewed before promotion to evidence. */
try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
