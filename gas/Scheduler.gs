/**
 * One minute trigger for every Apps Script task (decision D50).
 *
 * Before D50 four time-driven triggers (mail poll, mail send, supplier sync, Drive and stock export) fired at
 * about the same second and shared one script lock. Each waited up to 25 s for it, so most runs failed with a
 * lock timeout. Now exactly one trigger, `runLumaMinute`, takes the lock once and runs the tasks in sequence.
 * The tasks themselves are lock-free functions with a trailing underscore (`pollLumaMail_`, ...); the public
 * names (`pollLumaMail`, `sendLumaMail`, `synchronizeSupplierWorkbook`, `exportApprovedQuotations`) stay as
 * manual entry points that take the lock themselves. The on-edit trigger `notifySupplierEdit` is separate.
 */

/**
 * How long a manual entry point (or the on-edit handler) waits for the shared script lock. The minute run
 * holds it for the length of its tasks (about 10 to 30 s), so this must exceed a normal run.
 */
var LOCK_WAIT_MS = 25000;

/** How long `runLumaMinute` waits for the lock: zero-ish, so a run that overlaps the previous one skips its minute. */
var MINUTE_LOCK_WAIT_MS = 1000;

/**
 * Time budget of one minute run. Apps Script stops an execution at 6 minutes, so no new task starts after
 * 4.5 minutes; the last task that started may still use the remaining margin. Each task is itself bounded
 * (mail: 5 mails, 4 search pages, 3 sends; export: 3 PDFs and 1 stock export; sync: 3 tables of at most 1000 rows).
 */
var MINUTE_BUDGET_MS = 270000;

/** Handlers of every time-driven trigger this project used; the installer removes all of them before creating its own. */
var MINUTE_TRIGGER_HANDLERS = ['runLumaMinute', 'pollLumaMail', 'sendLumaMail', 'synchronizeSupplierWorkbook',
  'exportApprovedQuotations'];

/**
 * Run one task under the shared script lock, waiting up to LOCK_WAIT_MS; a timeout throws so the run shows as
 * Failed. Releases the lock even when the task throws. Used only by the manual entry points.
 */
function withScriptLock_(task) {
  var lock = LockService.getScriptLock();
  lock.waitLock(LOCK_WAIT_MS);
  try {
    task();
  } finally {
    lock.releaseLock();
  }
}

/**
 * The tasks of one minute, in order: mail poll (customer replies first), mail send, supplier synchronization,
 * Drive and stock export. Each entry is a lock-free function that takes the resolved configuration.
 */
function minuteTasks_() {
  return [
    { name: 'pollLumaMail', run: pollLumaMail_ },
    { name: 'sendLumaMail', run: sendLumaMail_ },
    { name: 'synchronizeSupplierWorkbook', run: synchronizeSupplierWorkbook_ },
    { name: 'exportApprovedQuotations', run: exportApprovedQuotations_ }
  ];
}

/**
 * Minute timer (the only time-driven trigger). Takes the script lock once with a short tryLock and skips the
 * minute, without an error, when the previous run still holds it. Runs the tasks of `minuteTasks_` in order;
 * each is in its own try/catch so one failure never skips the rest. Stops starting tasks after
 * MINUTE_BUDGET_MS (the skipped task names are logged and they run first next minute only by order, so a task
 * that always overruns would starve later ones; the log shows it). After the last task the first error is
 * rethrown so the run shows as Failed; only task names and the error's own message are logged, never mail or
 * quotation content. The backend owns retries; every task is idempotent against its own claim or cursor.
 */
function runLumaMinute() {
  var started = Date.now();
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(MINUTE_LOCK_WAIT_MS)) {
    console.log('Skipped: the previous minute run still holds the script lock.');
    return;
  }
  var failed = [];
  var skipped = [];
  var firstError = null;
  try {
    var config = configuration_();
    minuteTasks_().forEach(function runTask_(task) {
      /** Run one task unless the time budget is spent; record its failure and keep going. */
      if (Date.now() - started > MINUTE_BUDGET_MS) {
        skipped.push(task.name);
        return;
      }
      try {
        task.run(config);
      } catch (error) {
        failed.push(task.name);
        firstError = firstError || error;
        console.error(task.name + ' failed: ' + String(error && error.message));
      }
    });
  } finally {
    lock.releaseLock();
  }
  if (skipped.length) console.warn('Time budget spent; skipped: ' + skipped.join(', '));
  if (firstError) throw firstError;
}

/**
 * Install the single one-minute trigger: delete every project trigger whose handler is `runLumaMinute` or one of
 * the four old per-task handlers, then create one `runLumaMinute` every-minute trigger. Leaves other triggers
 * (the on-edit `notifySupplierEdit`) alone. Needs the Script Properties to be complete. Takes no lock: trigger
 * changes touch no shared data, and a second concurrent installer would only create a duplicate whose run skips
 * its minute at the tryLock. Run once in the editor; every older installer calls this function.
 */
function installLumaMinute() {
  configuration_();
  ScriptApp.getProjectTriggers().forEach(function removeMinuteTrigger_(trigger) {
    /** Replace only this project's own time-driven handlers. */
    if (MINUTE_TRIGGER_HANDLERS.indexOf(trigger.getHandlerFunction()) >= 0) ScriptApp.deleteTrigger(trigger);
  });
  ScriptApp.newTrigger('runLumaMinute').timeBased().everyMinutes(1).create();
}
