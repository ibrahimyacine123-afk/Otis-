-- =========================================================================
-- TRINITY WISDOM LAYER — wisdom_principles + decision_audit
-- =========================================================================
-- A executer une seule fois sur la base Supabase (SQL Editor si DATABASE_URL
-- n'est pas disponible pour une execution automatisee).

-- =========================================================================
-- 1. Table : wisdom_principles
-- =========================================================================
CREATE TABLE IF NOT EXISTS wisdom_principles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL
        CONSTRAINT chk_wisdom_source CHECK (source IN ('Ego is Enemy', 'Think and Grow Rich', 'Emotional Intelligence')),
    chapter TEXT,
    principle_name TEXT NOT NULL,
    principle_text TEXT NOT NULL,
    application_domain TEXT[] DEFAULT '{}',
    agent_focus TEXT,
    trigger_scenario TEXT,
    action_framework TEXT,
    priority INT NOT NULL DEFAULT 5
        CONSTRAINT chk_wisdom_priority CHECK (priority BETWEEN 1 AND 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wisdom_source ON wisdom_principles(source);
CREATE INDEX IF NOT EXISTS idx_wisdom_priority ON wisdom_principles(priority DESC);


-- =========================================================================
-- 2. Table : decision_audit
-- =========================================================================
CREATE TABLE IF NOT EXISTS decision_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL,
    decision_name TEXT NOT NULL,
    decision_context JSONB DEFAULT '{}'::jsonb,
    ego_test_score INT
        CONSTRAINT chk_audit_ego CHECK (ego_test_score BETWEEN 1 AND 10),
    desire_clarity_score INT
        CONSTRAINT chk_audit_clarity CHECK (desire_clarity_score BETWEEN 1 AND 10),
    faith_score INT
        CONSTRAINT chk_audit_faith CHECK (faith_score BETWEEN 1 AND 10),
    emotion_identified TEXT,
    emotion_score INT
        CONSTRAINT chk_audit_emotion CHECK (emotion_score BETWEEN 1 AND 10),
    decision_outcome TEXT NOT NULL DEFAULT 'Pending'
        CONSTRAINT chk_audit_outcome CHECK (decision_outcome IN ('Pending', 'Success', 'Partial Success', 'Learning', 'Failed', 'Rejected')),
    outcome_rationale TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_agent ON decision_audit(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_outcome ON decision_audit(decision_outcome);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON decision_audit(created_at);


-- =========================================================================
-- 3. Fonction : log_decision_with_trinity
-- =========================================================================
CREATE OR REPLACE FUNCTION log_decision_with_trinity(
    p_agent_id TEXT,
    p_decision_name TEXT,
    p_decision_context JSONB,
    p_ego_test_score INT,
    p_desire_clarity_score INT,
    p_faith_score INT,
    p_emotion_identified TEXT,
    p_emotion_score INT
) RETURNS decision_audit AS $$
DECLARE
    result decision_audit;
BEGIN
    INSERT INTO decision_audit (
        agent_id, decision_name, decision_context,
        ego_test_score, desire_clarity_score, faith_score,
        emotion_identified, emotion_score
    ) VALUES (
        p_agent_id, p_decision_name, p_decision_context,
        p_ego_test_score, p_desire_clarity_score, p_faith_score,
        p_emotion_identified, p_emotion_score
    )
    RETURNING * INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;


-- =========================================================================
-- 4. Seed : 6 principes fondateurs (2 par source)
-- Textes redigés par OTIS, fideles a l'esprit des ouvrages, non copies mot pour mot.
-- =========================================================================
INSERT INTO wisdom_principles (source, chapter, principle_name, principle_text, application_domain, agent_focus, trigger_scenario, action_framework, priority)
VALUES
(
    'Ego is Enemy',
    'Aspire',
    'Who Decides?',
    'Le succes durable vient de ceux qui font le travail pour le travail lui-meme, pas pour l''image qu''il projette. Avant d''agir, demande-toi : est-ce l''ego qui parle, ou la tache qui le demande ?',
    ARRAY['decision', 'finance', 'strategie'],
    'Orchestrator',
    'L''utilisateur veut agir vite ou impressionner plutot que construire methodiquement.',
    '1) Nomme ce que l''ego cherche a prouver. 2) Demande ce que la tache exige reellement. 3) Compare les deux avant d''agir.',
    8
),
(
    'Ego is Enemy',
    'Failure',
    'Failure as Teacher',
    'L''echec n''est pas une sentence, c''est un professeur froid et honnete. L''ego veut fuir la lecon ; la sagesse s''assoit et prend des notes.',
    ARRAY['finance', 'apprentissage', 'strategie'],
    'ProductivityAgent',
    'Un objectif ou une tache echoue et l''utilisateur cherche a en minimiser ou en rejeter la cause.',
    '1) Reconnais l''echec sans dramatiser ni minimiser. 2) Extrais une lecon concrete. 3) Ajuste le plan, pas l''ego.',
    7
),
(
    'Think and Grow Rich',
    'Desire',
    'Burning Desire',
    'Un souhait vague ne produit rien. Le desir doit etre precis : montant exact, date exacte, methode exacte — sinon ce n''est qu''un voeu pieux.',
    ARRAY['finance', 'objectifs', 'decision'],
    'Orchestrator',
    'L''utilisateur exprime un objectif flou ("je veux gagner plus d''argent", "je veux reussir").',
    '1) Exige un montant chiffre. 2) Exige une date limite. 3) Exige une methode concrete. Sans les trois, le desir reste une intention.',
    9
),
(
    'Think and Grow Rich',
    'Faith',
    'Belief Precedes Action',
    'La foi transforme le desir en realite en chargeant la pensee d''une intention absolue. Sans croyance reelle dans le resultat, meme le plan le plus solide reste lettre morte.',
    ARRAY['finance', 'objectifs', 'motivation'],
    'ProductivityAgent',
    'L''utilisateur a un plan clair mais doute de pouvoir l''executer ou l''atteindre.',
    '1) Fais verbaliser la croyance reelle (score de foi). 2) Si elle est basse, adresse le doute avant le plan. 3) Renforce par des preuves passees, pas des slogans.',
    7
),
(
    'Emotional Intelligence',
    'Self-Awareness',
    'Name Your Emotion',
    'Nommer une emotion la transforme d''ordre impulsif en donnee exploitable. "Je ressens de la peur" est une information ; "j''ai peur donc je dois" est un piege.',
    ARRAY['communication', 'decision', 'finance'],
    'Orchestrator',
    'Une decision est prise sous le coup d''une emotion forte (peur, excitation, colere, avidite).',
    '1) Identifie l''emotion precise. 2) Score son intensite (1-10). 3) Separe l''emotion de la decision : l''une informe, l''autre doit rester rationnelle.',
    9
),
(
    'Emotional Intelligence',
    'Empathy',
    'Empathy First',
    'Comprendre ce que l''autre ressent avant de repondre change la nature de toute decision relationnelle. L''intelligence emotionnelle commence par l''ecoute, pas par la reaction.',
    ARRAY['communication', 'crm', 'relations'],
    'BusinessAgent',
    'Un echange avec un client, prospect ou proche est tendu ou charge emotionnellement.',
    '1) Ecoute et reformule sans juger. 2) Nomme l''emotion percue chez l''autre. 3) Reponds a l''emotion avant de repondre au contenu.',
    6
);
