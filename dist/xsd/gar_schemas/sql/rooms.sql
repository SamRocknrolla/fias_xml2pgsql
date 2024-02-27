CREATE TABLE IF NOT EXISTS rooms();
alter table rooms add column  if not exists id bigint;
alter table rooms add column  if not exists objectid bigint;
alter table rooms add column  if not exists objectguid varchar(36);
alter table rooms add column  if not exists changeid bigint;
alter table rooms add column  if not exists number varchar(50);
alter table rooms add column  if not exists roomtype bigint;
alter table rooms add column  if not exists opertypeid bigint;
alter table rooms add column  if not exists previd bigint;
alter table rooms add column  if not exists nextid bigint;
alter table rooms add column  if not exists updatedate timestamp;
alter table rooms add column  if not exists startdate timestamp;
alter table rooms add column  if not exists enddate timestamp;
alter table rooms add column  if not exists isactual smallint;
alter table rooms add column  if not exists isactive smallint;