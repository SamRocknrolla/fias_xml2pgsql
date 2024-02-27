CREATE TABLE IF NOT EXISTS house_types();
alter table house_types add column  if not exists id bigint;
alter table house_types add column  if not exists name varchar(50);
alter table house_types add column  if not exists shortname varchar(50);
alter table house_types add column  if not exists "desc" varchar(250);
alter table house_types add column  if not exists updatedate timestamp;
alter table house_types add column  if not exists startdate timestamp;
alter table house_types add column  if not exists enddate timestamp;
alter table house_types add column  if not exists isactive boolean;
