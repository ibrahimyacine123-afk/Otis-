# BLOCKERS.md — Chantier OTIS (5 phases, exécution autonome)

Journal des blocages, contournements et décisions prises sans validation humaine,
conformément au mode autonome activé pour ce chantier.

## Phase 1 — Hygiène + GitHub

- **DATABASE_URL manquante.** L'utilisateur a indiqué qu'elle était "déjà dans mon
  .env actuel" mais le fichier `.env` local ne la contenait pas (vérifié avant et
  après mise à jour des secrets). Variable ajoutée à `.env.template` (vide).
  Conséquence : impossible d'exécuter les migrations SQL de la Phase 2 directement
  sur la base Postgres. Contournement : le SQL est écrit dans
  `backend/migrations/` et doit être collé manuellement dans le SQL Editor
  Supabase. **Action requise : ajouter DATABASE_URL au `.env` pour permettre
  l'exécution automatique lors d'un prochain run.**

- **Conflit d'historique Git résolu par force-push.** Le remote
  `https://github.com/ibrahimyacine123-afk/Otis-.git` contenait déjà un commit
  "chantier 1" (issu d'un autre environnement, `/tmp/otis-github`) avec une
  structure différente et partielle (pas de `whatsapp-bridge/`, pas de
  `skills/agents/`, pas de `server.py`/`dashboard.py`/`otis.py` — juste
  `db.py`, `orchestrator.py`, `schema.sql` et des docs). Le chantier en 5 phases
  demandé ici dépend entièrement de l'architecture présente dans CE dossier
  local (agents, serveur FastAPI, dashboard, pont WhatsApp). Décision : la
  version locale devient la source de vérité, poussée avec `--force`,
  écrasant l'ancien commit distant. L'ancien commit reste récupérable via le
  reflog GitHub pendant un certain temps si besoin de le consulter.

- **Changement de clé Supabase.** L'ancienne `SUPABASE_KEY` dans `.env` était un
  JWT `service_role` (accès complet, contourne les RLS). La nouvelle clé fournie
  (`sb_publishable_...`) est une clé publique/anon. Si des policies RLS
  restrictives existent sur les tables `tasks`/`thoughts`/`finances`/`reminders`,
  les écritures backend (via `skills/db.py`) pourraient échouer silencieusement
  ou être rejetées avec cette nouvelle clé. **Non testé en direct** (nécessite
  DATABASE_URL ou un accès Supabase pour vérifier les policies). À surveiller
  en priorité si des erreurs d'insertion apparaissent.
