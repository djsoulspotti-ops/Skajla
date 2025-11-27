{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 """\
Flask Routes - API Gamification\
Endpoints per frontend\
"""\
\
from flask import Blueprint, jsonify, request, current_app\
from functools import wraps\
from datetime import datetime, timedelta\
from sqlalchemy import desc, func\
\
from models.gamification_models import (\
    db, UserGamification, Badge, UserBadge, Challenge, UserChallenge,\
    Leaderboard, Notification, Kudos, Duel, Season, BattlePassLevel,\
    Event, PowerUp, UserPowerUp, calcola_rango, xp_per_prossimo_rango\
)\
from services.xp_manager import xp_manager\
from services.challenge_manager import challenge_manager\
\
# Blueprint\
gamification_bp = Blueprint('gamification', __name__, url_prefix='/api/gamification')\
\
# ============================================================================\
# AUTH DECORATOR (adatta al tuo sistema di autenticazione)\
# ============================================================================\
\
def login_required(f):\
    """Decorator per verificare autenticazione"""\
    @wraps(f)\
    def decorated_function(*args, **kwargs):\
        # TODO: Implementa la tua logica di auth\
        # Per ora assumo che user_id sia in session o JWT\
        user_id = request.headers.get('X-User-ID')  # Placeholder\
        \
        if not user_id:\
            return jsonify(\{'error': 'Non autenticato'\}), 401\
        \
        request.user_id = int(user_id)\
        return f(*args, **kwargs)\
    return decorated_function\
\
# ============================================================================\
# USER PROFILE & STATS\
# ============================================================================\
\
@gamification_bp.route('/profile', methods=['GET'])\
@login_required\
def get_profile():\
    """Ottieni profilo gamification completo utente"""\
    try:\
        user_id = request.user_id\
        \
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if not user_gam:\
            # Crea se non esiste\
            user_gam = UserGamification(user_id=user_id)\
            db.session.add(user_gam)\
            db.session.commit()\
        \
        # Ottieni leaderboard\
        leaderboard = Leaderboard.query.filter_by(\
            user_gamification_id=user_gam.id\
        ).first()\
        \
        # Ottieni badge count\
        badge_count = UserBadge.query.filter_by(\
            user_gamification_id=user_gam.id\
        ).count()\
        \
        # XP per prossimo livello\
        xp_prossimo = xp_per_prossimo_rango(user_gam.rango)\
        xp_attuale = user_gam.xp_totale\
        \
        # Se gi\'e0 immortale, calcola basandosi su 13000\
        if user_gam.rango.value == 'Immortale':\
            xp_per_livello = 13000\
        else:\
            # Calcola XP dall'inizio del livello attuale\
            ranghi_xp = [0, 200, 600, 1200, 2200, 3800, 6000, 9000, 13000]\
            rango_idx = ['Germoglio', 'Cadetto', 'Cavaliere', 'Guardiano', \
                         'Campione', 'Leggenda', 'Maestro', 'Grande Maestro', 'Immortale'].index(user_gam.rango.value)\
            xp_start_livello = ranghi_xp[rango_idx]\
            xp_per_livello = xp_prossimo - xp_start_livello\
            xp_attuale_livello = xp_attuale - xp_start_livello\
        \
        profile = \{\
            'user_id': user_id,\
            'xp': \{\
                'totale': user_gam.xp_totale,\
                'stagionale': user_gam.xp_stagionale,\
                'settimanale': user_gam.xp_settimanale,\
                'giornaliero': user_gam.xp_giornaliero,\
                'per_prossimo_livello': xp_prossimo,\
                'progresso_livello': int((xp_attuale_livello / xp_per_livello) * 100) if xp_per_livello > 0 else 100\
            \},\
            'rango': \{\
                'attuale': user_gam.rango.value,\
                'icon': get_rango_icon(user_gam.rango.value),\
                'max_raggiunto': user_gam.rango_max_raggiunto.value\
            \},\
            'streak': \{\
                'attuale': user_gam.streak_giorni,\
                'massimo': user_gam.streak_max\
            \},\
            'statistiche': \{\
                'messaggi_inviati': user_gam.messaggi_inviati,\
                'chatbot_interazioni': user_gam.chatbot_interazioni,\
                'compagni_aiutati': user_gam.compagni_aiutati,\
                'gruppi_studio_creati': user_gam.gruppi_studio_creati,\
                'reactions_ricevute': user_gam.reactions_ricevute,\
                'badge_totali': badge_count\
            \},\
            'personalizzazione': \{\
                'avatar_id': user_gam.avatar_id,\
                'tema_colore': user_gam.tema_colore,\
                'titolo': user_gam.titolo,\
                'cornice_profilo': user_gam.cornice_profilo,\
                'effetto_messaggio': user_gam.effetto_messaggio,\
                'pet_id': user_gam.pet_id\
            \},\
            'battle_pass': \{\
                'livello': user_gam.battle_pass_livello,\
                'premium': user_gam.battle_pass_premium\
            \},\
            'posizioni': \{\
                'classe': leaderboard.posizione_classe if leaderboard else None,\
                'scuola': leaderboard.posizione_scuola if leaderboard else None,\
                'stagionale': leaderboard.posizione_stagionale if leaderboard else None\
            \}\
        \}\
        \
        return jsonify(profile), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/stats', methods=['GET'])\
@login_required\
def get_stats():\
    """Ottieni statistiche dettagliate"""\
    try:\
        user_id = request.user_id\
        stats = xp_manager.get_user_stats(user_id)\
        \
        if not stats:\
            return jsonify(\{'error': 'Utente non trovato'\}), 404\
        \
        return jsonify(stats), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# CHALLENGES\
# ============================================================================\
\
@gamification_bp.route('/challenges/active', methods=['GET'])\
@login_required\
def get_active_challenges():\
    """Ottieni tutte le sfide attive"""\
    try:\
        user_id = request.user_id\
        \
        sfide = \{\
            'giornaliera': challenge_manager.get_sfida_giornaliera(user_id),\
            'settimanali': challenge_manager.get_sfide_settimanali(user_id),\
            'tutte': challenge_manager.get_sfide_attive(user_id)\
        \}\
        \
        return jsonify(sfide), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/challenges/daily', methods=['GET'])\
