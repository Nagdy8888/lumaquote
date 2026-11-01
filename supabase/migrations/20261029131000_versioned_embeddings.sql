alter table luma.usage add column operation text not null default 'primary'
 check(operation in ('primary','retrieval'));
alter table luma.usage drop constraint usage_job_id_key;
alter table luma.usage add constraint usage_operation_identity unique(job_id,operation);

create function luma.catalog_evidence_text(item luma.products) returns text
language sql immutable as $$
 select concat_ws(E'\n',(item).sku,(item).name,(item).family,(item).description,
   (item).watts::text||'W',(item).lumens::text||' lm',(item).cct::text||'K',(item).ip_rating)
$$;

create table luma.catalog_embeddings (
 company_id uuid not null, product_id uuid not null, source_id uuid not null,
 source_version integer not null check(source_version>0), page integer not null check(page>0),
 model text not null check(model='text-embedding-3-small'), content text not null,
 embedding extensions.vector(1536) not null, indexed_at timestamptz not null default now(),
 primary key(company_id,product_id),
 foreign key(company_id,product_id) references luma.products(company_id,id),
 foreign key(company_id,source_id) references luma.sources(company_id,id)
);
alter table luma.catalog_embeddings enable row level security;
create policy staff_scope on luma.catalog_embeddings for select to luma_api using
 (exists(select 1 from luma.memberships m where m.company_id=catalog_embeddings.company_id and m.user_id=auth.uid() and m.active));
create policy worker_scope on luma.catalog_embeddings to luma_worker using(true) with check(true);
grant select on luma.catalog_embeddings to luma_api;
grant select,insert,update on luma.catalog_embeddings to luma_worker;
