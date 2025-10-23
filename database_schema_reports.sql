-- Tabella per salvare storico report aziendali
CREATE TABLE IF NOT EXISTS business_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(20) NOT NULL,  -- 'weekly' o 'monthly'
    period VARCHAR(100) NOT NULL,      -- Es: "18/12/2024 - 24/12/2024"
    data JSONB NOT NULL,                -- Dati completi del report
    recipient_email VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_successfully BOOLEAN DEFAULT FALSE
);

-- Indice per ricerche veloci
CREATE INDEX IF NOT EXISTS idx_business_reports_type ON business_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_business_reports_generated_at ON business_reports(generated_at DESC);

COMMENT ON TABLE business_reports IS 'Storico report aziendali settimanali e mensili SKAILA';
