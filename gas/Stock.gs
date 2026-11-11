/**
 * Stock export to Google Sheets (decision D49, task T5). The web app is the stock master; this file only
 * copies a read-only view of it into three tabs of the configured workbook when a staff member presses
 * "Export to Google Sheets". Backend contract: docs/reference/GOOGLE_SYNC.md and docs/reference/INVENTORY.md.
 *
 * Safety rules:
 * - Only the tabs in STOCK_TABS are ever written. Products, Prices, Policies, Inventory and Quote Register
 *   are never touched.
 * - Text columns get the plain-text number format "@" BEFORE the values are written, so a value that starts
 *   with an apostrophe, equals sign, plus, minus or at sign (the backend already neutralizes these) is shown
 *   as text and never evaluated as a formula.
 * - Logs and Script Properties hold status codes and short error codes only, never cell contents.
 */

var STOCK_TABS = ['Stock', 'Customer Orders', 'Purchase Orders'];

/** Bold the header row and freeze it, the same look on every exported tab. */
function styleStockHeader_(sheet, columns) {
  sheet.getRange(1, 1, 1, columns).setFontWeight('bold');
  sheet.setFrozenRows(1);
}

/** Return true when any data row has a non-empty string in this column, which makes it a text column. */
function isTextColumn_(values, column) {
  for (var r = 1; r < values.length; r++) {
    if (typeof values[r][column] === 'string' && values[r][column] !== '') return true;
  }
  return false;
}

/** Check one tab's values are a non-empty rectangular grid of strings and numbers; throws a code-only error. */
function validateStockTab_(values) {
  if (!Array.isArray(values) || values.length < 1 || !Array.isArray(values[0]) || values[0].length < 1) {
    throw new Error('bad_response');
  }
  var width = values[0].length;
  values.forEach(function checkRow_(row) {
    /** Every row must have the header's width and hold only strings or numbers. */
    if (!Array.isArray(row) || row.length !== width) throw new Error('bad_response');
    row.forEach(function checkCell_(cell) {
      /** Reject anything Apps Script could interpret beyond plain text and numbers. */
      if (typeof cell !== 'string' && typeof cell !== 'number') throw new Error('bad_response');
    });
  });
}

/** Replace one export tab: create it when missing, format text columns as plain text, write the values. */
function writeStockTab_(book, name, values) {
  if (STOCK_TABS.indexOf(name) < 0) throw new Error('bad_response');
  var sheet = book.getSheetByName(name) || book.insertSheet(name);
  sheet.clearContents();
  var rows = values.length;
  var columns = values[0].length;
  for (var c = 0; c < columns; c++) {
    var header = String(values[0][c]);
    var format = isTextColumn_(values, c) || rows === 1 ? '@' : (/price|total|cost/.test(header) ? '#,##0.00' : '0');
    sheet.getRange(1, c + 1, rows, 1).setNumberFormat(format);
  }
  sheet.getRange(1, 1, rows, columns).setValues(values);
  styleStockHeader_(sheet, columns);
  sheet.autoResizeColumns(1, columns);
}

/** POST the signed outcome of one claimed stock export; returns true when the backend accepted it (HTTP 200). */
function stockReceipt_(config, claimed, fields) {
  var base = { event: 'stock_export_receipt', export_id: claimed.export_id, claim_token: claimed.claim_token };
  Object.keys(fields).forEach(function copyField_(key) {
    /** Add only the outcome-specific fields. */
    base[key] = fields[key];
  });
  var receipt = signedExportPost_(config, '/stock/receipt', base);
  PropertiesService.getScriptProperties().setProperty('LUMA_LAST_STOCK_EXPORT_STATUS', String(receipt.status));
  return receipt.status === 200;
}

/**
 * Claim at most one queued stock export and write its three tabs; the caller holds the shared script lock.
 * Posts a stored receipt with the data row count per tab, or a failed receipt with a short code
 * (bad_response, sheet_error). Throws only when the claim itself is refused. Returns true when an export was written.
 */
function exportStockTabs_(config) {
  var claim = signedExportPost_(config, '/stock/claim', { event: 'stock_export_claim' });
  if (claim.status !== 200) {
    PropertiesService.getScriptProperties().setProperty('LUMA_LAST_STOCK_EXPORT_STATUS', String(claim.status));
    throw new Error('Stock export claim was not accepted; check backend configuration and the connection.');
  }
  var claimed = claim.body;
  if (!claimed || claimed.status !== 'claimed') return false;
  var errorCode = null;
  try {
    var counts = {};
    STOCK_TABS.forEach(function check_(name) {
      /** All three tabs must be present and well formed before any tab is written. */
      validateStockTab_(claimed.tabs && claimed.tabs[name]);
    });
    var book = SpreadsheetApp.openById(config.spreadsheetId);
    STOCK_TABS.forEach(function write_(name) {
      /** Write one tab and count its data rows (the header is not counted). */
      writeStockTab_(book, name, claimed.tabs[name]);
      counts[name] = claimed.tabs[name].length - 1;
    });
    SpreadsheetApp.flush();
    if (claimed.truncated && claimed.truncated.length) console.log('Stock export truncated tabs: ' + claimed.truncated.join(', '));
    return stockReceipt_(config, claimed, { outcome: 'stored', row_counts: counts });
  } catch (error) {
    errorCode = String(error && error.message) === 'bad_response' ? 'bad_response' : 'sheet_error';
  }
  stockReceipt_(config, claimed, { outcome: 'failed', error_code: errorCode });
  return false;
}

/** Install the one-minute export timer (Drive PDFs and stock tabs share exportApprovedQuotations) without needing Drive. */
function installStockExport() {
  configuration_();
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    ScriptApp.getProjectTriggers().forEach(function removeDuplicateExport_(trigger) {
      /** Replace only this integration's own export trigger. */
      if (trigger.getHandlerFunction() === 'exportApprovedQuotations') ScriptApp.deleteTrigger(trigger);
    });
    ScriptApp.newTrigger('exportApprovedQuotations').timeBased().everyMinutes(1).create();
  } finally {
    lock.releaseLock();
  }
}
