-- LiciGuard AI · Aviso de privacidad (Ley N.° 29733)   (ejecútalo DESPUÉS de 01, 02 y 03)
-- Supabase > SQL Editor > New query > pega todo > Run.  No borra ni cambia nada de lo anterior.
-- Guarda cuándo aceptó cada persona el aviso de privacidad al crear su código.
-- El botón "Borrar mi cuenta" usa el "on delete cascade" que ya existe en todas las tablas.

alter table usuarios add column if not exists acepto_privacidad_en timestamptz;
