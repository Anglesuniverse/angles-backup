-- Skapa decision_vault tabell i Supabase
-- Kör detta SQL-script i din Supabase SQL Editor

CREATE TABLE IF NOT EXISTS decision_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    beslut TEXT NOT NULL,
    datum DATE NOT NULL DEFAULT CURRENT_DATE,
    typ TEXT NOT NULL,
    aktivt BOOLEAN NOT NULL DEFAULT true,
    kommentar TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT decision_vault_beslut_not_empty CHECK (LENGTH(TRIM(beslut)) > 0),
    CONSTRAINT decision_vault_typ_not_empty CHECK (LENGTH(TRIM(typ)) > 0),
    CONSTRAINT decision_vault_typ_valid CHECK (typ IN ('strategi', 'teknik', 'etik', 'arkitektur', 'process', 'säkerhet', 'annat'))
);

-- Skapa index för bättre prestanda
CREATE INDEX IF NOT EXISTS idx_decision_vault_datum ON decision_vault(datum DESC);
CREATE INDEX IF NOT EXISTS idx_decision_vault_typ ON decision_vault(typ);
CREATE INDEX IF NOT EXISTS idx_decision_vault_aktivt ON decision_vault(aktivt);
CREATE INDEX IF NOT EXISTS idx_decision_vault_created_at ON decision_vault(created_at DESC);

-- Skapa trigger för att uppdatera updated_at automatiskt
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_decision_vault_updated_at 
    BEFORE UPDATE ON decision_vault 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Lägg till test-data för att verifiera att tabellen fungerar
INSERT INTO decision_vault (beslut, datum, typ, aktivt, kommentar) VALUES 
('Vi använder PostgreSQL som primär databas för bättre prestanda', CURRENT_DATE, 'teknik', true, 'Beslut taget efter prestanda-analys'),
('Implementera Code Review för alla pull requests', CURRENT_DATE - INTERVAL '1 day', 'process', true, 'Förbättrar kodkvalitet och kunskapsdelning'),
('Använd HTTPS för all kommunikation', CURRENT_DATE - INTERVAL '2 days', 'säkerhet', true, 'Krav från säkerhetsavdelningen');

-- Visa tabellstruktur
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'decision_vault'
ORDER BY ordinal_position;