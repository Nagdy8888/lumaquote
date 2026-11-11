/** Install exactly one authorized edit trigger for this workbook; run once after setting Script Properties. */
function installSupplierEditTrigger() {
  var config = configuration_();
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    ScriptApp.getProjectTriggers().forEach(function removeOwnedDuplicate_(trigger) {
      /** Replace only this integration's own edit handler, preserving unrelated account/project triggers. */
      if (trigger.getHandlerFunction() === 'notifySupplierEdit') ScriptApp.deleteTrigger(trigger);
    });
    ScriptApp.newTrigger('notifySupplierEdit').forSpreadsheet(config.spreadsheetId).onEdit().create();
    PropertiesService.getScriptProperties().setProperty('LUMA_TRIGGER_INSTALLED_AT', new Date().toISOString());
  } finally {
    lock.releaseLock();
  }
}

/** Send a signed invalidation hint for a human edit; the backend must fetch authoritative records itself. */
function notifySupplierEdit(event) {
  if (!event || !event.source || !event.range) throw new Error('An installable spreadsheet edit event is required.');
  var config = configuration_();
  if (event.source.getId() !== config.spreadsheetId) throw new Error('Unexpected workbook.');
  var allowed = ['Products', 'Prices', 'Policies'];
  if (allowed.indexOf(event.range.getSheet().getName()) < 0) return;
  var payload = JSON.stringify({ schema_version: 1, company_id: config.companyId,
    spreadsheet_id: config.spreadsheetId, timestamp: Math.floor(Date.now() / 1000),
    nonce: Utilities.getUuid(), event: 'supplier_records_changed' });
  var response = UrlFetchApp.fetch(config.callbackUrl, { method: 'post', contentType: 'application/json',
    payload: payload, headers: { 'X-Luma-Signature': signPayload_(payload, config.secret) },
    followRedirects: false, muteHttpExceptions: true });
  if (response.getResponseCode() !== 202) {
    PropertiesService.getScriptProperties().setProperty('LUMA_LAST_CALLBACK_STATUS', String(response.getResponseCode()));
    throw new Error('Supplier sync notification was not accepted; periodic reconciliation remains required.');
  }
  PropertiesService.getScriptProperties().setProperty('LUMA_LAST_CALLBACK_AT', new Date().toISOString());
  synchronizeSupplierWorkbook();
}

/** Send one signed test hint without changing any cell; success proves receipt only, not completed synchronization. */
function verifySupplierCallback() {
  var config = configuration_();
  var book = SpreadsheetApp.openById(config.spreadsheetId);
  var products = book.getSheetByName('Products');
  if (!products) throw new Error('Initialize the Products tab before testing the callback.');
  notifySupplierEdit({ source: book, range: products.getRange('A1') });
  console.log('Signed callback accepted. Sheet snapshot synchronization is a separate operation.');
}
