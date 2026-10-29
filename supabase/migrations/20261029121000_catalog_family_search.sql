-- Family is supplier-owned descriptive evidence and participates in lookup.
create index catalog_family_search on luma.products
 using gin(to_tsvector('english',sku||' '||name||' '||family||' '||description));
