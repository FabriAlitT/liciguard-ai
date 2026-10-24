-- LiciGuard AI · Módulos Seguimiento y Mis documentos (ejecútalo DESPUÉS de 01_esquema.sql)
-- Supabase > SQL Editor > New query > pega todo > Run.  No borra ni cambia nada de lo anterior.

create table if not exists seguimiento (
  id                   uuid primary key default gen_random_uuid(),
  usuario_id           uuid not null references usuarios(id) on delete cascade,
  sha256               text not null,
  nombre               text,
  entidad              text,
  valor_estimado       numeric(14,2),
  recomendacion        text,
  etapa                text not null default 'Revisada'
                       check (etapa in ('Revisada','Observada','Ofertada','Ganada','Perdida','Descartada')),
  fecha_observaciones  date,
  fecha_ofertas        date,
  fecha_buena_pro      date,
  mi_oferta            numeric(14,2),
  oferta_ganadora      numeric(14,2),
  ganador              text,
  checklist            jsonb not null default '{}',
  notas                text default '',
  actualizado_en       timestamptz not null default now(),
  unique (usuario_id, sha256)
);
create index if not exists seguimiento_usuario_idx on seguimiento(usuario_id);

create table if not exists documentos (
  id          uuid primary key default gen_random_uuid(),
  usuario_id  uuid not null references usuarios(id) on delete cascade,
  nombre      text not null,
  tipo        text,
  vence_el    date,
  creado_en   timestamptz not null default now()
);
create index if not exists documentos_usuario_idx on documentos(usuario_id);

alter table seguimiento enable row level security;
alter table documentos  enable row level security;
