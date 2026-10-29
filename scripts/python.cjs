const { spawn } = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const executable = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');

/** Run a native project Python command with both application packages importable; inherit no custom shell. */
function run() {
  const pythonPath = [path.join(root, 'app/backend'), path.join(root, 'app/agents')].join(path.delimiter);
  const child = spawn(executable, process.argv.slice(2), {
    cwd: root, stdio: 'inherit', windowsHide: true, env: { ...process.env, PYTHONPATH: pythonPath },
  });
  /** Mirror completion so callers and CI see the Python command's actual result. */
  child.on('exit', function finish(code) { process.exitCode = code ?? 1; });
  /** Report a bounded startup failure without dumping environment credentials. */
  child.on('error', function failed(error) { console.error(`Python did not start: ${error.code}`); process.exitCode = 1; });
}
run();
