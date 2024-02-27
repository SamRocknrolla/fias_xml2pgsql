CREATE TABLE IF NOT EXISTS room_types();
alter table room_types add column  if not exists id bigint;
alter table room_types add column  if not exists name varchar(100);
alter table room_types add column  if not exists shortname varchar(50);
alter table room_types add column  if not exists "desc" varchar(250);
alter table room_types add column  if not exists updatedate timestamp;
alter table room_types add column  if not exists startdate timestamp;
alter table room_types add column  if not exists enddate timestamp;
alter table room_types add column  if not exists isactive boolean;