@login_required\
def get_daily_challenge():\
    """Ottieni sfida giornaliera"""\
    try:\
        user_id = request.user_id\
        sfida = challenge_manager.get_sfida_giornaliera(user_id)\
        \
        # Se non esiste, assegnala\
        if not sfida:\
            result = challenge_manager.assegna_sfida_giornaliera(user_id)\
            sfida = result.get('challenge') if result.get('success') else None\
        \
        return jsonify(sfida), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/challenges/weekly', methods=['GET'])\
@login_required\
def get_weekly_challenges():\
    """Ottieni sfide settimanali"""\
    try:\
        user_id = request.user_id\
        sfide = challenge_manager.get_sfide_settimanali(user_id)\
        \
        return jsonify(sfide), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/challenges/class/<int:classe_id>', methods=['GET'])\
@login_required\
def get_class_challenges(classe_id):\
    """Ottieni sfide di classe"""\
    try:\
        sfide = challenge_manager.get_sfide_classe(classe_id)\
        return jsonify(sfide), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# BADGES\
# ============================================================================\
\
@gamification_bp.route('/badges', methods=['GET'])\
@login_required\
def get_badges():\
    """Ottieni badge dell'utente"""\
    try:\
        user_id = request.user_id\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        \
        if not user_gam:\
            return jsonify([]), 200\
        \
        # Badge posseduti\
        user_badges = UserBadge.query.filter_by(\
            user_gamification_id=user_gam.id\
        ).join(Badge).all()\
        \
        badges_posseduti = [\{\
            'id': ub.badge.id,\
            'codice': ub.badge.codice,\
            'nome': ub.badge.nome,\
            'descrizione': ub.badge.descrizione,\
            'icon': ub.badge.icon,\
            'rarita': ub.badge.rarita.value,\
            'sbloccato': True,\
            'sbloccato_at': ub.unlocked_at.isoformat()\
        \} for ub in user_badges]\
        \
        # Badge disponibili (non ancora sbloccati)\
        badge_ids_posseduti = [ub.badge_id for ub in user_badges]\
        badges_disponibili = Badge.query.filter(\
            ~Badge.id.in_(badge_ids_posseduti),\
            Badge.segreto == False  # Non mostrare badge segreti\
        ).all()\
        \
        badges_da_sbloccare = [\{\
            'id': b.id,\
            'codice': b.codice,\
            'nome': b.nome,\
            'descrizione': b.descrizione,\
            'icon': b.icon,\
            'rarita': b.rarita.value,\
            'sbloccato': False,\
            'condizioni': b.condizioni\
        \} for b in badges_disponibili]\
        \
        return jsonify(\{\
            'posseduti': badges_posseduti,\
            'da_sbloccare': badges_da_sbloccare,\
            'totale_posseduti': len(badges_posseduti),\
            'totale_disponibili': len(badges_disponibili) + len(badges_posseduti)\
        \}), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# LEADERBOARDS\
