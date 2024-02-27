CREATE TABLE IF NOT EXISTS normative_docs_types();
alter table normative_docs_types add column  if not exists id bigint;
alter table normative_docs_types add column  if not exists name varchar(500);
alter table normative_docs_types add column  if not exists startdate timestamp;
alter table normative_docs_types add column  if not exists enddate timestamp;
