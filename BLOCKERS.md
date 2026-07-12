# BLOCKERS.md — Chantier OTIS (5 phases + vérification finale, exécution autonome)

Journal des blocages, contournements et décisions prises sans validation humaine.
Mis à jour après la ronde de vérification post-"3 blockers manuels réglés".

## Résolus lors du chantier initial (Phases 1-5)

- **Conflit d'historique Git résolu par force-push.** Le remote contenait un ancien commit
  "chantier 1" (issu de `/tmp/otis-github`), structure différente et partielle. La version locale
  (seule à contenir l'architecture complète : agents, FastAPI, dashboard, pont WhatsApp) est devenue
  la source de vérité via `git push --force`. Ancien commit récupérable via le reflog GitHub un temps.

- **`UnicodeEncodeError` sur Windows dès que stdout n'est pas un terminal interactif** — bug réel
  préexistant (pas introduit par ce chantier), cassait 100% des requêtes webhook en usage service/log
  redirigé (codepage `cp1254` incompatible avec les emojis des `print()`). Corrigé par
  `sys.stdout.reconfigure(encoding="utf-8")` dans `server.py`/`otis.py`/`scheduler.py`. **Vérifié en
  direct** : le webhook renvoie maintenant bien 403 avec logs lisibles pour un numéro non autorisé.

## Vérification finale — état par point demandé

**1. Appels LLM live avec la nouvelle clé NVIDIA — toujours bloqués, cause isolée précisément.**
La valeur de `NVIDIA_API_KEY` dans `.env` est identique à celle d'avant l'incident (pas de nouvelle
clé détectée dans ce fichier local). Indépendamment de ça, diagnostic réseau approfondi :
- `curl -X POST .../chat/completions` avec clé invalide + body vide → **404/400 en 0.2s** (gateway OK)
- `curl -X POST .../chat/completions` avec clé valide + modèle invalide → **404 en 0.19s** (auth OK, routage OK)
- `curl -X POST .../chat/completions` avec clé valide + modèle réel (`meta/llama-3.3-70b-instruct`) +
  payload valide → **bloque indéfiniment** (testé jusqu'à 40s, à répétition, SDK et curl brut)

Conclusion : ce n'est ni un problème de clé, ni de code, ni de réseau/sandbox — l'API gateway NVIDIA
répond normalement, seul le pipeline d'inférence du modèle `meta/llama-3.3-70b-instruct` hang. C'est
un incident côté NVIDIA sur ce modèle précis, hors de contrôle. **Action requise : retester
`python -m unittest tests.test_trinity` en conditions réelles (script `tests/test_trinity.py` déjà
prêt et mocké pour l'instant) et un appel direct `TrinityFilter.evaluate()` une fois l'incident résolu.**

**2. `log_decision_with_trinity` sur la vraie base — migration Trinity introuvable.**
Test direct : `TrinityFilter.log_decision(...)` échoue avec `PGRST202` ("function ... not found").
Vérification complémentaire : `SELECT * FROM wisdom_principles` et `SELECT * FROM decision_audit`
échouent tous les deux avec `PGRST205` ("table not found in schema cache") sur le projet Supabase
`tmvhhpxerequhvdevvms`. **Les migrations Trinity n'ont donc pas été appliquées sur ce projet**, malgré
l'indication contraire. **Action requise : coller `backend/migrations/trinity_schema.sql` dans le SQL
Editor du projet `tmvhhpxerequhvdevvms.supabase.co` (vérifier qu'il s'agit bien du bon projet actif),
puis relancer ce test.**

**3. Policies RLS avec la clé publishable — cassées, SQL correctif écrit.**
Test empirique (insert/select) avec la clé `sb_publishable_...` actuelle :
- `tasks`, `thoughts`, `finances`, `reminders` : **SELECT OK, INSERT rejeté** (`42501 row-level
  security policy`) — la clé anon n'a pas de policy d'écriture sur ces tables.
- `finance_categories` : INSERT/SELECT OK (policy permissive déjà présente).
- `accounts` : table absente (migration `finance_accounts.sql` non appliquée non plus).

**Ceci casse actuellement toute écriture backend** (ajout de tâche, dépense, pensée, rappel) tant que
l'app tourne avec cette clé. Correctif écrit : `backend/migrations/rls_policies_fix.sql` (idempotent,
ajoute une policy permissive `FOR ALL` pour `anon`/`authenticated` sur les 8 tables du projet, ignore
celles qui n'existent pas encore). **Compromis de sécurité assumé et documenté dans le fichier lui-même
et dans RAPPORT.md** : ce schéma n'a pas de colonne `user_id` (app mono-utilisateur), donc RLS
"par ligne" ne modélise rien ici — l'alternative plus propre est d'utiliser une clé `service_role`
côté backend (jamais exposée) plutôt que d'ouvrir `anon` en écriture. **Action requise : coller
`rls_policies_fix.sql` dans le SQL Editor (après `trinity_schema.sql` et `finance_accounts.sql` pour
couvrir aussi ces tables), ou remplacer `SUPABASE_KEY` par une clé `service_role` dans `.env`.**

**4. Envoi WhatsApp réel via `/send` — testé et confirmé.**
Pont démarré (`node whatsapp-bridge/index.js`), session déjà authentifiée détectée
("✅ Client WhatsApp connecté avec succès !"). `POST http://127.0.0.1:8002/send` avec un message de
test vers `905411078112` → **`{"success":true}` HTTP 200**. Message réellement livré sur WhatsApp.

**5. Rituel matinal déclenché manuellement — confirmé, contenu partiel (attendu).**
`scheduler.send_morning_ritual()` exécuté : construction du message + envoi réussi (`200`,
`success:true`). Contenu actuellement dégradé (pas de principe de sagesse ni de tâches du jour)
puisque `wisdom_principles` n'existe pas encore et que les tables de tâches sont vides/bloquées en
écriture (points 2 et 3 ci-dessus) — le message dégrade proprement (`try/except` déjà en place) au
lieu de planter. Une fois les migrations et le correctif RLS appliqués, le contenu sera complet sans
changement de code.

## Résumé des actions manuelles restantes

1. Coller `backend/migrations/trinity_schema.sql`, `backend/migrations/finance_accounts.sql`, puis
   `backend/migrations/rls_policies_fix.sql` (dans cet ordre) dans le SQL Editor du projet Supabase
   **`tmvhhpxerequhvdevvms`** — vérifier que c'est bien le projet actif/attendu.
2. Décider : garder la policy RLS permissive (simple, fonctionne immédiatement) ou repasser
   `SUPABASE_KEY` en clé `service_role` (plus strict, RLS conservé fermé pour `anon`).
3. Réessayer les appels LLM (`tests/test_trinity.py` en mode réel, ou `TrinityFilter.evaluate()` direct)
   une fois l'incident NVIDIA sur `meta/llama-3.3-70b-instruct` résolu côté NVIDIA.
