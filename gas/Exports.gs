/** Return the private Drive folder configured for quotation copies; fail closed when it is missing or unreadable. */
function exportFolder_() {
  var id = PropertiesService.getScriptProperties().getProperty('LUMA_DRIVE_FOLDER_ID');
  if (!id) throw new Error('Set LUMA_DRIVE_FOLDER_ID to a private Drive folder before enabling exports.');
  return DriveApp.getFolderById(id);
}

/** Return lowercase SHA-256 hex of a byte array so the Drive copy can be compared with the backend digest. */
function sha256Hex_(bytes) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes)
    .map(function toHexByte_(value) {
      /** Interpret signed Apps Script byte values as unsigned hexadecimal octets. */
      return ('0' + (value & 255).toString(16)).slice(-2);
    }).join('');
}

/** POST one signed envelope to a path under the configured callback URL and return status plus parsed JSON. */
function signedExportPost_(config, path, fields) {
  var envelope = { schema_version: 1, company_id: config.companyId, spreadsheet_id: config.spreadsheetId,
    timestamp: Math.floor(Date.now() / 1000), nonce: Utilities.getUuid() };
  Object.keys(fields).forEach(function copyField_(key) {
    /** Add only the event-specific fields; the shared envelope fields above cannot be overridden. */
    if (!(key in envelope)) envelope[key] = fields[key];
  });
  var payload = JSON.stringify(envelope);
  var response = UrlFetchApp.fetch(config.callbackUrl + path, { method: 'post', contentType: 'application/json',
    payload: payload, headers: { 'X-Luma-Signature': signPayload_(payload, config.secret) },
    followRedirects: false, muteHttpExceptions: true });
  var parsed = null;
  try { parsed = JSON.parse(response.getContentText()); } catch (ignored) { parsed = null; }
  return { status: response.getResponseCode(), body: parsed };
}

/** Find this export's earlier Drive file (same name and export id in its description) so a retry never duplicates it. */
function findExistingExport_(folder, name, exportId) {
  var files = folder.getFilesByName(name);
  while (files.hasNext()) {
    var file = files.next();
    if (file.getDescription() === exportId) return file;
  }
  return null;
}

/** File one claimed PDF in Drive, read it back and report the observed digest; never throws past its own receipt. */
function exportOne_(config, folder, claimed) {
  var errorCode = null;
  try {
    var bytes = Utilities.base64Decode(claimed.pdf_base64);
    if (sha256Hex_(bytes) !== claimed.sha256 || bytes.length !== claimed.size) {
      errorCode = 'transfer_corrupt';
    } else {
      var file = findExistingExport_(folder, claimed.filename, claimed.export_id);
      if (!file) {
        file = folder.createFile(Utilities.newBlob(bytes, 'application/pdf', claimed.filename));
        file.setDescription(claimed.export_id);
      }
      var stored = file.getBlob().getBytes();
      var receipt = signedExportPost_(config, '/exports/receipt', { event: 'drive_export_receipt',
        export_id: claimed.export_id, claim_token: claimed.claim_token, outcome: 'stored',
        drive_file_id: file.getId(), sha256: sha256Hex_(stored), size: stored.length });
      PropertiesService.getScriptProperties().setProperty('LUMA_LAST_EXPORT_STATUS', String(receipt.status));
      return receipt.status === 200;
    }
  } catch (error) {
    errorCode = 'drive_error';
  }
  var failure = signedExportPost_(config, '/exports/receipt', { event: 'drive_export_receipt',
    export_id: claimed.export_id, claim_token: claimed.claim_token, outcome: 'failed', error_code: errorCode });
  PropertiesService.getScriptProperties().setProperty('LUMA_LAST_EXPORT_STATUS', String(failure.status));
  return false;
}

/** Claim and file up to three approved quotation PDFs per run under a script lock; the backend owns retries. */
function exportApprovedQuotations() {
  var config = configuration_();
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    var folder = exportFolder_();
    for (var count = 0; count < 3; count++) {
      var claim = signedExportPost_(config, '/exports/claim', { event: 'drive_export_claim' });
      if (claim.status !== 200) {
        PropertiesService.getScriptProperties().setProperty('LUMA_LAST_EXPORT_STATUS', String(claim.status));
        throw new Error('Export claim was not accepted; check backend configuration and the connection.');
      }
      if (!claim.body || !claim.body.export) return;
      exportOne_(config, folder, claim.body.export);
    }
  } finally {
    lock.releaseLock();
  }
}

/** Validate folder access, then install one one-minute export trigger without touching other handlers. */
function installDriveExport() {
  exportFolder_();
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
