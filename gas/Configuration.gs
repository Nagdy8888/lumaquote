/** Resolve required private Script Properties; never log the callback secret or customer content. */
function configuration_() {
  var properties = PropertiesService.getScriptProperties();
  var config = {
    spreadsheetId: properties.getProperty('LUMA_SPREADSHEET_ID'),
    companyId: properties.getProperty('LUMA_COMPANY_ID'),
    callbackUrl: properties.getProperty('LUMA_CALLBACK_URL'),
    secret: properties.getProperty('LUMA_CALLBACK_SECRET')
  };
  if (!config.spreadsheetId || !config.companyId || !config.callbackUrl || !config.secret) {
    throw new Error('Complete the LUMA Script Properties before installing the edit trigger.');
  }
  if (config.callbackUrl.indexOf('https://') !== 0 || !/\/callbacks\/google$/.test(config.callbackUrl)) {
    throw new Error('The callback must use HTTPS and end with /callbacks/google.');
  }
  return config;
}

/** Return lowercase SHA-256 HMAC hex for the exact UTF-8 payload bytes shared with the backend verifier. */
function signPayload_(payload, secret) {
  return Utilities.computeHmacSha256Signature(payload, secret, Utilities.Charset.UTF_8)
    .map(function toHexByte_(value) {
      /** Interpret signed Apps Script byte values as unsigned hexadecimal octets. */
      return ('0' + (value & 255).toString(16)).slice(-2);
    }).join('');
}
