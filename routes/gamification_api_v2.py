"""
Gamification API V2 - Advanced gamification endpoints
Complete API for profile, challenges, badges, leaderboards, kudos, and power-ups
"""

from flask import Blueprint, jsonify, request, session
from functools import wraps
import json
from datetime import datetime
from services.database.database_manager import db_manager
from services.gamification.xp_manager_v2 import xp_manager_v2
from services.gamification.challenge_manager_v2 import challenge_manager_v2
from services.gamification.advanced_gamification import RANK_CONFIG, RANK_ORDER
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

gamification_api_bp = Blueprint('gamification_api_v2', __name__, url_prefix='/api/gamification/v2')


# =============================================================================
# AUTH DECORATOR
# =============================================================================

def require_auth(f):
    """Require authentication for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non autenticato'}), 401
        request.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# USER PROFILE & STATS
# =============================================================================

@gamification_api_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get complete gamification profile for current user"""
    try:
        profile = xp_manager_v2.get_user_profile(request.user_id)
        if not profile:
            return jsonify({'error': 'Profilo non trovato'}), 404
        return jsonify(profile), 200
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get user statistics"""
    try:
        stats = xp_manager_v2.get_user_stats(request.user_id)
        if not stats:
            return jsonify({'error': 'Statistiche non trovate'}), 404
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/ranks', methods=['GET'])
def get_ranks():
    """Get all available ranks and their requirements"""
    ranks = []
    for rank_name in RANK_ORDER:
        config = RANK_CONFIG[rank_name]
        ranks.append({
            'nome': rank_name,
            'min_xp': config['min_xp'],
            'icon': config['icon'],
            'color': config['color']
        })
    return jsonify(ranks), 200


# =============================================================================
# CHALLENGES
# =============================================================================

@gamification_api_bp.route('/challenges/active', methods=['GET'])
@require_auth
def get_active_challenges():
    """Get all active challenges for user"""
    try:
        sfide = challenge_manager_v2.get_sfide_attive(request.user_id)
        return jsonify(sfide), 200
    except Exception as e:
        logger.error(f"Error getting challenges: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/challenges/daily', methods=['GET'])
@require_auth
def get_daily_challenge():
    """Get today's daily challenge"""
    try:
        sfida = challenge_manager_v2.get_sfida_giornaliera(request.user_id)
        
        # If no challenge assigned, assign one
        if not sfida:
            result = challenge_manager_v2.assegna_sfida_giornaliera(request.user_id)
            sfida = result.get('challenge') if result.get('success') else None
        
        return jsonify(sfida), 200
    except Exception as e:
        logger.error(f"Error getting daily challenge: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/challenges/weekly', methods=['GET'])
@require_auth
def get_weekly_challenges():
    """Get this week's challenges"""
    try:
        sfide = challenge_manager_v2.get_sfide_settimanali(request.user_id)
        
        # If no challenges assigned, assign them
        if not sfide:
            result = challenge_manager_v2.assegna_sfide_settimanali(request.user_id)
            sfide = result.get('challenges', []) if result.get('success') else []
        
        return jsonify(sfide), 200
    except Exception as e:
        logger.error(f"Error getting weekly challenges: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# BADGES
# =============================================================================

@gamification_api_bp.route('/badges', methods=['GET'])
@require_auth
def get_badges():
    """Get user's badges (owned and available)"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get owned badges
            cursor.execute('''
                SELECT b.id, b.codice, b.nome, b.descrizione, b.icon, 
                       b.rarita, ub.unlocked_at
                FROM user_badges_v2 ub
                JOIN badges_v2 b ON ub.badge_id = b.id
                WHERE ub.user_id = %s
                ORDER BY ub.unlocked_at DESC
            ''', (request.user_id,))
            
            owned = []
            for row in cursor.fetchall():
                owned.append({
                    'id': row[0],
                    'codice': row[1],
                    'nome': row[2],
                    'descrizione': row[3],
                    'icon': row[4],
                    'rarita': row[5],
                    'sbloccato': True,
                    'unlocked_at': row[6].isoformat() if row[6] else None
                })
            
            owned_ids = [b['id'] for b in owned]
            
            # Get available badges (not owned, not secret)
            if owned_ids:
                cursor.execute('''
                    SELECT id, codice, nome, descrizione, icon, rarita, condizioni
                    FROM badges_v2
                    WHERE id NOT IN %s AND segreto = FALSE
                    ORDER BY rarita, nome
                ''', (tuple(owned_ids),))
            else:
                cursor.execute('''
                    SELECT id, codice, nome, descrizione, icon, rarita, condizioni
                    FROM badges_v2
                    WHERE segreto = FALSE
                    ORDER BY rarita, nome
                ''')
            
            available = []
            for row in cursor.fetchall():
                available.append({
                    'id': row[0],
                    'codice': row[1],
                    'nome': row[2],
                    'descrizione': row[3],
                    'icon': row[4],
                    'rarita': row[5],
                    'sbloccato': False,
                    'condizioni': row[6]
                })
            
            return jsonify({
                'posseduti': owned,
                'da_sbloccare': available,
                'totale_posseduti': len(owned),
                'totale_disponibili': len(owned) + len(available)
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting badges: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# LEADERBOARDS
# =============================================================================

@gamification_api_bp.route('/leaderboard/<tipo>', methods=['GET'])
@require_auth
def get_leaderboard(tipo):
    """
    Get leaderboard
    Types: 'giornaliera', 'settimanale', 'mensile', 'stagionale', 'lifetime'
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        
        xp_columns = {
            'giornaliera': 'xp_giornaliero',
            'settimanale': 'xp_settimanale',
            'mensile': 'xp_mensile',
            'stagionale': 'xp_stagionale',
            'lifetime': 'xp_lifetime'
        }
        
        xp_col = xp_columns.get(tipo, 'xp_lifetime')
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get leaderboard entries
            cursor.execute(f'''
                SELECT l.user_id, l.{xp_col}, u.rango, u.avatar_id, u.titolo,
                       ut.nome, ut.cognome
                FROM leaderboards_v2 l
                JOIN user_gamification_v2 u ON l.user_id = u.user_id
                LEFT JOIN utenti ut ON l.user_id = ut.id
                ORDER BY l.{xp_col} DESC
                LIMIT %s
            ''', (limit,))
            
            leaderboard = []
            for idx, row in enumerate(cursor.fetchall()):
                leaderboard.append({
                    'posizione': idx + 1,
                    'user_id': row[0],
                    'xp': row[1],
                    'rango': row[2],
                    'avatar_id': row[3],
                    'titolo': row[4],
                    'nome': f"{row[5] or ''} {row[6] or ''}".strip() or f"Utente {row[0]}",
                    'is_you': row[0] == request.user_id
                })
            
            # Get current user's position
            cursor.execute(f'''
                SELECT COUNT(*) + 1 FROM leaderboards_v2
                WHERE {xp_col} > (SELECT {xp_col} FROM leaderboards_v2 WHERE user_id = %s)
            ''', (request.user_id,))
            user_position = cursor.fetchone()[0]
            
            cursor.execute(f'''
                SELECT {xp_col} FROM leaderboards_v2 WHERE user_id = %s
            ''', (request.user_id,))
            user_xp_row = cursor.fetchone()
            user_xp = user_xp_row[0] if user_xp_row else 0
            
            return jsonify({
                'tipo': tipo,
                'leaderboard': leaderboard,
                'user_position': user_position,
                'user_xp': user_xp,
                'total_users': len(leaderboard)
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/leaderboard/smart', methods=['GET'])
@require_auth
def get_smart_leaderboard():
    """Smart leaderboard: top 3 + nearby positions"""
    try:
        tipo = request.args.get('tipo', 'lifetime')
        
        xp_columns = {
            'settimanale': 'xp_settimanale',
            'mensile': 'xp_mensile',
            'stagionale': 'xp_stagionale',
            'lifetime': 'xp_lifetime'
        }
        
        xp_col = xp_columns.get(tipo, 'xp_lifetime')
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get top 3
            cursor.execute(f'''
                SELECT l.user_id, l.{xp_col}, u.rango, u.avatar_id, u.titolo,
                       ut.nome, ut.cognome
                FROM leaderboards_v2 l
                JOIN user_gamification_v2 u ON l.user_id = u.user_id
                LEFT JOIN utenti ut ON l.user_id = ut.id
                ORDER BY l.{xp_col} DESC
                LIMIT 3
            ''')
            
            top3 = []
            for idx, row in enumerate(cursor.fetchall()):
                top3.append({
                    'posizione': idx + 1,
                    'user_id': row[0],
                    'xp': row[1],
                    'rango': row[2],
                    'avatar_id': row[3],
                    'titolo': row[4],
                    'nome': f"{row[5] or ''} {row[6] or ''}".strip() or f"Utente {row[0]}",
                    'is_you': row[0] == request.user_id
                })
            
            # Get user position
            cursor.execute(f'''
                SELECT {xp_col} FROM leaderboards_v2 WHERE user_id = %s
            ''', (request.user_id,))
            user_xp_row = cursor.fetchone()
            user_xp = user_xp_row[0] if user_xp_row else 0
            
            cursor.execute(f'''
                SELECT COUNT(*) + 1 FROM leaderboards_v2
                WHERE {xp_col} > %s
            ''', (user_xp,))
            user_position = cursor.fetchone()[0]
            
            # Get 2 above and 2 below
            cursor.execute(f'''
                SELECT l.user_id, l.{xp_col}, u.rango, u.avatar_id, u.titolo,
                       ut.nome, ut.cognome
                FROM leaderboards_v2 l
                JOIN user_gamification_v2 u ON l.user_id = u.user_id
                LEFT JOIN utenti ut ON l.user_id = ut.id
                WHERE l.{xp_col} > %s
                ORDER BY l.{xp_col} ASC
                LIMIT 2
            ''', (user_xp,))
            above = list(cursor.fetchall())
            
            cursor.execute(f'''
                SELECT l.user_id, l.{xp_col}, u.rango, u.avatar_id, u.titolo,
                       ut.nome, ut.cognome
                FROM leaderboards_v2 l
                JOIN user_gamification_v2 u ON l.user_id = u.user_id
                LEFT JOIN utenti ut ON l.user_id = ut.id
                WHERE l.{xp_col} < %s
                ORDER BY l.{xp_col} DESC
                LIMIT 2
            ''', (user_xp,))
            below = list(cursor.fetchall())
            
            nearby = []
            for row in reversed(above):
                nearby.append({
                    'user_id': row[0],
                    'xp': row[1],
                    'rango': row[2],
                    'avatar_id': row[3],
                    'titolo': row[4],
                    'nome': f"{row[5] or ''} {row[6] or ''}".strip() or f"Utente {row[0]}",
                    'is_you': False
                })
            
            # Add current user
            cursor.execute('''
                SELECT u.avatar_id, u.titolo, ut.nome, ut.cognome, u.rango
                FROM user_gamification_v2 u
                LEFT JOIN utenti ut ON u.user_id = ut.id
                WHERE u.user_id = %s
            ''', (request.user_id,))
            user_row = cursor.fetchone()
            if user_row:
                nearby.append({
                    'user_id': request.user_id,
                    'xp': user_xp,
                    'rango': user_row[4],
                    'avatar_id': user_row[0],
                    'titolo': user_row[1],
                    'nome': f"{user_row[2] or ''} {user_row[3] or ''}".strip() or f"Utente {request.user_id}",
                    'is_you': True
                })
            
            for row in below:
                nearby.append({
                    'user_id': row[0],
                    'xp': row[1],
                    'rango': row[2],
                    'avatar_id': row[3],
                    'titolo': row[4],
                    'nome': f"{row[5] or ''} {row[6] or ''}".strip() or f"Utente {row[0]}",
                    'is_you': False
                })
            
            return jsonify({
                'tipo': tipo,
                'top3': top3,
                'nearby': nearby,
                'user_position': user_position,
                'user_xp': user_xp
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting smart leaderboard: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# KUDOS (Peer Recognition)
# =============================================================================

@gamification_api_bp.route('/kudos', methods=['POST'])
@require_auth
def send_kudos():
    """Send kudos to another user"""
    try:
        data = request.get_json()
        to_user_id = data.get('to_user_id')
        motivo = data.get('motivo', 'Grande lavoro!')
        
        if not to_user_id:
            return jsonify({'error': 'to_user_id richiesto'}), 400
        
        if to_user_id == request.user_id:
            return jsonify({'error': 'Non puoi dare kudos a te stesso'}), 400
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if already sent kudos today
            cursor.execute('''
                SELECT id FROM kudos 
                WHERE from_user_id = %s AND to_user_id = %s
                AND created_at::date = CURRENT_DATE
            ''', (request.user_id, to_user_id))
            
            if cursor.fetchone():
                return jsonify({'error': 'Hai già inviato kudos a questo utente oggi'}), 400
            
            # Create kudos
            cursor.execute('''
                INSERT INTO kudos (from_user_id, to_user_id, motivo, xp_reward)
                VALUES (%s, %s, %s, 50)
                RETURNING id
            ''', (request.user_id, to_user_id, motivo))
            
            kudos_id = cursor.fetchone()[0]
            
            # Award XP to recipient
            xp_manager_v2.assegna_xp(
                to_user_id, 50, 'kudos',
                f"Kudos ricevuti da utente {request.user_id}",
                {'from_user_id': request.user_id},
                check_limits=False
            )
            
            # Create notification for recipient
            cursor.execute('''
                INSERT INTO gamification_notifications (user_id, tipo, titolo, messaggio, data)
                VALUES (%s, 'kudos', %s, %s, %s)
            ''', (to_user_id, 'Kudos Ricevuti!', 
                  f"Hai ricevuto kudos: {motivo}",
                  json.dumps({'from_user_id': request.user_id, 'kudos_id': kudos_id})))
            
            return jsonify({
                'success': True,
                'message': 'Kudos inviati!',
                'kudos_id': kudos_id
            }), 201
            
    except Exception as e:
        logger.error(f"Error sending kudos: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/kudos/received', methods=['GET'])
@require_auth
def get_received_kudos():
    """Get kudos received by user"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT k.id, k.from_user_id, k.motivo, k.xp_reward, k.created_at,
                       ut.nome, ut.cognome
                FROM kudos k
                LEFT JOIN utenti ut ON k.from_user_id = ut.id
                WHERE k.to_user_id = %s
                ORDER BY k.created_at DESC
                LIMIT 50
            ''', (request.user_id,))
            
            kudos = []
            for row in cursor.fetchall():
                kudos.append({
                    'id': row[0],
                    'from_user_id': row[1],
                    'from_user_name': f"{row[5] or ''} {row[6] or ''}".strip() or f"Utente {row[1]}",
                    'motivo': row[2],
                    'xp_reward': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                })
            
            return jsonify(kudos), 200
            
    except Exception as e:
        logger.error(f"Error getting received kudos: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# POWER-UPS
# =============================================================================

@gamification_api_bp.route('/powerups/available', methods=['GET'])
@require_auth
def get_available_powerups():
    """Get available power-ups for purchase"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, codice, nome, descrizione, tipo, effetto, 
                       durata_minuti, costo_xp, costo_monete
                FROM powerups
                WHERE disponibile = TRUE
                ORDER BY costo_xp
            ''')
            
            powerups = []
            for row in cursor.fetchall():
                powerups.append({
                    'id': row[0],
                    'codice': row[1],
                    'nome': row[2],
                    'descrizione': row[3],
                    'tipo': row[4],
                    'effetto': row[5],
                    'durata_minuti': row[6],
                    'costo_xp': row[7],
                    'costo_monete': row[8]
                })
            
            return jsonify(powerups), 200
            
    except Exception as e:
        logger.error(f"Error getting power-ups: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/powerups/buy', methods=['POST'])
@require_auth
def buy_powerup():
    """Buy a power-up"""
    try:
        data = request.get_json()
        powerup_id = data.get('powerup_id')
        
        if not powerup_id:
            return jsonify({'error': 'powerup_id richiesto'}), 400
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get power-up
            cursor.execute('''
                SELECT id, nome, costo_xp FROM powerups WHERE id = %s AND disponibile = TRUE
            ''', (powerup_id,))
            
            powerup = cursor.fetchone()
            if not powerup:
                return jsonify({'error': 'Power-up non trovato'}), 404
            
            pu_id, nome, costo_xp = powerup
            
            # Check user XP
            cursor.execute('''
                SELECT xp_totale FROM user_gamification_v2 WHERE user_id = %s
            ''', (request.user_id,))
            
            user_xp = cursor.fetchone()
            if not user_xp or user_xp[0] < costo_xp:
                return jsonify({'error': 'XP insufficienti'}), 400
            
            # Deduct XP
            cursor.execute('''
                UPDATE user_gamification_v2 
                SET xp_totale = xp_totale - %s
                WHERE user_id = %s
            ''', (costo_xp, request.user_id))
            
            # Add power-up to user inventory
            cursor.execute('''
                INSERT INTO user_powerups (user_id, powerup_id, quantita)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, powerup_id) 
                DO UPDATE SET quantita = user_powerups.quantita + 1
            ''', (request.user_id, pu_id))
            
            # Log transaction
            cursor.execute('''
                INSERT INTO xp_logs (user_id, amount, source, description, metadata)
                VALUES (%s, %s, 'powerup_purchase', %s, %s)
            ''', (request.user_id, -costo_xp, f"Acquisto {nome}",
                  json.dumps({'powerup_id': pu_id})))
            
            return jsonify({
                'success': True,
                'message': f'Power-up {nome} acquistato!'
            }), 200
            
    except Exception as e:
        logger.error(f"Error buying power-up: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/powerups/activate', methods=['POST'])
@require_auth
def activate_powerup():
    """Activate a power-up"""
    try:
        data = request.get_json()
        powerup_id = data.get('powerup_id')
        
        if not powerup_id:
            return jsonify({'error': 'powerup_id richiesto'}), 400
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user has this power-up
            cursor.execute('''
                SELECT up.id, up.quantita, p.durata_minuti, p.nome
                FROM user_powerups up
                JOIN powerups p ON up.powerup_id = p.id
                WHERE up.user_id = %s AND up.powerup_id = %s AND up.quantita > 0
            ''', (request.user_id, powerup_id))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Power-up non disponibile'}), 404
            
            up_id, quantita, durata, nome = row
            
            # Activate power-up
            scade_at = None
            if durata:
                scade_at = datetime.utcnow() + timedelta(minutes=durata)
            
            cursor.execute('''
                UPDATE user_powerups 
                SET attivo = TRUE, attivato_at = CURRENT_TIMESTAMP, 
                    scade_at = %s, quantita = quantita - 1
                WHERE id = %s
            ''', (scade_at, up_id))
            
            return jsonify({
                'success': True,
                'message': f'Power-up {nome} attivato!',
                'scade_at': scade_at.isoformat() if scade_at else None
            }), 200
            
    except Exception as e:
        logger.error(f"Error activating power-up: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# NOTIFICATIONS
# =============================================================================

@gamification_api_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """Get user's gamification notifications"""
    try:
        limit = request.args.get('limit', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, tipo, titolo, messaggio, data, letta, created_at
                FROM gamification_notifications
                WHERE user_id = %s
            '''
            
            if unread_only:
                query += ' AND letta = FALSE'
            
            query += ' ORDER BY created_at DESC LIMIT %s'
            
            cursor.execute(query, (request.user_id, limit))
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    'id': row[0],
                    'tipo': row[1],
                    'titolo': row[2],
                    'messaggio': row[3],
                    'data': row[4],
                    'letta': row[5],
                    'created_at': row[6].isoformat() if row[6] else None
                })
            
            return jsonify(notifications), 200
            
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@require_auth
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE gamification_notifications 
                SET letta = TRUE
                WHERE id = %s AND user_id = %s
            ''', (notification_id, request.user_id))
            
            return jsonify({'success': True}), 200
            
    except Exception as e:
        logger.error(f"Error marking notification read: {e}")
        return jsonify({'error': str(e)}), 500


@gamification_api_bp.route('/notifications/read-all', methods=['POST'])
@require_auth
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE gamification_notifications 
                SET letta = TRUE
                WHERE user_id = %s AND letta = FALSE
            ''', (request.user_id,))
            
            return jsonify({'success': True}), 200
            
    except Exception as e:
        logger.error(f"Error marking all notifications read: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# BATTLE PASS
# =============================================================================

@gamification_api_bp.route('/battlepass', methods=['GET'])
@require_auth
def get_battlepass():
    """Get battle pass info for current season"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get active season
            cursor.execute('''
                SELECT id, numero, nome, tema, data_inizio, data_fine, 
                       descrizione, moneta_stagionale
                FROM seasons WHERE attiva = TRUE
            ''')
            
            season = cursor.fetchone()
            if not season:
                return jsonify({'message': 'Nessuna stagione attiva'}), 200
            
            season_id, numero, nome, tema, inizio, fine, desc, moneta = season
            
            # Get user's battle pass progress
            cursor.execute('''
                SELECT battle_pass_livello, battle_pass_premium, xp_stagionale
                FROM user_gamification_v2 WHERE user_id = %s
            ''', (request.user_id,))
            
            user_bp = cursor.fetchone()
            bp_level = user_bp[0] if user_bp else 0
            is_premium = user_bp[1] if user_bp else False
            xp_stagionale = user_bp[2] if user_bp else 0
            
            # Get battle pass levels
            cursor.execute('''
                SELECT livello, reward_free, reward_premium, xp_richiesti
                FROM battle_pass_levels
                WHERE stagione_id = %s
                ORDER BY livello
            ''', (season_id,))
            
            levels = []
            for row in cursor.fetchall():
                levels.append({
                    'livello': row[0],
                    'reward_free': row[1],
                    'reward_premium': row[2],
                    'xp_richiesti': row[3],
                    'sbloccato': bp_level >= row[0]
                })
            
            return jsonify({
                'stagione': {
                    'id': season_id,
                    'numero': numero,
                    'nome': nome,
                    'tema': tema,
                    'data_inizio': inizio.isoformat() if inizio else None,
                    'data_fine': fine.isoformat() if fine else None,
                    'descrizione': desc,
                    'moneta_stagionale': moneta
                },
                'utente': {
                    'livello': bp_level,
                    'premium': is_premium,
                    'xp_stagionale': xp_stagionale
                },
                'livelli': levels
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting battle pass: {e}")
        return jsonify({'error': str(e)}), 500
