const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { chromium, expect } = require('@playwright/test');
const AxeBuilder=require('@axe-core/playwright').default;

/** Dispatch only this test tenant's queued message through a fresh real worker process, without any application debug route. */
function dispatchFixture(company) {
  const result=spawnSync(process.execPath,[path.resolve('scripts/python.cjs'),'-c',
    'import sys; from uuid import UUID; from luma_agent.runtime.delivery import deliver_one; assert deliver_one(UUID(sys.argv[1]))',company],
    {cwd:path.resolve('.'),encoding:'utf8',timeout:15000,windowsHide:true});
  if(result.status!==0)throw new Error('The isolated fixture dispatch did not complete.');
}

/** Normalize only the fixture company's queued voice note in a fresh native worker with paid inference disabled. */
function processMediaFixture(company, kind="audio") {
  const jobKind = kind === "audio" ? "transcribe" : "read_photo";
  const code = `import sys
from luma.core.database import database
from luma_agent.runtime.media import process_media
from luma_agent.runtime.jobs import finish_job
with database(worker=True) as conn:
    job=conn.execute("update luma.jobs set status='running',fence=fence+1,lease_until=now()+interval '120 seconds' where company_id=%s and kind=%s and status='queued' returning *",(sys.argv[1],sys.argv[2])).fetchone()
assert job
process_media(job,sys.argv[3])
finish_job(job,'done')`;
  const result=spawnSync(process.execPath,[path.resolve('scripts/python.cjs'),'-c',code,company,jobKind,kind],
    {cwd:path.resolve('.'),encoding:'utf8',timeout:25000,windowsHide:true,env:{...process.env,ENABLE_PAID_AI:'false',LANGSMITH_TRACING:'false'}});
  if(result.status!==0)throw new Error('The isolated voice processor did not complete.');
}

/** Construct a labeled one-second silent PCM fixture without depending on a microphone or external speech service. */
function syntheticVoice() {
  const buffer=Buffer.alloc(44+32000);
  buffer.write('RIFF',0);buffer.writeUInt32LE(buffer.length-8,4);buffer.write('WAVEfmt ',8);
  buffer.writeUInt32LE(16,16);buffer.writeUInt16LE(1,20);buffer.writeUInt16LE(1,22);
  buffer.writeUInt32LE(16000,24);buffer.writeUInt32LE(32000,28);buffer.writeUInt16LE(2,32);buffer.writeUInt16LE(16,34);
  buffer.write('data',36);buffer.writeUInt32LE(32000,40);return buffer;
}

/** Showcase recording (LUMA_RECORD_DIR set): wait so a viewer can read each step; a no-op for the normal test. */
const RECORDING = process.env.LUMA_RECORD_DIR || '';
const PRIVATE = [/\bsk-[A-Za-z0-9_-]{16,}/, /\blsv2_[A-Za-z0-9_-]{16,}/, /\bEAA[A-Za-z0-9]{20,}/, /\beyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}/, /[\w.+-]+@[\w-]+\.[\w.-]+/, /\+\d[\d \-().]{7,18}\d/];
/** Pause only while recording the walkthrough, and then scan the visible text for credentials, emails and phones. */
async function beat(page, milliseconds = 1400) {
  if (!RECORDING) return;
  await page.waitForTimeout(milliseconds);
  const text = await page.locator('body').innerText();
  PRIVATE.forEach((pattern, index) => { if (pattern.test(text)) throw new Error(`Private pattern ${index} is visible while recording.`); });
}

