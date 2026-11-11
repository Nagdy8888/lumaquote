/** Create the fictional supplier workbook tabs without overwriting existing populated tabs or formulas. */
function initializeSyntheticWorkbook(spreadsheetId) {
  var properties = PropertiesService.getScriptProperties();
  var configured = properties.getProperty('LUMA_SPREADSHEET_ID');
  if (configured && spreadsheetId && configured !== spreadsheetId) throw new Error('A different workbook is already configured.');
  var id = configured || spreadsheetId;
  var book = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
  if (!book) throw new Error('Set LUMA_SPREADSHEET_ID to the dedicated synthetic workbook.');
  properties.setProperty('LUMA_SPREADSHEET_ID', book.getId());
  var families = [
    ['Downlights','DL','Recessed commercial downlight',18,1800,32],
    ['Linear systems','LN','Continuous linear luminaire',36,4200,79],
    ['Track lighting','TR','Adjustable retail track spotlight',25,2500,58],
    ['High bays','HB','Industrial high-bay luminaire',120,18000,145],
    ['Outdoor lighting','OD','Weather-resistant exterior floodlight',50,6000,94],
    ['Emergency lighting','EM','Maintained emergency bulkhead',8,700,48]
  ];
  var products = [['sku','name','family','watts','lumens','cct','ip_rating','pack_size','discontinued']];
  var prices = [['sku','currency','unit_price','effective_from']];
  families.forEach(function makeFamily_(family) {
    /** Generate coherent, labeled fictional SKUs; the production importer validates each commercial field. */
    for (var i=0; i<12; i++) {
      var sku=family[1]+'-'+('00'+(i+1)).slice(-3);
      var cct=[3000,4000,5000][i%3];
      var watts=family[3]+Math.floor(i/3)*3;
      products.push([sku,family[2]+' '+watts+'W / '+cct+'K',family[0],watts,
        family[4]+Math.floor(i/3)*250,cct,(['OD','HB'].indexOf(family[1])>=0?'IP65':'IP44'),1,i===11]);
      prices.push([sku,'USD',family[5]+Math.floor(i/3)*8,'2026-10-29']);
    }
  });
  var tabs = {Products:products,Prices:prices,
    Policies:[['key','value'],['dataset','Synthetic supplier records for portfolio testing'],['currency','USD'],
      ['tax','excluded'],['quote_valid_days',7],['max_admin_discount_percent',10],['stock_reserved',false],
      ['delivery','Staff confirmation required']],
    'Quote Register':[['quotation_id','revision','customer_reference','total_usd','review_status','delivery_status']]};
  Object.keys(tabs).forEach(function initializeTab_(name) {
    /** Write only an empty dedicated tab; preserve any existing values so repeated setup is non-destructive. */
    var sheet=book.getSheetByName(name) || book.insertSheet(name);
    if (sheet.getLastRow() !== 0) return;
    sheet.getRange(1,1,tabs[name].length,tabs[name][0].length).setValues(tabs[name]);
    sheet.setFrozenRows(1);
    sheet.getRange(1,1,1,tabs[name][0].length).setBackground('#27312d').setFontColor('#ffffff').setFontWeight('bold');
    sheet.autoResizeColumns(1,tabs[name][0].length);
  });
  book.setSpreadsheetTimeZone('Africa/Cairo');
  SpreadsheetApp.flush();
  inspectSupplierWorkbook();
}

/** Log the configured workbook destination and tab sizes without exposing cell contents or private properties. */
function inspectSupplierWorkbook() {
  var id = PropertiesService.getScriptProperties().getProperty('LUMA_SPREADSHEET_ID');
  if (!id) throw new Error('LUMA_SPREADSHEET_ID is missing in Script Properties.');
  var book = SpreadsheetApp.openById(id);
  console.log('Configured workbook: ' + book.getUrl());
  ['Products', 'Prices', 'Policies', 'Quote Register', 'Stock', 'Customer Orders', 'Purchase Orders'].forEach(function reportTab_(name) {
    /** Report only tab presence and occupied dimensions to diagnose skipped initialization safely. */
    var sheet = book.getSheetByName(name);
    console.log(name + ': ' + (sheet ? sheet.getLastRow() + ' rows, ' + sheet.getLastColumn() + ' columns' : 'MISSING'));
  });
}
