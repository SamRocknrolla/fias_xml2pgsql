CREATE TABLE IF NOT EXISTS steads();
alter table steads add column  if not exists id bigint;
alter table steads add column  if not exists objectid bigint;
alter table steads add column  if not exists objectguid varchar(36);
alter table steads add column  if not exists changeid bigint;
alter table steads add column  if not exists number varchar(250);
alter table steads add column  if not exists opertypeid varchar(2);
alter table steads add column  if not exists previd bigint;
alter table steads add column  if not exists nextid bigint;
alter table steads add column  if not exists updatedate timestamp;
alter table steads add column  if not exists startdate timestamp;
alter table steads add column  if not exists enddate timestamp;
alter table steads add column  if not exists isactual smallint;
alter table steads add column  if not exists isactive smallint;