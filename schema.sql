-- =========================================================================
-- 1. Table : tasks (Gestion de la To-Do list et des priorités)
-- =========================================================================
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo' 
        CONSTRAINT chk_tasks_status CHECK (status IN ('todo', 'in_progress', 'done', 'backlog')),
    priority TEXT NOT NULL DEFAULT 'medium' 
        CONSTRAINT chk_tasks_priority CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);


-- =========================================================================
-- 2. Table : thoughts (Notes rapides, pensées et journal)
-- =========================================================================
CREATE TABLE thoughts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_thoughts_category ON thoughts(category);


-- =========================================================================
-- 3. Table : finances (Suivi des dépenses et entrées d'argent)
-- =========================================================================
CREATE TABLE finances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    type TEXT NOT NULL 
        CONSTRAINT chk_finances_type CHECK (type IN ('income', 'expense')),
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_finances_type_category ON finances(type, category);
CREATE INDEX idx_finances_created_at ON finances(created_at);


-- =========================================================================
-- 4. Table : reminders (Planification de rappels WhatsApp/Telegram)
-- =========================================================================
CREATE TABLE reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message TEXT NOT NULL,
    trigger_at TIMESTAMPTZ NOT NULL,
    is_sent BOOLEAN NOT NULL DEFAULT FALSE,
    channel TEXT NOT NULL 
        CONSTRAINT chk_reminders_channel CHECK (channel IN ('whatsapp', 'telegram')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reminders_trigger_is_sent ON reminders(trigger_at) WHERE is_sent = FALSE;
