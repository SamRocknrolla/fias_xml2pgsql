CREATE TABLE IF NOT EXISTS addr_obj_division();
alter table addr_obj_division add column  if not exists id bigint;
alter table addr_obj_division add column  if not exists parentid bigint;
alter table addr_obj_division add column  if not exists childid bigint;
alter table addr_obj_division add column  if not exists changeid bigint;
