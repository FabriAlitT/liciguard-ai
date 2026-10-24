-- LiciGuard · 06 · Varias empresas por persona (p. ej. un consultor con varios clientes)
--
-- Qué hace:
--   1. Una persona puede tener VARIAS empresas (antes solo una).
--   2. Cada revisión, seguimiento y documento pasa a pertenecer a UNA empresa (columna empresa_id): así no se mezclan.
--   3. Lo que ya tenías se asigna a tu empresa actual. Si tenías revisiones pero nunca llenaste «Mi empresa», se
--      crea una empresa «Mi empresa» para no perder nada.
--
-- Cómo usarlo: Supabase → SQL Editor → New query → pega todo → Run (después de 01 a 05). Se puede repetir.

-- 1) Quitar «una sola empresa por persona»
alter table empresas drop constraint if exists empresas_usuario_id_key;
alter table empresas add column if not exists creado_en timestamptz not null default now();
create index if not exists empresas_usuario_idx on empresas(usuario_id);

-- 2) Empresa para quien tenía datos sin perfil
insert into empresas (usuario_id, razon_social)
select distinct x.usuario_id, 'Mi empresa'
from (select usuario_id from analisis union select usuario_id from seguimiento
      union select usuario_id from documentos) x
where not exists (select 1 from empresas e where e.usuario_id = x.usuario_id);

-- 3) Columna empresa_id (si se borra la empresa, se borra lo suyo)
alter table analisis    add column if not exists empresa_id uuid references empresas(id) on delete cascade;
alter table seguimiento add column if not exists empresa_id uuid references empresas(id) on delete cascade;
alter table documentos  add column if not exists empresa_id uuid references empresas(id) on delete cascade;

-- 4) Lo anterior pasa a la (primera) empresa de cada persona
update analisis a set empresa_id = (select e.id from empresas e where e.usuario_id = a.usuario_id
                                    order by e.creado_en limit 1) where a.empresa_id is null;
update seguimiento s set empresa_id = (select e.id from empresas e where e.usuario_id = s.usuario_id
                                       order by e.creado_en limit 1) where s.empresa_id is null;
update documentos d set empresa_id = (select e.id from empresas e where e.usuario_id = d.usuario_id
                                      order by e.creado_en limit 1) where d.empresa_id is null;

-- 5) El mismo PDF puede revisarse para dos empresas distintas (antes: una vez por persona)
alter table analisis    drop constraint if exists analisis_usuario_id_sha256_key;
alter table seguimiento drop constraint if exists seguimiento_usuario_id_sha256_key;
alter table analisis    drop constraint if exists analisis_empresa_sha_key;
alter table seguimiento drop constraint if exists seguimiento_empresa_sha_key;
alter table analisis    add constraint analisis_empresa_sha_key    unique (empresa_id, sha256);
alter table seguimiento add constraint seguimiento_empresa_sha_key unique (empresa_id, sha256);
create index if not exists analisis_empresa_idx    on analisis(empresa_id, creado_en desc);
create index if not exists seguimiento_empresa_idx on seguimiento(empresa_id);
create index if not exists documentos_empresa_idx  on documentos(empresa_id);

-- 6) Permisos para el servidor (por si 05 se ejecutó antes)
grant all privileges on all tables in schema public to service_role;

-- Comprobación: cuántas empresas tiene cada persona y si quedó algo sin empresa (debe ser 0)
select (select count(*) from analisis where empresa_id is null)    as analisis_sin_empresa,
       (select count(*) from seguimiento where empresa_id is null) as seguimiento_sin_empresa,
       (select count(*) from documentos where empresa_id is null)  as documentos_sin_empresa;
