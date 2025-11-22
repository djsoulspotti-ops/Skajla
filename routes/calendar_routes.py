from flask import Blueprint, request, jsonify, session, render_template
from shared.error_handling import handle_errors, ValidationError, AuthError, get_logger
from services.calendar.calendar_system import calendar_system
from middleware.auth_middleware import require_auth, require_role
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__)
logger = get_logger(__name__)

@calendar_bp.route('/calendar')
@require_auth
@handle_errors
def calendar_page():
    """Pagina principale calendario"""
    user = session.get('user')
    return render_template('calendar.html', user=user)

@calendar_bp.route('/api/calendar/events', methods=['GET'])
@require_auth
@handle_errors
def get_events():
    """API: Ottieni eventi utente"""
    user_id = session['user']['user_id']
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    events = calendar_system.get_user_events(user_id, start_date, end_date)
    
    user_scuola_id = session['user'].get('scuola_id')
    if user_scuola_id:
        school_events = calendar_system.get_school_wide_events(user_scuola_id, start_date, end_date)
        
        for event in school_events:
            events.append({
                'id': f'school_{event["id"]}',
                'event_type': 'school_event',
                'title': event['title'],
                'start_datetime': event['start_datetime'],
                'end_datetime': event['end_datetime'],
                'all_day': event['all_day'],
                'event_data': {
                    'description': event.get('description', ''),
                    'is_school_event': True
                },
                'editable': False
            })
    
    return jsonify({
        'success': True,
        'events': events
    })

@calendar_bp.route('/api/calendar/events', methods=['POST'])
@require_auth
@handle_errors
def create_event():
    """API: Crea nuovo evento"""
    user_id = session['user']['user_id']
    data = request.get_json()
    
    required_fields = ['title', 'start_datetime', 'event_type']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Campo obbligatorio mancante: {field}")
    
    event_data = data.get('event_data', {})
    
    if session['user']['ruolo'] == 'professore' and data['event_type'] == 'lesson':
        classe_id = session['user'].get('classe_id')
        if classe_id:
            event_data['class_id'] = classe_id
    
    result = calendar_system.create_event(
        user_id=user_id,
        event_type=data['event_type'],
        title=data['title'],
        start_datetime=data['start_datetime'],
        end_datetime=data.get('end_datetime'),
        event_data=event_data,
        all_day=data.get('all_day', False),
        recurrence=data.get('recurrence', 'none')
    )
    
    return jsonify({
        'success': True,
        'event_id': result['id'],
        'message': 'Evento creato con successo'
    })

@calendar_bp.route('/api/calendar/events/<int:event_id>', methods=['PUT'])
@require_auth
@handle_errors
def update_event(event_id):
    """API: Aggiorna evento"""
    user_id = session['user']['user_id']
    data = request.get_json()
    
    calendar_system.update_event(event_id, user_id, data)
    
    return jsonify({
        'success': True,
        'message': 'Evento aggiornato con successo'
    })

@calendar_bp.route('/api/calendar/events/<int:event_id>', methods=['DELETE'])
@require_auth
@handle_errors
def delete_event(event_id):
    """API: Elimina evento"""
    user_id = session['user']['user_id']
    
    calendar_system.delete_event(event_id, user_id)
    
    return jsonify({
        'success': True,
        'message': 'Evento eliminato con successo'
    })

@calendar_bp.route('/api/calendar/class/<int:class_id>', methods=['GET'])
@require_auth
@handle_errors
def get_class_schedule(class_id):
    """API: Ottieni orario classe (per studenti/professori)"""
    user = session['user']
    
    if user['ruolo'] not in ['studente', 'professore', 'dirigente']:
        raise AuthError("Non autorizzato")
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    events = calendar_system.get_class_schedule(class_id, start_date, end_date)
    
    return jsonify({
        'success': True,
        'events': events
    })

@calendar_bp.route('/api/calendar/school-event', methods=['POST'])
@require_role('dirigente')
@handle_errors
def create_school_event():
    """API: Crea evento scolastico globale (solo dirigente)"""
    user = session['user']
    scuola_id = user.get('scuola_id')
    
    if not scuola_id:
        raise ValidationError("Scuola non associata")
    
    data = request.get_json()
    
    required_fields = ['title', 'start_datetime', 'event_type']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Campo obbligatorio mancante: {field}")
    
    result = calendar_system.create_school_wide_event(
        scuola_id=scuola_id,
        created_by=user['user_id'],
        event_type=data['event_type'],
        title=data['title'],
        description=data.get('description', ''),
        start_datetime=data['start_datetime'],
        end_datetime=data.get('end_datetime'),
        all_day=data.get('all_day', True)
    )
    
    return jsonify({
        'success': True,
        'event_id': result['id'],
        'message': 'Evento scolastico creato con successo'
    })

@calendar_bp.route('/api/calendar/user/<int:user_id>', methods=['GET'])
@require_role('dirigente')
@handle_errors
def get_user_calendar(user_id):
    """API: Visualizza calendario di qualsiasi utente (solo dirigente)"""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    events = calendar_system.get_user_events(user_id, start_date, end_date)
    
    return jsonify({
        'success': True,
        'events': events
    })

@calendar_bp.route('/api/calendar/chatbot/update', methods=['POST'])
@require_auth
@handle_errors
def chatbot_update_schedule():
    """
    API per il Chatbot: Aggiorna calendario via linguaggio naturale
    
    Esempi:
    - { "action": "add", "day": "Tuesday", "time": "10:00", "subject": "Physics" }
    - { "action": "remove", "event_id": 123 }
    """
    user_id = session['user']['user_id']
    data = request.get_json()
    
    action = data.get('action')
    
    if action == 'add':
        day = data.get('day')
        time = data.get('time')
        subject = data.get('subject')
        
        if not all([day, time, subject]):
            raise ValidationError("day, time, subject sono obbligatori")
        
        start_datetime = f"2025-01-{_day_to_number(day)} {time}:00"
        
        result = calendar_system.create_event(
            user_id=user_id,
            event_type='lesson',
            title=subject,
            start_datetime=start_datetime,
            event_data={'added_by_chatbot': True}
        )
        
        return jsonify({
            'success': True,
            'message': f"✅ {subject} aggiunto {day} alle {time}",
            'event_id': result['id']
        })
    
    elif action == 'remove':
        event_id = data.get('event_id')
        if not event_id:
            raise ValidationError("event_id obbligatorio")
        
        calendar_system.delete_event(event_id, user_id)
        
        return jsonify({
            'success': True,
            'message': "✅ Evento rimosso"
        })
    
    else:
        raise ValidationError(f"Azione non supportata: {action}")

def _day_to_number(day: str) -> str:
    """Helper: Converte giorno in numero (semplificato)"""
    days = {
        'monday': '01', 'tuesday': '02', 'wednesday': '03',
        'thursday': '04', 'friday': '05', 'saturday': '06', 'sunday': '07'
    }
    return days.get(day.lower(), '01')
