from flask import Blueprint, render_template, request, jsonify, session
from services.study_groups_service import study_groups_service
from shared.middleware.auth import require_login

study_groups_bp = Blueprint('study_groups', __name__)

@study_groups_bp.route('/study-groups')
@require_login
def study_groups_page():
    return render_template('study_groups.html', user=session)

@study_groups_bp.route('/api/study-groups', methods=['GET'])
@require_login
def get_user_groups():
    user_id = session.get('user_id')
    groups = study_groups_service.get_user_groups(user_id)
    return jsonify({'success': True, 'groups': groups})

@study_groups_bp.route('/api/study-groups', methods=['POST'])
@require_login
def create_group():
    user_id = session.get('user_id')
    data = request.get_json()
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Nome gruppo richiesto'}), 400
    
    if len(name) > 100:
        return jsonify({'success': False, 'error': 'Nome troppo lungo (max 100 caratteri)'}), 400
    
    result = study_groups_service.create_group(
        name=name,
        description=description,
        created_by=user_id,
        classe_id=session.get('classe_id'),
        scuola_id=session.get('scuola_id')
    )
    
    return jsonify(result)

@study_groups_bp.route('/api/study-groups/<int:group_id>', methods=['GET'])
@require_login
def get_group_details(group_id):
    user_id = session.get('user_id')
    group = study_groups_service.get_group_details(group_id, user_id)
    
    if not group:
        return jsonify({'success': False, 'error': 'Gruppo non trovato'}), 404
    
    members = study_groups_service.get_group_members(group_id)
    
    return jsonify({'success': True, 'group': group, 'members': members})

@study_groups_bp.route('/api/study-groups/<int:group_id>/members', methods=['GET'])
@require_login
def get_group_members(group_id):
    user_id = session.get('user_id')
    group = study_groups_service.get_group_details(group_id, user_id)
    if not group:
        return jsonify({'success': False, 'error': 'Non autorizzato'}), 403
    
    members = study_groups_service.get_group_members(group_id)
    return jsonify({'success': True, 'members': members})

@study_groups_bp.route('/api/study-groups/<int:group_id>/members', methods=['POST'])
@require_login
def add_member(group_id):
    user_id = session.get('user_id')
    data = request.get_json()
    new_member_id = data.get('user_id')
    
    if not new_member_id:
        return jsonify({'success': False, 'error': 'ID utente richiesto'}), 400
    
    result = study_groups_service.add_member(group_id, new_member_id, user_id)
    return jsonify(result)

@study_groups_bp.route('/api/study-groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
@require_login
def remove_member(group_id, member_id):
    user_id = session.get('user_id')
    result = study_groups_service.remove_member(group_id, member_id, user_id)
    return jsonify(result)

@study_groups_bp.route('/api/study-groups/<int:group_id>/messages', methods=['GET'])
@require_login
def get_messages(group_id):
    user_id = session.get('user_id')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    messages = study_groups_service.get_messages(group_id, user_id, limit, offset)
    
    formatted = []
    for msg in messages:
        formatted.append({
            'id': msg['id'],
            'content': msg['content'],
            'sender_id': msg['sender_id'],
            'sender_name': f"{msg['nome']} {msg['cognome']}",
            'sender_avatar': msg.get('avatar', 'default.jpg'),
            'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None,
            'message_type': msg.get('message_type', 'text')
        })
    
    return jsonify({'success': True, 'messages': formatted})

@study_groups_bp.route('/api/study-groups/<int:group_id>/messages', methods=['POST'])
@require_login
def send_message(group_id):
    user_id = session.get('user_id')
    data = request.get_json()
    
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'text')
    
    if not content:
        return jsonify({'success': False, 'error': 'Messaggio vuoto'}), 400
    
    result = study_groups_service.send_message(group_id, user_id, content, message_type)
    return jsonify(result)

@study_groups_bp.route('/api/study-groups/<int:group_id>/tasks', methods=['GET'])
@require_login
def get_tasks(group_id):
    user_id = session.get('user_id')
    tasks = study_groups_service.get_tasks(group_id, user_id)
    
    formatted = []
    for task in tasks:
        formatted.append({
            'id': task['id'],
            'title': task['title'],
            'description': task.get('description'),
            'due_date': task['due_date'].isoformat() if task.get('due_date') else None,
            'is_completed': task['is_completed'],
            'priority': task.get('priority', 'normal'),
            'creator_name': task.get('creator_name'),
            'completed_by_name': task.get('completed_by_name'),
            'created_at': task['created_at'].isoformat() if task.get('created_at') else None
        })
    
    return jsonify({'success': True, 'tasks': formatted})

@study_groups_bp.route('/api/study-groups/<int:group_id>/tasks', methods=['POST'])
@require_login
def add_task(group_id):
    user_id = session.get('user_id')
    data = request.get_json()
    
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    due_date = data.get('due_date')
    priority = data.get('priority', 'normal')
    
    if not title:
        return jsonify({'success': False, 'error': 'Titolo richiesto'}), 400
    
    result = study_groups_service.add_task(group_id, user_id, title, description, due_date, priority)
    return jsonify(result)

@study_groups_bp.route('/api/study-groups/tasks/<int:task_id>/toggle', methods=['POST'])
@require_login
def toggle_task(task_id):
    user_id = session.get('user_id')
    result = study_groups_service.toggle_task(task_id, user_id)
    return jsonify(result)

@study_groups_bp.route('/api/study-groups/classmates', methods=['GET'])
@require_login
def get_classmates():
    user_id = session.get('user_id')
    classe_id = session.get('classe_id')
    
    if not classe_id:
        return jsonify({'success': True, 'classmates': []})
    
    classmates = study_groups_service.get_classmates(user_id, classe_id)
    return jsonify({'success': True, 'classmates': classmates})
