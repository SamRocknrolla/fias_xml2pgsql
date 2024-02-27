CREATE TABLE IF NOT EXISTS object_levels();
alter table object_levels add column  if not exists level integer;
alter table object_levels add column  if not exists name varchar(250);
alter table object_levels add column  if not exists shortname varchar(50);
alter table object_levels add column  if not exists updatedate timestamp;
alter table object_levels add column  if not exists startdate timestamp;
alter table object_levels add column  if not exists enddate timestamp;
alter table object_levels add column  if not exists isactive boolean;
