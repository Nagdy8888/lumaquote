const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');

/** Capture this local stack's CLI configuration into an ignored environment override without printing credentials. */
function main() {
  const cli = path.join(root, 'node_modules/supabase/dist/supabase.js');
  const result = spawnSync(process.execPath, [cli, 'status', '--output', 'json'], { cwd: root, encoding: 'utf8', windowsHide: true });
  if (result.status !== 0) throw new Error('Start this project with npm run db:start before generating its local configuration.');
  const values = JSON.parse(result.stdout);
  const api = values.API_URL, database = values.DB_URL;
  if (api !== 'http://127.0.0.1:55321' || !/^postgresql:\/\/[^@]+@127\.0\.0\.1:55322\//.test(database)) throw new Error('Refusing a configuration outside this project\'s loopback stack.');
  const selected = { SUPABASE_URL: api, SUPABASE_ANON_KEY: values.ANON_KEY, SUPABASE_SERVICE_ROLE_KEY: values.SERVICE_ROLE_KEY,
    DATABASE_URL: database, VITE_SUPABASE_URL: api, VITE_SUPABASE_ANON_KEY: values.ANON_KEY };
  if (Object.values(selected).some(value => typeof value !== 'string' || !value)) throw new Error('The local CLI response is missing required connection fields.');
  const target = path.join(root, '.env.local');
  let text = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : '';
  for (const [key, value] of Object.entries(selected)) {
    const line = `${key}='${value.replaceAll("'", "\\'")}'`;
    const expression = new RegExp(`^${key}=.*$`, 'm');
    text = expression.test(text) ? text.replace(expression, line) : `${text.trimEnd()}\n${line}\n`;
  }
  fs.writeFileSync(target, text.trimStart(), { mode: 0o600 });
  console.log('Local Supabase settings saved to ignored .env.local; no credentials printed.');
}
/** Surface a bounded setup failure without exposing the captured CLI output. */
try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
