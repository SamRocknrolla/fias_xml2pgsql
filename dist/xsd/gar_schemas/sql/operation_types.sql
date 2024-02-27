CREATE TABLE IF NOT EXISTS operation_types();
alter table operation_types add column  if not exists id bigint;
alter table operation_types add column  if not exists name varchar(100);
alter table operation_types add column  if not exists shortname varchar(100);
alter table operation_types add column  if not exists "desc" varchar(250);
alter table operation_types add column  if not exists updatedate timestamp;
alter table operation_types add column  if not exists startdate timestamp;
alter table operation_types add column  if not exists enddate timestamp;
alter table operation_types add column  if not exists isactive boolean;
