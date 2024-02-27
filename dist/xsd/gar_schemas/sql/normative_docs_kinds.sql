CREATE TABLE IF NOT EXISTS normative_docs_kinds();
alter table normative_docs_kinds add column  if not exists id bigint;
alter table normative_docs_kinds add column  if not exists name varchar(500);
