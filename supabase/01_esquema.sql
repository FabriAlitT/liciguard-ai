-- LiciGuard AI · Esquema base (Fase 1)
-- Cómo usarlo: Supabase > SQL Editor > New query > pega todo > Run.

create extension if not exists pgcrypto;

-- 1) Personas que entran con su código (sin contraseña, solo para la demo)
create table if not exists usuarios (
  id         uuid primary key default gen_random_uuid(),
  codigo     text not null unique check (codigo = lower(codigo) and codigo ~ '^[a-z0-9-]{3,40}$'),
  nombre     text not null,
  acepto_privacidad_en timestamptz,      -- cuándo aceptó el aviso de privacidad (Ley 29733)
  creado_en  timestamptz not null default now()
);

-- 2) Perfil de la empresa (se llena una vez)
create table if not exists empresas (
  id                  uuid primary key default gen_random_uuid(),
  usuario_id          uuid not null unique references usuarios(id) on delete cascade,
  razon_social        text,
  rubro               text,
  region              text,
  es_mype             boolean default true,
  experiencia_soles   numeric(14,2) default 0,
  produccion_mensual  integer,
  maquinas            integer,
  personal            integer,
  certificaciones     text[] not null default '{}',
  rnp_vigente         boolean,               -- null = no lo registró
  actualizado_en      timestamptz not null default now()
);

-- 3) Cada licitación revisada
create table if not exists analisis (
  id                 uuid primary key default gen_random_uuid(),
  usuario_id         uuid not null references usuarios(id) on delete cascade,
  nombre_archivo     text not null,
  sha256             text not null,
  paginas            integer,
  paginas_sin_texto  integer default 0,
  entidad            text,
  objeto             text,
  nomenclatura       text,
  valor_estimado     numeric(14,2),
  estado             text not null default 'leido'
                     check (estado in ('leido','procesando','listo','error')),
  recomendacion      text check (recomendacion in ('postular','observar','no_postular')),
  resultado          jsonb not null default '{}',
  creado_en          timestamptz not null default now(),
  unique (usuario_id, sha256)            -- el mismo PDF no se duplica en el historial
);
create index if not exists analisis_usuario_idx on analisis(usuario_id, creado_en desc);

-- 4) Requisitos extraídos de las bases (con su página)
create table if not exists requisitos (
  id           uuid primary key default gen_random_uuid(),
  analisis_id  uuid not null references analisis(id) on delete cascade,
  categoria    text not null,           -- experiencia, certificacion, plazo, equipo, personal, documento…
  descripcion  text not null,
  valor        numeric(14,2),           -- p. ej. monto de experiencia exigido
  pagina       integer not null,
  cita         text not null
);
create index if not exists requisitos_analisis_idx on requisitos(analisis_id);

-- 5) Hallazgos de las 4 preguntas (cada uno con su prueba)
create table if not exists hallazgos (
  id               uuid primary key default gen_random_uuid(),
  analisis_id      uuid not null references analisis(id) on delete cascade,
  pregunta         text not null check (pregunta in ('justa','puedo','conviene','ganar')),
  severidad        text not null check (severidad in ('fuerte','media','leve','info')),
  titulo           text not null,
  explicacion      text not null,
  pagina           integer,
  cita             text,
  cita_verificada  boolean not null default false,
  norma_ref        text,
  estado_revision  text not null default 'pendiente'
                   check (estado_revision in ('pendiente','correcta','descartada')),
  creado_en        timestamptz not null default now()
);
create index if not exists hallazgos_analisis_idx on hallazgos(analisis_id, pregunta);

-- 6) Registro de llamadas a modelos (Gemini / Groq) para depurar y para el pitch
create table if not exists llm_llamadas (
  id           bigserial primary key,
  analisis_id  uuid references analisis(id) on delete set null,
  proveedor    text not null,
  modelo       text,
  tarea        text,
  latencia_ms  integer,
  tokens       integer,
  estado       text,
  error        text,
  creado_en    timestamptz not null default now()
);

-- Seguridad: activamos RLS sin políticas públicas.
-- La app usa la clave service_role desde el servidor de Streamlit, que sí puede leer/escribir.
-- Nadie puede leer estas tablas con la clave pública (anon) desde un navegador.
alter table usuarios     enable row level security;
alter table empresas     enable row level security;
alter table analisis     enable row level security;
alter table requisitos   enable row level security;
alter table hallazgos    enable row level security;
alter table llm_llamadas enable row level security;
