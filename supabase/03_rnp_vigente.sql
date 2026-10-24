-- LiciGuard AI · ¿RNP vigente? en el perfil de la empresa (ejecútalo DESPUÉS de 01 y 02)
-- Supabase > SQL Editor > New query > pega todo > Run.  No borra ni cambia nada de lo anterior.
-- null = la empresa no lo registró · true = vigente · false = no tiene o venció

alter table empresas add column if not exists rnp_vigente boolean;
