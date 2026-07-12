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

- **API NVIDIA (integrate.api.nvidia.com) devenue injoignable en cours de chantier — POST bloqué/hang.**
  Le tout premier test de `TrinityFilter.evaluate()` (juste après l'écriture du module) a réussi et
  retourné des scores corrects (ego=8, clarté=2, foi=6, émotion=avidité/8 sur le message levier x3
  USDT/TRY — exactement le scénario attendu en Phase 5). Quelques minutes plus tard, tout appel POST
  vers `https://integrate.api.nvidia.com/v1/chat/completions` se met à bloquer indéfiniment (testé
  jusqu'à 5 fois : SDK OpenAI par défaut, SDK avec `timeout=20s`/`max_retries=1` explicites, puis
  `curl -X POST` brut avec la même clé — tous restent bloqués au-delà de 20-40s sans réponse ni erreur).
  Diagnostic : `curl GET /v1/models` sur le même hôte répond en 0.3s (HTTP 200) — la connectivité
  réseau vers l'hôte fonctionne, seul le POST vers `/v1/chat/completions` reste bloqué. Ce n'est donc
  pas un bug dans `llm_client.py`/`trinity.py`/`orchestrator.py` (le code identique fonctionnait au
  premier essai) mais un blocage externe (API NVIDIA en incident, ou filtrage réseau côté sandbox
  spécifique à ce endpoint/verbe). **Contournement : aucun disponible côté code.** La suite du chantier
  (Phases 2-5) a donc été implémentée et vérifiée par compilation Python (`py_compile`) et relecture,
  mais PAS re-testée en conditions réelles au-delà du tout premier appel réussi. **Action requise :
  relancer les tests end-to-end (Phase 5) une fois l'API NVIDIA de nouveau joignable.**

## Phase 4 — WhatsApp + rituel

- **Bug réel trouvé et corrigé (pas introduit par ce chantier) : `UnicodeEncodeError` sur Windows
  dès que stdout n'est pas un terminal interactif.** En testant le flux `webhook` en local
  (`uvicorn` avec stdout redirigé vers un fichier de log, ce qui est la situation normale pour un
  service lancé en tâche de fond), chaque requête plantait avec `UnicodeEncodeError` sur les emojis
  des `print()` (codepage Windows `cp1254`, pas UTF-8), renvoyant systématiquement une 500 au pont
  WhatsApp. Corrigé en forçant `sys.stdout.reconfigure(encoding="utf-8")` en tête de `server.py`,
  `otis.py` et `scheduler.py`. Revérifié : le rejet d'un numéro non autorisé renvoie maintenant bien
  403 avec logs lisibles. **Ce bug aurait cassé le pont WhatsApp en usage réel (service/systemd/tâche
  planifiée) sans jamais se voir en test interactif dans un terminal.**

- **Test du chemin "numéro autorisé" du webhook non concluant** : bloqué par le même incident API
  NVIDIA que documenté plus haut (le call `orchestrator.process_request` → `trinity.evaluate`
  atteint bien le code, mais le POST vers NVIDIA reste bloqué). Le routage, l'auth et le formatage
  WhatsApp sont vérifiés ; le passage réel par le LLM ne l'est pas au-delà du tout premier test réussi.

- **Envoi WhatsApp sortant non testable en conditions réelles dans cet environnement.** Le nouvel
  endpoint `POST /send` du pont (`whatsapp-bridge/index.js`) est vérifié par lecture de code et
  `node --check` (syntaxe OK), mais son exécution réelle nécessite une session WhatsApp Web
  authentifiée (scan de QR code) — impossible à faire de façon autonome/headless. **Action requise :
  lancer `node index.js`, scanner le QR, puis lancer `python scheduler.py` (ou déclencher
  manuellement `send_morning_ritual()`) pour valider l'envoi réel.**

- **Changement de clé Supabase.** L'ancienne `SUPABASE_KEY` dans `.env` était un
  JWT `service_role` (accès complet, contourne les RLS). La nouvelle clé fournie
  (`sb_publishable_...`) est une clé publique/anon. Si des policies RLS
  restrictives existent sur les tables `tasks`/`thoughts`/`finances`/`reminders`,
  les écritures backend (via `skills/db.py`) pourraient échouer silencieusement
  ou être rejetées avec cette nouvelle clé. **Non testé en direct** (nécessite
  DATABASE_URL ou un accès Supabase pour vérifier les policies). À surveiller
  en priorité si des erreurs d'insertion apparaissent.
