CREATE TABLE IF NOT EXISTS addhouse_types();
alter table addhouse_types add column  if not exists id bigint;
alter table addhouse_types add column  if not exists name varchar(50);
alter table addhouse_types add column  if not exists shortname varchar(50);
alter table addhouse_types add column  if not exists "desc" varchar(250);
alter table addhouse_types add column  if not exists updatedate timestamp;
alter table addhouse_types add column  if not exists startdate timestamp;
alter table addhouse_types add column  if not exists enddate timestamp;
alter table addhouse_types add column  if not exists isactive boolean;