# ============================================================================\
\
@gamification_bp.route('/leaderboard/<tipo>', methods=['GET'])\
@login_required\
def get_leaderboard(tipo):\
    """\
    Ottieni leaderboard\
    Tipi: 'classe', 'scuola', 'settimanale', 'mensile', 'stagionale', 'lifetime'\
    """\
    try:\
        user_id = request.user_id\
        limite = request.args.get('limit', 50, type=int)\
        \
        # Determina quale campo XP usare\
        xp_field_map = \{\
            'giornaliera': Leaderboard.xp_giornaliero,\
            'settimanale': Leaderboard.xp_settimanale,\
            'mensile': Leaderboard.xp_mensile,\
            'stagionale': Leaderboard.xp_stagionale,\
            'lifetime': Leaderboard.xp_lifetime\
        \}\
        \
        xp_field = xp_field_map.get(tipo, Leaderboard.xp_lifetime)\
        \
        # Query leaderboard\
        query = Leaderboard.query.join(UserGamification).order_by(desc(xp_field)).limit(limite)\
        \
        # TODO: Filtra per classe se tipo=='classe'\
        \
        leaderboard_entries = query.all()\
        \
        # Trova posizione utente corrente\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        user_position = None\
        user_entry = None\
        \
        if user_gam:\
            user_leaderboard = Leaderboard.query.filter_by(\
                user_gamification_id=user_gam.id\
            ).first()\
            \
            if user_leaderboard:\
                # Calcola posizione\
                user_xp = getattr(user_leaderboard, xp_field.key)\
                user_position = Leaderboard.query.filter(\
                    xp_field > user_xp\
                ).count() + 1\
                \
                user_entry = \{\
                    'posizione': user_position,\
                    'user_id': user_id,\
                    'xp': user_xp,\
                    'rango': user_gam.rango.value,\
                    'is_you': True\
                \}\
        \
        # Formatta leaderboard\
        leaderboard = [\{\
            'posizione': idx + 1,\
            'user_id': entry.user_gamification.user_id,\
            'xp': getattr(entry, xp_field.key),\
            'rango': entry.user_gamification.rango.value,\
            'avatar_id': entry.user_gamification.avatar_id,\
            'titolo': entry.user_gamification.titolo,\
            'is_you': entry.user_gamification.user_id == user_id\
        \} for idx, entry in enumerate(leaderboard_entries)]\
        \
        return jsonify(\{\
            'tipo': tipo,\
            'leaderboard': leaderboard,\
            'user_position': user_position,\
            'user_entry': user_entry,\
            'total_users': Leaderboard.query.count()\
        \}), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/leaderboard/smart', methods=['GET'])\
@login_required\
def get_smart_leaderboard():\
    """Leaderboard intelligente: mostra top 3 + posizioni vicine all'utente"""\
    try:\
        user_id = request.user_id\
        tipo = request.args.get('tipo', 'lifetime')\
        \
        xp_field_map = \{\
            'settimanale': Leaderboard.xp_settimanale,\
            'mensile': Leaderboard.xp_mensile,\
            'stagionale': Leaderboard.xp_stagionale,\
            'lifetime': Leaderboard.xp_lifetime\
        \}\
        \
        xp_field = xp_field_map.get(tipo, Leaderboard.xp_lifetime)\
        \
        # Top 3\
        top3 = Leaderboard.query.join(UserGamification).order_by(\
            desc(xp_field)\
        ).limit(3).all()\
        \
        # Trova posizione utente\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        user_leaderboard = Leaderboard.query.filter_by(\
            user_gamification_id=user_gam.id\
        ).first() if user_gam else None\
        \
        nearby = []\
        user_position = None\
        \
        if user_leaderboard:\
            user_xp = getattr(user_leaderboard, xp_field.key)\
            \
            # Calcola posizione\
            user_position = Leaderboard.query.filter(\
                xp_field > user_xp\
            ).count() + 1\
            \
            # 2 sopra e 2 sotto\
            nearby_above = Leaderboard.query.join(UserGamification).filter(\
                xp_field > user_xp\
            ).order_by(xp_field).limit(2).all()\
            \
            nearby_below = Leaderboard.query.join(UserGamification).filter(\
                xp_field < user_xp\
            ).order_by(desc(xp_field)).limit(2).all()\
            \
            nearby = nearby_above + [user_leaderboard] + nearby_below\
        \
        # Formatta\
        top3_formatted = [\{\
            'posizione': idx + 1,\
            'user_id': entry.user_gamification.user_id,\
            'xp': getattr(entry, xp_field.key),\
            'rango': entry.user_gamification.rango.value,\
            'avatar_id': entry.user_gamification.avatar_id,\
            'titolo': entry.user_gamification.titolo\
        \} for idx, entry in enumerate(top3)]\
        \
        nearby_formatted = [\{\
            'posizione': Leaderboard.query.filter(\
                xp_field > getattr(entry, xp_field.key)\
            ).count() + 1,\
            'user_id': entry.user_gamification.user_id,\
            'xp': getattr(entry, xp_field.key),\
            'rango': entry.user_gamification.rango.value,\
            'is_you': entry.user_gamification.user_id == user_id\
        \} for entry in nearby]\
        \
        return jsonify(\{\
            'top3': top3_formatted,\
            'nearby': nearby_formatted,\
            'user_position': user_position\
        \}), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# NOTIFICATIONS\
# ============================================================================\
\
@gamification_bp.route('/notifications', methods=['GET'])\
@login_required\
def get_notifications():\
    """Ottieni notifiche utente"""\
    try:\
        user_id = request.user_id\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        \
        if not user_gam:\
            return jsonify([]), 200\
        \
        # Parametri\
        solo_non_lette = request.args.get('unread', 'false').lower() == 'true'\
        limite = request.args.get('limit', 20, type=int)\
        \
        query = Notification.query.filter_by(\
            user_gamification_id=user_gam.id\
        )\
        \
        if solo_non_lette:\
            query = query.filter_by(letta=False)\
        \
        notifications = query.order_by(\
            desc(Notification.created_at)\
        ).limit(limite).all()\
        \
        notifiche_formatted = [\{\
            'id': n.id,\
            'tipo': n.tipo,\
            'titolo': n.titolo,\
            'messaggio': n.messaggio,\
            'icon': n.icon,\
            'letta': n.letta,\
            'metadata': n.metadata,\
            'action_url': n.action_url,\
            'created_at': n.created_at.isoformat()\
        \} for n in notifications]\
        \
        return jsonify(notifiche_formatted), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])\
@login_required\
def mark_notification_read(notification_id):\
    """Segna notifica come letta"""\
    try:\
        notification = Notification.query.get(notification_id)\
        \
        if not notification:\
            return jsonify(\{'error': 'Notifica non trovata'\}), 404\
        \
        notification.letta = True\
        notification.read_at = datetime.utcnow()\
        db.session.commit()\
        \
        return jsonify(\{'success': True\}), 200\
        \
    except Exception as e:\
        db.session.rollback()\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# BATTLE PASS\
# ============================================================================\
\
@gamification_bp.route('/battlepass', methods=['GET'])\
@login_required\
def get_battle_pass():\
    """Ottieni info battle pass stagione corrente"""\
    try:\
        user_id = request.user_id\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        \
        # Ottieni stagione attiva\
        stagione = Season.query.filter_by(attiva=True).first()\
        \
        if not stagione:\
            return jsonify(\{'error': 'Nessuna stagione attiva'\}), 404\
        \
        # Ottieni livelli battle pass\
        livelli = BattlePassLevel.query.filter_by(\
            stagione_id=stagione.id\
        ).order_by(BattlePassLevel.livello).all()\
        \
        livelli_formatted = [\{\
            'livello': lv.livello,\
            'xp_richiesti': lv.xp_richiesti,\
            'reward_free': lv.reward_free,\
            'reward_premium': lv.reward_premium,\
            'sbloccato': user_gam.battle_pass_livello >= lv.livello if user_gam else False\
        \} for lv in livelli]\
        \
        return jsonify(\{\
            'stagione': \{\
                'numero': stagione.numero,\
                'nome': stagione.nome,\
                'tema': stagione.tema\
            \},\
            'livello_attuale': user_gam.battle_pass_livello if user_gam else 0,\
            'premium_unlocked': user_gam.battle_pass_premium if user_gam else False,\
            'xp_stagionale': user_gam.xp_stagionale if user_gam else 0,\
            'livelli': livelli_formatted\
        \}), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# SOCIAL FEATURES\
# ============================================================================\
\
@gamification_bp.route('/kudos', methods=['POST'])\
@login_required\
def give_kudos():\
    """Dai kudos a un compagno"""\
    try:\
        user_id = request.user_id\
        data = request.get_json()\
        \
        to_user_id = data.get('to_user_id')\
        motivo = data.get('motivo')\
        \
        if not to_user_id or not motivo:\
            return jsonify(\{'error': 'Parametri mancanti'\}), 400\
        \
        # Check limite giornaliero (3 kudos/giorno)\
        oggi = datetime.utcnow().date()\
        kudos_oggi = Kudos.query.join(UserGamification).filter(\
            UserGamification.user_id == user_id,\
            func.date(Kudos.created_at) == oggi\
        ).count()\
        \
        if kudos_oggi >= 3:\
            return jsonify(\{'error': 'Limite giornaliero raggiunto (3 kudos/giorno)'\}), 400\
        \
        # Ottieni user_gamification IDs\
        from_user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        to_user_gam = UserGamification.query.filter_by(user_id=to_user_id).first()\
        \
        if not from_user_gam or not to_user_gam:\
            return jsonify(\{'error': 'Utente non trovato'\}), 404\
        \
        # Crea kudos\
        kudos = Kudos(\
            from_user_id=from_user_gam.id,\
            to_user_id=to_user_gam.id,\
            motivo=motivo\
        )\
        db.session.add(kudos)\
        \
        # Assegna XP al ricevente\
        xp_manager.assegna_xp(\
            user_id=to_user_id,\
            amount=50,\
            source='kudos',\
            description=f"Kudos ricevuto da User \{user_id\}",\
            check_limits=False\
        )\
        \
        db.session.commit()\
        \
        return jsonify(\{\
            'success': True,\
            'message': 'Kudos inviato!',\
            'kudos_id': kudos.id\
        \}), 200\
        \
    except Exception as e:\
        db.session.rollback()\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/kudos/received', methods=['GET'])\
@login_required\
def get_received_kudos():\
    """Ottieni kudos ricevuti"""\
    try:\
        user_id = request.user_id\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        \
        if not user_gam:\
            return jsonify([]), 200\
        \
        kudos_list = Kudos.query.filter_by(\
            to_user_id=user_gam.id\
        ).order_by(desc(Kudos.created_at)).limit(20).all()\
        \
        kudos_formatted = [\{\
            'id': k.id,\
            'from_user_id': k.from_user.user_id,\
            'motivo': k.motivo,\
            'reactions_count': k.reactions_count,\
            'created_at': k.created_at.isoformat()\
        \} for k in kudos_list]\
        \
        return jsonify(kudos_formatted), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# POWER UPS\
# ============================================================================\
\
@gamification_bp.route('/powerups/available', methods=['GET'])\
@login_required\
def get_available_powerups():\
    """Ottieni power-ups acquistabili"""\
    try:\
        powerups = PowerUp.query.filter_by(disponibile=True).all()\
        \
        powerups_formatted = [\{\
            'id': pu.id,\
            'codice': pu.codice,\
            'nome': pu.nome,\
            'descrizione': pu.descrizione,\
            'icon': pu.icon,\
            'costo_xp': pu.costo_xp,\
            'effetto': pu.effetto\
        \} for pu in powerups]\
        \
        return jsonify(powerups_formatted), 200\
        \
    except Exception as e:\
        return jsonify(\{'error': str(e)\}), 500\
\
@gamification_bp.route('/powerups/buy', methods=['POST'])\
@login_required\
def buy_powerup():\
    """Acquista power-up"""\
    try:\
        user_id = request.user_id\
        data = request.get_json()\
        powerup_id = data.get('powerup_id')\
        \
        if not powerup_id:\
            return jsonify(\{'error': 'power_up_id richiesto'\}), 400\
        \
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        powerup = PowerUp.query.get(powerup_id)\
        \
        if not powerup:\
            return jsonify(\{'error': 'Power-up non trovato'\}), 404\
        \
        # Check se ha abbastanza XP\
        if user_gam.xp_totale < powerup.costo_xp:\
            return jsonify(\{'error': 'XP insufficienti'\}), 400\
        \
        # Sottrai XP\
        user_gam.xp_totale -= powerup.costo_xp\
        \
        # Crea UserPowerUp\
        durata = powerup.effetto.get('duration', 3600)  # default 1 ora\
        user_powerup = UserPowerUp(\
            user_gamification_id=user_gam.id,\
            power_up_id=powerup.id,\
            attivato_at=datetime.utcnow(),\
            scade_at=datetime.utcnow() + timedelta(seconds=durata)\
        )\
        db.session.add(user_powerup)\
        db.session.commit()\
        \
        return jsonify(\{\
            'success': True,\
            'message': f'Power-up "\{powerup.nome\}" attivato!',\
            'scade_at': user_powerup.scade_at.isoformat()\
        \}), 200\
        \
    except Exception as e:\
        db.session.rollback()\
        return jsonify(\{'error': str(e)\}), 500\
\
# ============================================================================\
# HELPERS\
# ============================================================================\
\
def get_rango_icon(rango_name):\
    """Restituisce emoji per rango"""\
    icons = \{\
        'Germoglio': '\uc0\u55356 \u57137 ',\
        'Cadetto': '\uc0\u55357 \u56624 ',\
        'Cavaliere': '\uc0\u9876 \u65039 ',\
        'Guardiano': '\uc0\u55357 \u57057 \u65039 ',\
        'Campione': '\uc0\u55357 \u56401 ',\
        'Leggenda': '\uc0\u11088 ',\
        'Maestro': '\uc0\u55357 \u56462 ',\
        'Grande Maestro': '\uc0\u55357 \u56613 ',\
        'Immortale': '\uc0\u55356 \u57119 '\
    \}\
    return icons.get(rango_name, '\uc0\u55356 \u57262 ')\
\
# ============================================================================\
# ERROR HANDLERS\
# ============================================================================\
\
@gamification_bp.errorhandler(404)\
def not_found(error):\
    return jsonify(\{'error': 'Risorsa non trovata'\}), 404\
\
@gamification_bp.errorhandler(500)\
def internal_error(error):\
    db.session.rollback()\
    return jsonify(\{'error': 'Errore interno del server'\}), 500}