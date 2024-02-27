CREATE TABLE IF NOT EXISTS change_history();
alter table change_history add column  if not exists changeid bigint;
alter table change_history add column  if not exists objectid bigint;
alter table change_history add column  if not exists adrobjectid varchar(36);
alter table change_history add column  if not exists opertypeid bigint;
alter table change_history add column  if not exists ndocid bigint;
alter table change_history add column  if not exists changedate timestamp;
