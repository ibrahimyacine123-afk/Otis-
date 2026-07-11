-- 1. Création de la table des jalons (Milestones) pour la productivité
CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ajout de la colonne milestone_id à la table tasks
ALTER TABLE tasks 
ADD COLUMN milestone_id UUID REFERENCES milestones(id) ON DELETE SET NULL;

CREATE INDEX idx_tasks_milestone ON tasks(milestone_id);

-- 2. Création de la table des catégories financières strictes
CREATE TABLE finance_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense', 'both')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insertion de quelques catégories par défaut
INSERT INTO finance_categories (name, type) VALUES 
('Alimentation', 'expense'),
('Logement', 'expense'),
('Transports', 'expense'),
('Loisirs', 'expense'),
('Salaire', 'income'),
('Investissement', 'both')
ON CONFLICT DO NOTHING;

-- Ajout de la colonne category_id à la table finances
-- Pour la compatibilité, on peut garder l'ancienne colonne texte ou la remplacer.
-- On ajoute category_id et on pourra supprimer category plus tard si souhaité.
ALTER TABLE finances 
ADD COLUMN category_id UUID REFERENCES finance_categories(id) ON DELETE RESTRICT;

CREATE INDEX idx_finances_category_id ON finances(category_id);
