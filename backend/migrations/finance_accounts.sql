-- =========================================================================
-- Comptes multiples pour finance_tracker.py (Phase 3, inspiration Firefly III)
-- =========================================================================
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    currency TEXT NOT NULL DEFAULT 'TRY',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- La table finances existante (schema.sql) recoit une reference optionnelle
-- vers un compte. Nullable pour ne pas casser les transactions existantes
-- non rattachees a un compte.
ALTER TABLE finances ADD COLUMN IF NOT EXISTS account_id UUID REFERENCES accounts(id);

CREATE INDEX IF NOT EXISTS idx_finances_account ON finances(account_id);

-- Compte par defaut utilise quand aucun compte n'est precise
INSERT INTO accounts (name, currency)
VALUES ('Principal', 'TRY')
ON CONFLICT (name) DO NOTHING;
