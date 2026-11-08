/** Read bounded input tables with exact unique headers; reject formulas and serialize dates as calendar dates. */
function readSupplierTable_(book, name) {
  var sheet = book.getSheetByName(name);
  if (!sheet || sheet.getLastRow() < 2 || sheet.getLastRow() > 1001 || sheet.getLastColumn() > 12) {
    throw new Error('Missing or oversized supplier input table: ' + name);
  }
  var range = sheet.getRange(1, 1, sheet.getLastRow(), sheet.getLastColumn());
  var formulas = range.getFormulas();
  for (var r = 0; r < formulas.length; r++) {
    for (var c = 0; c < formulas[r].length; c++) {
      if (formulas[r][c]) throw new Error('Supplier input tables must contain values, not formulas.');
    }
  }
  var values = range.getValues();
  var headers = values.shift();
  var seen = {};
  headers.forEach(function validateHeader_(header) {
    /** Disallow duplicate or unsafe keys before building serialized supplier records. */
    if (typeof header !== 'string' || !/^[a-z][a-z0-9_]*$/.test(header) || seen[header]) {
      throw new Error('Invalid or duplicate supplier table header.');
    }
    seen[header] = true;
  });
  return values.map(function serializeRow_(row) {
    /** Retain primitive input types and serialize Sheet dates using the workbook timezone. */
    var record = {};
    headers.forEach(function assignCell_(header, column) {
      /** Normalize money as decimal text to avoid binary-floating-point arithmetic in the backend. */
      var value = row[column];
      if (value instanceof Date) value = Utilities.formatDate(value, book.getSpreadsheetTimeZone(), 'yyyy-MM-dd');
      if (header === 'unit_price') value = String(value);
      record[header] = value;
    });
    return record;
  });
}

/** Push one complete signed snapshot under a script lock; failure never reports fresh commercial data. */
function synchronizeSupplierWorkbook() {
  var config = configuration_();
  var lock = LockService.getScriptLock();
  lock.waitLock(LOCK_WAIT_MS);
  try {
    var book = SpreadsheetApp.openById(config.spreadsheetId);
    var tables = {};
    ['Products', 'Prices', 'Policies'].forEach(function collectTable_(name) {
      /** Read only the three configured supplier input tables (stock is owned by the web app, D49), never quotation/customer tabs. */
      tables[name] = readSupplierTable_(book, name);
    });
    ['Products', 'Prices', 'Policies'].forEach(function confirmStableRead_(name) {
      /** Detect edits across the sequential table reads; retry on the next trigger instead of pushing mixed records. */
      if (JSON.stringify(tables[name]) !== JSON.stringify(readSupplierTable_(book, name))) {
        throw new Error('Supplier tables changed during synchronization; retry after the edit completes.');
      }
    });
    var payload = JSON.stringify({ schema_version: 1, company_id: config.companyId,
      spreadsheet_id: config.spreadsheetId, timestamp: Math.floor(Date.now() / 1000),
      nonce: Utilities.getUuid(), event: 'supplier_snapshot', tables: tables });
    if (Utilities.newBlob(payload).getBytes().length > 524288) throw new Error('Supplier snapshot exceeds 512 KiB.');
    var response = UrlFetchApp.fetch(config.callbackUrl + '/snapshot', {
      method: 'post', contentType: 'application/json', payload: payload,
      headers: { 'X-Luma-Signature': signPayload_(payload, config.secret) },
      followRedirects: false, muteHttpExceptions: true
    });
    PropertiesService.getScriptProperties().setProperty('LUMA_LAST_SNAPSHOT_STATUS', String(response.getResponseCode()));
    if (response.getResponseCode() !== 202) throw new Error('Supplier snapshot rejected; check backend validation and connection.');
    PropertiesService.getScriptProperties().setProperty('LUMA_LAST_SNAPSHOT_AT', new Date().toISOString());
    console.log('Supplier snapshot accepted by backend validation.');
  } finally {
    lock.releaseLock();
  }
}

/** Validate an initial snapshot, then install one one-minute reconciliation trigger without changing other handlers. */
function installSupplierSynchronization() {
  synchronizeSupplierWorkbook();
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    ScriptApp.getProjectTriggers().forEach(function removeDuplicateSync_(trigger) {
      /** Replace only this account's owned periodic supplier synchronization triggers. */
      if (trigger.getHandlerFunction() === 'synchronizeSupplierWorkbook') ScriptApp.deleteTrigger(trigger);
    });
    ScriptApp.newTrigger('synchronizeSupplierWorkbook').timeBased().everyMinutes(1).create();
  } finally {
    lock.releaseLock();
  }
}
