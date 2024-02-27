CREATE TABLE IF NOT EXISTS reestr_objects();
alter table reestr_objects add column  if not exists objectid bigint;
alter table reestr_objects add column  if not exists createdate timestamp;
alter table reestr_objects add column  if not exists changeid bigint;
alter table reestr_objects add column  if not exists levelid bigint;
alter table reestr_objects add column  if not exists updatedate timestamp;
alter table reestr_objects add column  if not exists objectguid varchar(36);
alter table reestr_objects add column  if not exists isactive smallint;
