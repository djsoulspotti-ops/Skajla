-- SKAILA Database Optimization - Safe Production Indexes
-- Only includes indexes for confirmed existing tables

-- ===== USER & AUTHENTICATION INDEXES =====
CREATE INDEX IF NOT EXISTS idx_utenti_email ON utenti(email);
CREATE INDEX IF NOT EXISTS idx_utenti_scuola_id ON utenti(scuola_id);
CREATE INDEX IF NOT EXISTS idx_utenti_ruolo ON utenti(ruolo);
CREATE INDEX IF NOT EXISTS idx_utenti_classe_id ON utenti(classe_id);
CREATE INDEX IF NOT EXISTS idx_utenti_status_online ON utenti(status_online);
CREATE INDEX IF NOT EXISTS idx_utenti_scuola_ruolo ON utenti(scuola_id, ruolo);

-- ===== GAMIFICATION INDEXES =====
CREATE INDEX IF NOT EXISTS idx_user_gamification_user_id ON user_gamification(user_id);
CREATE INDEX IF NOT EXISTS idx_user_gamification_current_level ON user_gamification(current_level);
CREATE INDEX IF NOT EXISTS idx_user_gamification_total_xp ON user_gamification(total_xp DESC);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_user_id ON daily_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date);

-- ===== MESSAGING INDEXES =====
CREATE INDEX IF NOT EXISTS idx_messaggi_timestamp ON messaggi(timestamp);

-- ===== REGISTRO ELETTRONICO INDEXES =====
CREATE INDEX IF NOT EXISTS idx_registro_voti_student_id ON registro_voti(student_id);
CREATE INDEX IF NOT EXISTS idx_registro_voti_subject ON registro_voti(subject);
CREATE INDEX IF NOT EXISTS idx_registro_voti_date ON registro_voti(date);
CREATE INDEX IF NOT EXISTS idx_registro_presenze_student_id ON registro_presenze(student_id);
CREATE INDEX IF NOT EXISTS idx_registro_presenze_date ON registro_presenze(date);
CREATE INDEX IF NOT EXISTS idx_registro_presenze_status ON registro_presenze(status);

-- ===== SCHOOL MANAGEMENT INDEXES =====
CREATE INDEX IF NOT EXISTS idx_classi_scuola_id ON classi(scuola_id);
CREATE INDEX IF NOT EXISTS idx_classi_nome ON classi(nome);
CREATE INDEX IF NOT EXISTS idx_scuole_nome ON scuole(nome);

-- ===== FEATURE FLAGS INDEXES =====
CREATE INDEX IF NOT EXISTS idx_school_features_school_id ON school_features(school_id);
CREATE INDEX IF NOT EXISTS idx_school_features_feature_name ON school_features(feature_name);
CREATE INDEX IF NOT EXISTS idx_school_features_enabled ON school_features(enabled);

-- ===== STUDY TIMER INDEXES =====
CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_session_type ON study_sessions(session_type);

-- ===== COMPOSITE INDEXES FOR COMMON QUERIES =====
CREATE INDEX IF NOT EXISTS idx_registro_voti_student_subject ON registro_voti(student_id, subject);
CREATE INDEX IF NOT EXISTS idx_registro_presenze_student_date ON registro_presenze(student_id, date);

-- ===== ANALYZE TABLES FOR QUERY PLANNER =====
ANALYZE utenti;
ANALYZE user_gamification;
ANALYZE messaggi;
ANALYZE registro_voti;
ANALYZE registro_presenze;
ANALYZE classi;
ANALYZE school_features;
ANALYZE study_sessions;

-- Success message
SELECT 'Safe database indexes created successfully!' as status;
