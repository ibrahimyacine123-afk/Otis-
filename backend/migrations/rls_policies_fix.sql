-- =========================================================================
-- Correctif RLS — accès backend OTIS avec la cle publishable (anon)
-- =========================================================================
-- Constat (verification autonome) : le passage de SUPABASE_KEY d'une cle
-- service_role (JWT, contourne RLS) a une cle publishable/anon a casse les
-- INSERT sur tasks/thoughts/finances/reminders ("new row violates row-level
-- security policy"). Aucune colonne user_id n'existe dans ce schema : OTIS
-- est une app mono-utilisateur, le modele RLS "par ligne/par utilisateur"
-- ne s'applique pas ici — la frontiere de securite reelle est la possession
-- de la cle API, pas une isolation par ligne.
--
-- SECURITE : alternative architecturalement plus propre = garder RLS strict
-- pour anon et faire tourner le backend (skills/db.py) avec une cle
-- service_role (jamais exposee cote client), en reservant la cle
-- publishable au strict necessaire cote client (ex: dashboard en lecture
-- seule). Voir RAPPORT.md pour le detail de ce compromis.
--
-- Idempotent et sans danger si une table n'existe pas encore (ex:
-- wisdom_principles/decision_audit/accounts avant execution des migrations
-- trinity_schema.sql / finance_accounts.sql) : a re-executer apres celles-ci.

DO $$
DECLARE
    tbl text;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'tasks', 'thoughts', 'finances', 'reminders', 'milestones',
        'accounts', 'wisdom_principles', 'decision_audit'
    ]
    LOOP
        IF to_regclass('public.' || tbl) IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl);
            EXECUTE format('DROP POLICY IF EXISTS otis_backend_full_access ON public.%I', tbl);
            EXECUTE format(
                'CREATE POLICY otis_backend_full_access ON public.%I FOR ALL TO anon, authenticated USING (true) WITH CHECK (true)',
                tbl
            );
            RAISE NOTICE 'Policy appliquee sur %', tbl;
        ELSE
            RAISE NOTICE 'Table % absente, ignoree (executer a nouveau apres ses migrations)', tbl;
        END IF;
    END LOOP;
END $$;
