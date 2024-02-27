CREATE TABLE IF NOT EXISTS param_types();
alter table param_types add column  if not exists id integer;
alter table param_types add column  if not exists name varchar(50);
alter table param_types add column  if not exists code varchar(50);
alter table param_types add column  if not exists "desc" varchar(120);
alter table param_types add column  if not exists updatedate timestamp;
alter table param_types add column  if not exists startdate timestamp;
alter table param_types add column  if not exists enddate timestamp;
alter table param_types add column  if not exists isactive boolean;