/** Exercise the actual staff UI against isolated native servers and a synthetic tenant; never record sign-in credentials. */
async function main() {
  const configuration = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch({ headless: true });
  /** Close the owned browser before the outer process deadline so failed checks cannot leave orphaned Chromium processes. */
  const deadline=setTimeout(function closeExpiredBrowser(){void browser.close()},RECORDING?240000:65000);
  const pdfs = new Set();
  const failures = [];
  let discardedVideo = null;
  try {
    const context = await browser.newContext({
      viewport: RECORDING ? { width: 1280, height: 800 } : { width: 1440, height: 1050 },
      reducedMotion: 'reduce',
      ...(RECORDING ? { recordVideo: { dir: RECORDING, size: { width: 1280, height: 800 } } } : {}),
    });
    // While recording, sign in on a throwaway page and hand its session to the recorded page, so neither
    // the fixture email nor the password field ever appears in the walkthrough video.
    let session = null;
    if (RECORDING) {
      const loginPage = await context.newPage();
      await loginPage.goto(configuration.url);
      await loginPage.getByLabel('Staff email').fill(configuration.email);
      await loginPage.getByLabel('Password', { exact: true }).fill(configuration.password);
      await loginPage.getByRole('button', { name: 'Open workspace' }).click();
      await loginPage.getByRole('heading', { name: 'A clearer path to every quote.' }).waitFor();
      session = await loginPage.evaluate(() => JSON.stringify(Object.fromEntries(Object.entries(sessionStorage))));
      discardedVideo = loginPage.video();
      await loginPage.close();
    }
    const page = await context.newPage();
    if (session) await page.addInitScript((stored) => { for (const [k, v] of Object.entries(JSON.parse(stored))) sessionStorage.setItem(k, v); }, session);
    /** Retain only bounded browser exception text, not request headers, session storage, or submitted form values. */
    page.on('pageerror', function browserFailure(error) { failures.push(error.message); });
    /** Fail on application console errors; the deliberately exercised stale-version HTTP 409 is the sole expected network rejection. */
    page.on('console', function consoleFailure(message) {
      if(message.type()!=='error') return;
      if(message.text().startsWith('Failed to load resource:') && message.text().includes('409')) return;
      failures.push('Unexpected application console error');
    });
    /** Track canonical documents generated by this scenario so the Python fixture can remove its own exact private objects. */
    page.on('response', function recordPrivateDocument(response) {
      const match = new URL(response.url()).pathname.match(/^\/api\/quotes\/([a-f0-9-]{36})\/pdf$/i);
      if (match && response.ok()) pdfs.add(match[1]);
    });
    await page.goto(configuration.url);
    if (!RECORDING) {
      await page.getByLabel('Staff email').fill(configuration.email);
      await page.getByLabel('Password', { exact: true }).fill(configuration.password);
      await page.getByRole('button', { name: 'Open workspace' }).click();
    }
    await page.getByRole('heading', { name: 'A clearer path to every quote.' }).waitFor();
    if (RECORDING) await page.getByRole('button', { name: 'Capture mode' }).click();
    await beat(page, 2500);
    await page.getByRole('link', { name: 'New request', exact: true }).click();
    await page.getByLabel('Customer name', { exact: true }).fill('Browser fixture customer');
    await page.getByLabel('Company', { exact: true }).fill('Browser test only');
    await page.getByLabel('Customer request', { exact: true }).fill('Please quote three DL-001 downlights. Synthetic browser test.');
    await page.getByRole('button', { name: 'Create local request' }).click();
    await page.getByRole('heading', { name: 'Quotation workspace' }).waitFor();
    const conversation = new URL(page.url()).pathname.split('/').pop();
    // Upload controls and document viewers are hidden in capture mode, so it is off while they are used (all data here is synthetic).
    if (RECORDING) await page.getByRole('button', { name: 'Capture mode' }).click();
    await beat(page);
    await page.getByLabel('Test customer voice note', {exact:true}).setInputFiles({name:'synthetic.wav',mimeType:'audio/wav',buffer:syntheticVoice()});
    await page.getByRole('button',{name:'Upload test voice note',exact:true}).click();
    await expect(page.locator('.message-list').getByText('Voice note awaiting processing.',{exact:true})).toBeVisible();
    processMediaFixture(configuration.company_id);
    await page.getByRole('button',{name:'Listen to voice note',exact:true}).click({timeout:15000});
    await expect(page.getByLabel('Voice note audio',{exact:true})).toHaveAttribute('src',/^blob:/);
    await beat(page);
    await page.getByRole('radio',{name:'Product-label photo attachment',exact:true}).click();
    await page.getByLabel('Test customer product-label photo',{exact:true}).setInputFiles(path.resolve('tests/fixtures/media/synthetic-label.png'));
    await page.getByRole('button',{name:'Upload test label photo',exact:true}).click();
    await expect(page.locator('.message-list').getByText('Product-label photo awaiting processing.',{exact:true})).toBeVisible();
    processMediaFixture(configuration.company_id,'image');
    await page.getByRole('button',{name:'View label photo',exact:true}).click({timeout:15000});
    await expect(page.getByAltText('Unconfirmed product-label photo',{exact:true})).toHaveAttribute('src',/^blob:/);
    await beat(page, 2000);
    await page.screenshot({path:'.local/photo-intake-desktop.png',fullPage:true});

    await page.getByLabel('Choose catalog product', { exact: true }).selectOption(configuration.product_id);
    await page.getByRole('button', { name: 'Add selected product' }).click();
    await page.getByLabel('Quantity for DL-001', { exact: true }).fill('3');
    await page.getByRole('button', { name: 'Save quotation revision' }).click();
    await expect(page.locator('.quote-grand-total')).toContainText('$97.05');
    await beat(page, 2500);
    await page.getByRole('button', { name: 'Take over', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Approve & queue delivery' })).toBeDisabled();
    await page.getByRole('radio',{name:'Customer reply mode',exact:true}).click();
    await page.getByRole('textbox',{name:'Customer reply',exact:true}).fill('Can you confirm the installation location? Synthetic staff clarification.');
    await page.getByRole('button',{name:'Queue customer reply',exact:true}).click();
    await expect(page.getByRole('status').filter({hasText:'Customer reply'})).toContainText('Queued');
    dispatchFixture(configuration.company_id);
    await expect(page.locator('.message-staff').filter({hasText:'Synthetic staff clarification.'})).toContainText('Sales team',{timeout:15000});
    await beat(page);
    await page.getByRole('radio',{name:'Internal staff note mode',exact:true}).click();
    await page.getByRole('button', { name: 'Resume agent', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Approve & queue delivery' })).toBeEnabled();

    // An actual background update must preserve the draft and its old precondition.
    await page.getByLabel('Quantity for DL-001', { exact: true }).fill('4');
    await page.getByRole('textbox', { name: 'Internal staff note', exact: true }).fill('Confirm specifications with the customer. Synthetic internal note.');
    await page.getByRole('button', { name: 'Add note', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'This request changed while you were editing.' })).toBeVisible();
    await page.getByRole('button', { name: 'Save quotation revision' }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'This request changed. Refresh before saving a revision.' })).toBeVisible();
    await beat(page, 2500);
    await expect(page.getByLabel('Quantity for DL-001', { exact: true })).toHaveValue('4');
    await page.screenshot({path:'.local/phase-2-stale-editor.png',fullPage:true});
    await page.getByRole('button', { name: 'Discard local edits & load latest' }).click();
    await expect(page.getByLabel('Quantity for DL-001', { exact: true })).toHaveValue('3');
    await page.getByLabel('Quantity for DL-001', { exact: true }).fill('4');
    await page.getByRole('button', { name: 'Save quotation revision' }).click();
    await expect(page.locator('.quote-grand-total')).toContainText('$129.40');
    await expect(page.locator('.quotation-panel > header')).toContainText('Revision 2');
    await beat(page, 2000);
    await page.getByRole('button', { name: 'View', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('dialog').locator('iframe')).toHaveAttribute('src', /^blob:/);
    await page.getByRole('button', { name: 'Close document' }).click();
    await page.getByRole('button', { name: 'View PDF', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('button', { name: 'Close document' }).click();
    if (RECORDING) await page.getByRole('button', { name: 'Capture mode' }).click();
    await page.getByRole('button', { name: 'Approve & queue delivery' }).click();
    await expect(page.locator('.delivery-summary')).toContainText('Queued');

    // Invoke only the fixture company's real worker dispatch; no debug/approval-
    // bypass endpoint is introduced into the application for this test.
    dispatchFixture(configuration.company_id);
    await expect(page.locator('.delivery-summary')).toContainText('Delivered in local test', { timeout: 15000 });
    await beat(page, 2500);
    await page.reload();
    await expect(page.locator('.delivery-summary')).toContainText('Delivered in local test');
    await expect(page.locator('.quote-grand-total')).toContainText('$129.40');
    const accessibility=await new AxeBuilder({page}).analyze();
    if(accessibility.violations.length)throw new Error('The working quotation flow has unresolved accessibility findings.');
    await page.screenshot({path:'.local/phase-2-delivered.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    const portrait=await new AxeBuilder({page}).analyze();
    if(portrait.violations.length)throw new Error('The portrait voice/quotation flow has unresolved accessibility findings.');
    const overflows=await page.evaluate(function inspectHorizontalBounds(){return document.documentElement.scrollWidth>window.innerWidth});
    if(overflows)throw new Error('The portrait workspace overflows horizontally.');
    await beat(page, 2500);
    await page.screenshot({path:'.local/phase-3-portrait.png',fullPage:true});
    if (failures.length) throw new Error('Unexpected browser exception during the working flow.');
    console.log(JSON.stringify({ conversation_id: conversation, canonical_pdf_ids: [...pdfs], checks: ['auth', 'intake', 'selection', 'canonical_totals', 'takeover', 'human_reply', 'stale_edit_preserved', 'revision', 'source_pdf', 'quotation_pdf', 'approval', 'scoped_dispatch', 'reload_persistence'] }));
  } finally {
    clearTimeout(deadline);
    await browser.close();
    if (RECORDING && discardedVideo) {
      try { fs.unlinkSync(await discardedVideo.path()); } catch (error) { /* the sign-in clip is best-effort removed */ }
    }
  }
}

/** Report bounded operational failures without serializing the private browser fixture configuration. */
main().catch(function failed(error) { console.error(error.message); process.exitCode = 1; });
