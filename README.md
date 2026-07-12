# OTIS — assistant multi-agents personnel

Assistant personnel autonome piloté depuis WhatsApp, mentor-stratège fusionnant trois sagesses
(Holiday / Hill / Goleman) via un filtre de décision ("Trinity") avant chaque action à enjeu.

## Architecture

```
WhatsApp ──▶ whatsapp-bridge/index.js (whatsapp-web.js) ──▶ server.py (FastAPI, /webhook)
                     ▲                                              │
                     │ POST /send (rituel matinal)                  ▼
              scheduler.py (APScheduler)              skills/orchestrator.py (MPCOrchestrator)
                                                                     │
                                              ┌──────────────────────┼──────────────────────┐
                                              ▼                      ▼                      ▼
                                     skills/trinity.py      skills/agents/            skills/thought_logger.py
                                     (filtre Holiday/         business_agent.py        skills/web_search.py
                                      Hill/Goleman)           productivity_agent.py
                                              │                      │
                                              ▼                      ▼
                                        Supabase (wisdom_principles,   Supabase (tasks, finances,
                                        decision_audit)                accounts, thoughts, reminders)
```

- **LLM** : Llama 3.3 70B via l'API NVIDIA (compatible OpenAI), client partagé dans `skills/llm_client.py`.
- **Orchestrateur** : `skills/orchestrator.py` (CEO Agent, boucle ReAct/function-calling), délègue à
  un registre d'agents (`AGENT_REGISTRY`) — `BusinessAgent` (CRM/support) et `ProductivityAgent`
  (tâches, jalons, calendrier, finances).
- **Trinity** : `skills/trinity.py` évalue chaque demande à enjeu en UN appel LLM (ego/clarté/foi/
  émotion), journalise dans `decision_audit`, et bloque l'exécution pour demander clarification si
  l'ego domine sans clarté du désir (`ego≥8` et `clarté≤4`).
- **Dashboard** : `dashboard.py` (Streamlit), lecture seule sur Supabase.
- **CLI** : `otis.py`, boucle interactive en console.

## Setup

```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.template .env       # puis remplir les valeurs
```

Variables requises (`.env.template`) : `SUPABASE_URL`, `SUPABASE_KEY`, `NVIDIA_API_KEY`,
`NVIDIA_MODEL`, `DATABASE_URL` (migrations SQL), `OTIS_OWNER_NUMBER`, `BRIDGE_SEND_URL`.

**Migrations** (SQL Editor Supabase si `DATABASE_URL` indisponible pour exécution automatisée) :
1. `schema.sql` (tasks, thoughts, finances, reminders)
2. `backend/migrations/trinity_schema.sql` (wisdom_principles, decision_audit + fonction + seed)
3. `backend/migrations/finance_accounts.sql` (comptes multiples)

**Lancer** :
```bash
python server.py                       # API webhook (port 8000)
cd whatsapp-bridge && node index.js    # pont WhatsApp (scan QR requis) + endpoint /send (port 8002)
python scheduler.py                    # rituel matinal 07:00 Europe/Istanbul
streamlit run dashboard.py             # dashboard
python otis.py                         # CLI interactif
```

**Tests** :
```bash
python -m unittest tests.test_trinity -v
```

## Phases livrées

| Phase | Contenu | Statut |
|---|---|---|
| 1 | Hygiène (suppression code mort, `.gitignore`, `requirements.txt`, `.env.template`) + GitHub | ✅ |
| 2 | Couche sagesse Trinity (schema SQL, filtre, personnalité OTIS) | ✅ code, ⚠️ migration SQL non exécutée en direct (voir BLOCKERS.md) |
| 3 | Skills finance/tâches étoffés + routing unifié (`llm_client.py`, registre d'agents) | ✅ |
| 4 | Pont WhatsApp (endpoint `/send`) + rituel matinal (APScheduler) + fix encodage Windows | ✅ code, ⚠️ envoi réel non testé (session WhatsApp requise) |
| 5 | Tests automatisés (mockés, déterministes), README, rapport final | ✅ |

Détail des limitations et décisions prises en autonomie : voir `BLOCKERS.md`.
Bilan complet : voir `RAPPORT.md`.
