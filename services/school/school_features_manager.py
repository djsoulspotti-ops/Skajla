
"""
SKAJLA - School Features Manager
Gestisce abilitazione/disabilitazione moduli per singola scuola
"""

from database_manager import db_manager
from typing import Dict, List, Optional

class SchoolFeaturesManager:
    """Gestisce le feature attive per ogni scuola"""
    
    # Feature disponibili
    AVAILABLE_FEATURES = {
        'gamification': {
            'name': 'Sistema Gamification',
            'description': 'XP, livelli, badge, classifiche e sfide',
            'routes': ['/gamification', '/crediti', '/api/gamification/*'],
            'default': True
        },
        'ai_coach': {
            'name': 'AI Coach & Chatbot',
            'description': 'Assistente AI per supporto studenti',
            'routes': ['/ai/*', '/chat'],
            'default': True
        },
        'registro_elettronico': {
            'name': 'Registro Elettronico',
            'description': 'Voti, presenze, note disciplinari',
            'routes': ['/registro', '/api/registro/*'],
            'default': True
        },
        'skaila_connect': {
            'name': 'SKAJLA Connect',
            'description': 'Orientamento carriera e aziende',
            'routes': ['/skaila-connect', '/api/companies/*'],
            'default': True
        },
        'materiali_didattici': {
            'name': 'Materiali Didattici',
            'description': 'Upload e condivisione materiali',
            'routes': ['/materiali', '/api/materials/*'],
            'default': True
        },
        'calendario': {
            'name': 'Calendario Scolastico',
            'description': 'Eventi, verifiche, compiti',
            'routes': ['/calendario', '/api/calendar/*'],
            'default': True
        },
        'analytics': {
            'name': 'Analytics & Reports',
            'description': 'Dashboard analytics e report',
            'routes': ['/reports', '/analytics'],
            'default': True
        }
    }
    
    def __init__(self):
        self._init_features_table()
    
    def _init_features_table(self):
        """Crea tabella per feature flags"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS school_features (
                        school_id INTEGER,
                        feature_name VARCHAR(50),
                        enabled BOOLEAN DEFAULT true,
                        enabled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        enabled_by INTEGER,
                        PRIMARY KEY (school_id, feature_name)
                    )
                ''')
                
                conn.commit()
                print("✅ Tabella school_features creata")
        except Exception as e:
            print(f"⚠️ Errore init features table: {e}")
    
    def get_school_features(self, school_id: int) -> Dict[str, bool]:
        """Ottieni feature abilitate per una scuola"""
        try:
            features = db_manager.query('''
                SELECT feature_name, enabled
                FROM school_features
                WHERE school_id = %s
            ''', (school_id,))
            
            # Se non ci sono impostazioni, usa default
            if not features:
                return {k: v['default'] for k, v in self.AVAILABLE_FEATURES.items()}
            
            feature_dict = {f['feature_name']: f['enabled'] for f in features}
            
            # Aggiungi feature mancanti con default
            for feature_name, feature_data in self.AVAILABLE_FEATURES.items():
                if feature_name not in feature_dict:
                    feature_dict[feature_name] = feature_data['default']
            
            return feature_dict
            
        except Exception as e:
            print(f"⚠️ Errore get_school_features: {e}")
            return {k: True for k in self.AVAILABLE_FEATURES.keys()}
    
    def is_feature_enabled(self, school_id: int, feature_name: str) -> bool:
        """Verifica se una feature è abilitata"""
        features = self.get_school_features(school_id)
        return features.get(feature_name, False)
    
    def enable_feature(self, school_id: int, feature_name: str, admin_id: int) -> bool:
        """Abilita una feature per una scuola"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO school_features (school_id, feature_name, enabled, enabled_by)
                    VALUES (%s, %s, true, %s)
                    ON CONFLICT (school_id, feature_name) DO UPDATE
                    SET enabled = true, enabled_at = CURRENT_TIMESTAMP, enabled_by = %s
                ''', (school_id, feature_name, admin_id, admin_id))
                
                conn.commit()
                print(f"✅ Feature '{feature_name}' abilitata per scuola {school_id}")
                return True
        except Exception as e:
            print(f"⚠️ Errore enable_feature: {e}")
            return False
    
    def disable_feature(self, school_id: int, feature_name: str, admin_id: int) -> bool:
        """Disabilita una feature per una scuola"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO school_features (school_id, feature_name, enabled, enabled_by)
                    VALUES (%s, %s, false, %s)
                    ON CONFLICT (school_id, feature_name) DO UPDATE
                    SET enabled = false, enabled_at = CURRENT_TIMESTAMP, enabled_by = %s
                ''', (school_id, feature_name, admin_id, admin_id))
                
                conn.commit()
                print(f"🚫 Feature '{feature_name}' disabilitata per scuola {school_id}")
                return True
        except Exception as e:
            print(f"⚠️ Errore disable_feature: {e}")
            return False
    
    def set_gamification_only(self, school_id: int, admin_id: int) -> bool:
        """Modalità 'Solo Gamification' - disabilita tutto tranne gamification"""
        try:
            for feature_name in self.AVAILABLE_FEATURES.keys():
                if feature_name == 'gamification':
                    self.enable_feature(school_id, feature_name, admin_id)
                else:
                    self.disable_feature(school_id, feature_name, admin_id)
            
            print(f"🎮 Scuola {school_id} configurata in modalità 'Solo Gamification'")
            return True
        except Exception as e:
            print(f"⚠️ Errore set_gamification_only: {e}")
            return False

school_features_manager = SchoolFeaturesManager()
