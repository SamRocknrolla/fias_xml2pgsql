CREATE TABLE IF NOT EXISTS normative_docs();
alter table normative_docs add column  if not exists id bigint;
alter table normative_docs add column  if not exists name varchar(8000);
alter table normative_docs add column  if not exists date timestamp;
alter table normative_docs add column  if not exists number varchar(150);
alter table normative_docs add column  if not exists type bigint;
alter table normative_docs add column  if not exists kind bigint;
alter table normative_docs add column  if not exists updatedate timestamp;
alter table normative_docs add column  if not exists orgname varchar(255);
alter table normative_docs add column  if not exists regnum varchar(100);
alter table normative_docs add column  if not exists regdate timestamp;
alter table normative_docs add column  if not exists accdate timestamp;
alter table normative_docs add column  if not exists comment varchar(8000);
