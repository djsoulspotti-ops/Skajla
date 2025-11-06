-- SKAILA Database Optimization - Production Indexes
-- Task 5: Database optimization for improved performance

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
CREATE INDEX IF NOT EXISTS idx_xp_history_user_id ON xp_history(user_id);
CREATE INDEX IF NOT EXISTS idx_xp_history_created_at ON xp_history(created_at);
CREATE INDEX IF NOT EXISTS idx_user_gamification_total_xp ON user_gamification(total_xp DESC);

-- ===== MESSAGING INDEXES =====
CREATE INDEX IF NOT EXISTS idx_messaggi_room_id ON messaggi(room_id);
CREATE INDEX IF NOT EXISTS idx_messaggi_sender_id ON messaggi(sender_id);
CREATE INDEX IF NOT EXISTS idx_messaggi_timestamp ON messaggi(timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_rooms_type ON chat_rooms(type);
CREATE INDEX IF NOT EXISTS idx_chat_rooms_created_by ON chat_rooms(created_by);

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
CREATE INDEX IF NOT EXISTS idx_docenti_classi_professore_id ON docenti_classi(professore_id);
CREATE INDEX IF NOT EXISTS idx_docenti_classi_classe_id ON docenti_classi(classe_id);

-- ===== FEATURE FLAGS INDEXES =====
CREATE INDEX IF NOT EXISTS idx_school_features_school_id ON school_features(school_id);
CREATE INDEX IF NOT EXISTS idx_school_features_feature_name ON school_features(feature_name);
CREATE INDEX IF NOT EXISTS idx_school_features_enabled ON school_features(enabled);

-- ===== COMPOSITE INDEXES FOR COMMON QUERIES =====
CREATE INDEX IF NOT EXISTS idx_messaggi_room_timestamp ON messaggi(room_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_registro_voti_student_subject ON registro_voti(student_id, subject);
CREATE INDEX IF NOT EXISTS idx_registro_presenze_student_date ON registro_presenze(student_id, date);
CREATE INDEX IF NOT EXISTS idx_utenti_scuola_online ON utenti(scuola_id, status_online) WHERE status_online = TRUE;

-- ===== ANALYZE TABLES FOR QUERY PLANNER =====
ANALYZE utenti;
ANALYZE user_gamification;
ANALYZE messaggi;
ANALYZE chat_rooms;
ANALYZE registro_voti;
ANALYZE registro_presenze;
ANALYZE classi;
ANALYZE school_features;

-- Success message
SELECT 'Database indexes created successfully!' as status;
