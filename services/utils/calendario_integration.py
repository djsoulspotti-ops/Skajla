"""
Sistema Calendario Integrato con Coaching SKAJLA
Pianificazione intelligente studio basata su scadenze reali
"""

from database_manager import db_manager
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

class CalendarioIntegration:
    """
    Gestisce calendario eventi e integrazione con pianificazione studio
    """
    
    def __init__(self):
        self.event_types = ['verifica', 'compito', 'scadenza', 'evento', 'studio', 'ripasso']
        self.priority_weights = {
            'verifica': 10,
            'scadenza': 9,
            'compito': 8,
            'ripasso': 6,
            'studio': 5,
            'evento': 3
        }
    
    def get_upcoming_events(self, user_id: int, days_ahead: int = 14) -> List[Dict]:
        """Ottiene eventi prossimi per lo studente"""
        try:
            events = db_manager.query('''
                SELECT id, tipo, titolo, descrizione, materia, data_inizio, data_fine, priorita, completato
                FROM calendario_eventi
                WHERE (studente_id = %s OR studente_id IS NULL)
                AND data_inizio >= CURRENT_DATE
                AND data_inizio <= CURRENT_DATE + INTERVAL '%s days'
                AND completato = FALSE
                ORDER BY data_inizio ASC, priorita DESC
            ''', (user_id, days_ahead))
            
            return [dict(e) for e in events] if events else []
        
        except Exception as e:
            logger.error(
                event_type='calendar_query_failed',
                message='Failed to retrieve upcoming events from database',
                domain='calendar',
                user_id=user_id,
                days_ahead=days_ahead,
                error=str(e),
                exc_info=True
            )
            return []
    
    def get_critical_deadlines(self, user_id: int, days: int = 7) -> List[Dict]:
        """Ottiene solo scadenze critiche (verifiche, scadenze)"""
        try:
            events = db_manager.query('''
                SELECT id, tipo, titolo, materia, data_inizio, priorita
                FROM calendario_eventi
                WHERE (studente_id = %s OR studente_id IS NULL)
                AND tipo IN ('verifica', 'scadenza', 'compito')
                AND data_inizio >= CURRENT_DATE
                AND data_inizio <= CURRENT_DATE + INTERVAL '%s days'
                AND completato = FALSE
                ORDER BY data_inizio ASC
            ''', (user_id, days))
            
            return [dict(e) for e in events] if events else []
        
        except Exception as e:
            logger.error(
                event_type='critical_deadlines_query_failed',
                message='Failed to retrieve critical deadlines from database',
                domain='calendar',
                user_id=user_id,
                days=days,
                error=str(e),
                exc_info=True
            )
            return []
    
    def calculate_study_load(self, user_id: int) -> Dict[str, Any]:
        """Calcola carico studio prossimi giorni"""
        deadlines = self.get_critical_deadlines(user_id, 7)
        
        load = {
            'total_events': len(deadlines),
            'by_day': {},
            'by_subject': {},
            'stress_level': 'low'
        }
        
        # Raggruppa per giorno
        for event in deadlines:
            date_str = event['data_inizio'].strftime('%Y-%m-%d')
            if date_str not in load['by_day']:
                load['by_day'][date_str] = []
            load['by_day'][date_str].append(event)
            
            # Raggruppa per materia
            materia = event.get('materia', 'Altro')
            if materia:
                load['by_subject'][materia] = load['by_subject'].get(materia, 0) + 1
        
        # Calcola stress level
        if len(deadlines) >= 5:
            load['stress_level'] = 'high'
        elif len(deadlines) >= 3:
            load['stress_level'] = 'medium'
        
        return load
    
    def generate_smart_schedule(self, user_id: int, student_data: Dict) -> Dict[str, Any]:
        """
        Genera schedule studio intelligente basato su:
        - Scadenze calendario
        - Materie deboli dello studente
        - Carico studio attuale
        """
        deadlines = self.get_critical_deadlines(user_id, 14)
        study_load = self.calculate_study_load(user_id)
        
        schedule = {
            'duration': '7 giorni',
            'daily_plan': [],
            'priority_subjects': [],
            'total_study_hours': 0,
            'tips': []
        }
        
        # Identifica materie prioritarie (scadenze vicine + materie deboli)
        weak_subjects = student_data.get('academic', {}).get('weak_subjects', [])
        upcoming_subjects = [d.get('materia') for d in deadlines[:3] if d.get('materia')]
        
        # Combina e deduplica
        priority_subjects = list(set(upcoming_subjects + weak_subjects))
        schedule['priority_subjects'] = priority_subjects[:3]
        
        # Genera piano giornaliero per prossimi 7 giorni
        for day_offset in range(7):
            target_date = datetime.now().date() + timedelta(days=day_offset)
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Eventi del giorno
            day_events = study_load['by_day'].get(date_str, [])
            
            # Decide ore studio
            if len(day_events) >= 2:
                study_hours = 3.0  # Giorno pesante
            elif len(day_events) == 1:
                study_hours = 2.0  # Giorno medio
            else:
                study_hours = 1.5  # Giorno leggero
            
            schedule['total_study_hours'] += study_hours
            
            # Piano giornaliero
            day_plan = {
                'date': date_str,
                'day_name': target_date.strftime('%A'),
                'events': [e['titolo'] for e in day_events],
                'recommended_hours': study_hours,
                'focus_subjects': []
            }
            
            # Assegna materie focus
            if day_events:
                # Studia materie delle scadenze
                day_plan['focus_subjects'] = [e.get('materia') for e in day_events if e.get('materia')]
            elif priority_subjects:
                # Studia materie deboli
                day_plan['focus_subjects'] = [priority_subjects[day_offset % len(priority_subjects)]]
            
            schedule['daily_plan'].append(day_plan)
        
        # Suggerimenti basati su carico
        if study_load['stress_level'] == 'high':
            schedule['tips'] = [
                "⚠️ Carico studio elevato - priorità assoluta alle scadenze",
                "🍅 Usa tecnica Pomodoro (25min focus + 5min pausa)",
                "😴 Dormi almeno 7 ore per consolidare apprendimento",
                "🤝 Chiedi aiuto ai professori se necessario"
            ]
        elif study_load['stress_level'] == 'medium':
            schedule['tips'] = [
                "📅 Distribisci lo studio nei prossimi giorni",
                "🎯 Focus su materie delle prossime verifiche",
                "📝 Crea schemi e mappe concettuali",
                "⏰ Pianifica pause regolari"
            ]
        else:
            schedule['tips'] = [
                "✅ Carico gestibile - ottimo momento per consolidare",
                "🔄 Ripassa argomenti passati (spaced repetition)",
                "💪 Lavora sulle materie deboli",
                "🎮 Mantieni il tuo streak attivo"
            ]
        
        return schedule
    
    def add_event(self, event_data: Dict) -> bool:
        """Aggiunge evento al calendario"""
        try:
            db_manager.execute('''
                INSERT INTO calendario_eventi 
                (tipo, titolo, descrizione, materia, data_inizio, data_fine, 
                 studente_id, priorita)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                event_data.get('tipo'),
                event_data.get('titolo'),
                event_data.get('descrizione'),
                event_data.get('materia'),
                event_data.get('data_inizio'),
                event_data.get('data_fine'),
                event_data.get('studente_id'),
                event_data.get('priorita', 5)
            ))
            return True
        except Exception as e:
            logger.error(
                event_type='calendar_event_creation_failed',
                message='Failed to add event to calendar',
                domain='calendar',
                event_type_value=event_data.get('tipo'),
                event_title=event_data.get('titolo'),
                student_id=event_data.get('studente_id'),
                error=str(e),
                exc_info=True
            )
            return False
    
    def mark_completed(self, event_id: int, user_id: int) -> bool:
        """Marca evento come completato"""
        try:
            db_manager.execute('''
                UPDATE calendario_eventi 
                SET completato = TRUE
                WHERE id = %s AND (studente_id = %s OR studente_id IS NULL)
            ''', (event_id, user_id))
            return True
        except Exception as e:
            logger.error(
                event_type='calendar_event_update_failed',
                message='Failed to mark calendar event as completed',
                domain='calendar',
                event_id=event_id,
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    def get_calendar_summary(self, user_id: int) -> str:
        """Genera summary testuale calendario per chatbot"""
        deadlines = self.get_critical_deadlines(user_id, 7)
        
        if not deadlines:
            return "📅 Nessuna scadenza imminente - ottimo momento per consolidare!"
        
        summary_parts = [f"📅 **Prossime scadenze ({len(deadlines)}):**\n"]
        
        for i, event in enumerate(deadlines[:5], 1):
            date = event['data_inizio'].strftime('%d/%m')
            tipo_emoji = {
                'verifica': '📝',
                'compito': '📄',
                'scadenza': '⏰',
                'ripasso': '🔄'
            }.get(event['tipo'], '📌')
            
            materia = event.get('materia', 'Generale')
            summary_parts.append(
                f"{i}. {tipo_emoji} {date} - {event['titolo']} ({materia})"
            )
        
        if len(deadlines) > 5:
            summary_parts.append(f"\n...e altre {len(deadlines) - 5} scadenze")
        
        return '\n'.join(summary_parts)

# Istanza globale
calendario = CalendarioIntegration()
