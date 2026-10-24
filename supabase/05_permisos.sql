-- LiciGuard · 05 · Permisos para el servidor (service_role)
--
-- Síntoma que arregla:  "permission denied for table usuarios" (código 42501)
-- Por qué pasa: en los proyectos nuevos de Supabase las tablas creadas con SQL ya no reciben permisos automáticos
-- para la API. LiciGuard entra SOLO desde el servidor con la clave service_role, así que basta con darle permisos
-- a ese rol. NO se dan permisos a "anon" ni a "authenticated": desde el navegador nadie puede leer las tablas
-- (además todas tienen Row Level Security activado y sin políticas públicas).
--
-- Cómo usarlo: Supabase → SQL Editor → New query → pega todo → Run. Se puede ejecutar varias veces sin problema.

grant usage on schema public to service_role;
grant all privileges on all tables    in schema public to service_role;
grant all privileges on all sequences in schema public to service_role;
grant execute on all functions        in schema public to service_role;

-- Para las tablas que se creen después (próximas versiones de LiciGuard)
alter default privileges in schema public grant all privileges on tables    to service_role;
alter default privileges in schema public grant all privileges on sequences to service_role;
alter default privileges in schema public grant execute on functions        to service_role;

-- Comprobación: debe listar las 8 tablas con "true" en las tres columnas
select c.relname as tabla,
       has_table_privilege('service_role', c.oid, 'select') as leer,
       has_table_privilege('service_role', c.oid, 'insert') as crear,
       has_table_privilege('service_role', c.oid, 'delete') as borrar
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r'
order by 1;
