{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 """\
XP Manager - Gestisce calcolo e assegnazione XP\
Sistema Gamification Skaila\
"""\
\
from datetime import datetime, timedelta\
from sqlalchemy import func\
from models.gamification_models import (\
    db, UserGamification, XPLog, Leaderboard, Notification,\
    calcola_rango, RangoEnum, UserPowerUp\
)\
\
\
class XPManager:\
    """Gestisce tutte le operazioni relative agli XP"""\
    \
    # ========================================================================\
    # CONFIGURAZIONE XP\
    # ========================================================================\
    \
    XP_CONFIG = \{\
        # Messaggistica\
        'messaggio_base': 5,\
        'messaggio_primo_giorno': 15,\
        'messaggio_risposta_veloce': 5,  # bonus se <2 min\
        'messaggio_con_emoji': 3,\
        'conversazione_gruppo': 20,\
        'aiutare_compagno': 30,\
        'reaction_ricevuta': 2,\
        \
        # Chatbot\
        'chatbot_prima_interazione': 20,\
        'chatbot_domanda': 5,\
        'chatbot_conversazione_lunga': 50,  # 5+ scambi\
        'chatbot_studio': 25,\
        'chatbot_feedback': 15,\
        'chatbot_problema_risolto': 40,\
        \
        # Bonus\
        'streak_3_giorni': 50,\
        'streak_7_giorni': 150,\
        'streak_14_giorni': 350,\
        'streak_30_giorni': 800,\
        'combo_5x': None,  # Multiplier 2x\
        'combo_10x': None,  # Multiplier 3x\
        'prime_time': 0.2,  # +20% tra 14-18\
        \
        # Limiti giornalieri\
        'max_xp_messaggi': 500,\
        'max_xp_chatbot': 300,\
    \}\
    \
    def __init__(self, app=None):\
        self.app = app\
        if app:\
            self.init_app(app)\
    \
    def init_app(self, app):\
        """Inizializza con Flask app"""\
        self.app = app\
    \
    # ========================================================================\
    # ASSEGNAZIONE XP PRINCIPALE\
    # ========================================================================\
    \
    def assegna_xp(self, user_id, amount, source, description="", metadata=None, \
                   check_limits=True, apply_multipliers=True):\
        """\
        Assegna XP a un utente e gestisce tutte le conseguenze\
        \
        Args:\
            user_id: ID utente\
            amount: Quantit\'e0 XP\
            source: Fonte XP ('messaggio', 'chatbot', 'sfida', etc.)\
            description: Descrizione dell'azione\
            metadata: Dict con info extra\
            check_limits: Se True, applica limiti giornalieri\
            apply_multipliers: Se True, applica moltiplicatori attivi\
        \
        Returns:\
            dict con info sull'operazione (xp_assegnati, livello_up, badge_unlocked, etc.)\
        """\
        try:\
            # Ottieni o crea UserGamification\
            user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
            if not user_gam:\
                user_gam = self._crea_user_gamification(user_id)\
            \
            # Verifica limiti giornalieri\
            if check_limits:\
                if not self._check_daily_limit(user_gam, source, amount):\
                    return \{\
                        'success': False,\
                        'message': 'Limite giornaliero raggiunto per questa categoria',\
                        'xp_assegnati': 0\
                    \}\
            \
            # Applica moltiplicatori (power-ups, eventi, combo)\
            if apply_multipliers:\
                amount = self._applica_moltiplicatori(user_gam, amount)\
            \
            # Salva old rank per check rank up\
            old_rank = user_gam.rango\
            \
            # Aggiungi XP\
            user_gam.xp_totale += amount\
            user_gam.xp_stagionale += amount\
            user_gam.xp_settimanale += amount\
            user_gam.xp_giornaliero += amount\
            user_gam.updated_at = datetime.utcnow()\
            \
            # Aggiorna rango\
            nuovo_rango = calcola_rango(user_gam.xp_totale)\
            rank_up = False\
            if nuovo_rango != old_rank:\
                user_gam.rango = nuovo_rango\
                rank_up = True\
                \
                # Aggiorna max rango raggiunto\
                if self._rank_order(nuovo_rango) > self._rank_order(user_gam.rango_max_raggiunto):\
                    user_gam.rango_max_raggiunto = nuovo_rango\
            \
            # Log XP\
            xp_log = XPLog(\
                user_gamification_id=user_gam.id,\
                amount=amount,\
                source=source,\
                description=description,\
                metadata=metadata or \{\}\
            )\
            db.session.add(xp_log)\
            \
            # Aggiorna leaderboard\
            self._aggiorna_leaderboard(user_gam, amount)\
            \
            # Commit\
            db.session.commit()\
            \
            # Notifiche\
            result = \{\
                'success': True,\
                'xp_assegnati': amount,\
                'xp_totale': user_gam.xp_totale,\
                'rango': user_gam.rango.value,\
                'rank_up': rank_up,\
                'nuovo_rango': nuovo_rango.value if rank_up else None\
            \}\
            \
            # Se rank up, crea notifica\
            if rank_up:\
                self._crea_notifica_rank_up(user_gam, nuovo_rango)\
            \
            # Check badge unlock\
            badge_unlocked = self._check_badge_unlock(user_gam)\
            if badge_unlocked:\
                result['badge_unlocked'] = badge_unlocked\
            \
            return result\
            \
        except Exception as e:\
            db.session.rollback()\
            print(f"Errore assegnazione XP: \{e\}")\
            return \{\
                'success': False,\
                'message': str(e),\
                'xp_assegnati': 0\
            \}\
    \
    # ========================================================================\
    # METODI SPECIFICI PER AZIONI\
    # ========================================================================\
    \
    def xp_messaggio(self, user_id, is_primo_oggi=False, risposta_veloce=False, \
                     con_emoji=False, gruppo=False):\
        """Assegna XP per invio messaggio"""\
        amount = self.XP_CONFIG['messaggio_base']\
        descrizione = "Messaggio inviato"\
        \
        if is_primo_oggi:\
            amount = self.XP_CONFIG['messaggio_primo_giorno']\
            descrizione = "Primo messaggio del giorno"\
        \
        if risposta_veloce:\
            amount += self.XP_CONFIG['messaggio_risposta_veloce']\
            descrizione += " (risposta veloce)"\
        \
        if con_emoji:\
            amount += self.XP_CONFIG['messaggio_con_emoji']\
            descrizione += " (con emoji)"\
        \
        if gruppo:\
            amount = self.XP_CONFIG['conversazione_gruppo']\
            descrizione = "Conversazione di gruppo"\
        \
        return self.assegna_xp(\
            user_id=user_id,\
            amount=amount,\
            source='messaggio',\
            description=descrizione,\
            metadata=\{'tipo': 'messaggio'\}\
        )\
    \
    def xp_chatbot(self, user_id, is_prima_oggi=False, conversazione_lunga=False,\
                   per_studio=False, problema_risolto=False):\
        """Assegna XP per interazione chatbot"""\
        amount = self.XP_CONFIG['chatbot_domanda']\
        descrizione = "Interazione chatbot"\
        \
        if is_prima_oggi:\
            amount = self.XP_CONFIG['chatbot_prima_interazione']\
            descrizione = "Prima interazione chatbot oggi"\
        \
        if conversazione_lunga:\
            amount = self.XP_CONFIG['chatbot_conversazione_lunga']\
            descrizione = "Conversazione lunga con chatbot"\
        \
        if per_studio:\
            amount = self.XP_CONFIG['chatbot_studio']\
            descrizione = "Uso chatbot per studio"\
        \
        if problema_risolto:\
            amount = self.XP_CONFIG['chatbot_problema_risolto']\
            descrizione = "Problema risolto con chatbot"\
        \
        return self.assegna_xp(\
            user_id=user_id,\
            amount=amount,\
            source='chatbot',\
            description=descrizione,\
            metadata=\{'tipo': 'chatbot'\}\
        )\
    \
    def xp_aiuto_compagno(self, user_id, compagno_id):\
        """Assegna XP per aver aiutato un compagno"""\
        # Incrementa statistica\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if user_gam:\
            user_gam.compagni_aiutati += 1\
            db.session.commit()\
        \
        return self.assegna_xp(\
            user_id=user_id,\
            amount=self.XP_CONFIG['aiutare_compagno'],\
            source='aiuto',\
            description=f"Aiutato compagno",\
            metadata=\{'compagno_id': compagno_id\}\
        )\
    \
    def xp_reaction_ricevuta(self, user_id):\
        """Assegna XP per reaction ricevuta su messaggio"""\
        return self.assegna_xp(\
            user_id=user_id,\
            amount=self.XP_CONFIG['reaction_ricevuta'],\
            source='reaction',\
            description="Reaction ricevuta",\
            check_limits=False  # No limits per reactions\
        )\
    \
    def xp_sfida_completata(self, user_id, challenge_id, reward_xp):\
        """Assegna XP per completamento sfida"""\
        return self.assegna_xp(\
            user_id=user_id,\
            amount=reward_xp,\
            source='sfida',\
            description=f"Sfida completata",\
            metadata=\{'challenge_id': challenge_id\},\
            check_limits=False  # Sfide non hanno limiti\
        )\
    \
    def xp_streak_bonus(self, user_id, streak_giorni):\
        """Assegna bonus streak"""\
        amount = 0\
        descrizione = ""\
        \
        if streak_giorni == 3:\
            amount = self.XP_CONFIG['streak_3_giorni']\
            descrizione = "Streak 3 giorni"\
        elif streak_giorni == 7:\
            amount = self.XP_CONFIG['streak_7_giorni']\
            descrizione = "Streak 7 giorni"\
        elif streak_giorni == 14:\
            amount = self.XP_CONFIG['streak_14_giorni']\
            descrizione = "Streak 14 giorni"\
        elif streak_giorni == 30:\
            amount = self.XP_CONFIG['streak_30_giorni']\
            descrizione = "Streak 30 giorni"\
        \
        if amount > 0:\
            return self.assegna_xp(\
                user_id=user_id,\
                amount=amount,\
                source='streak',\
                description=descrizione,\
                metadata=\{'streak_giorni': streak_giorni\},\
                check_limits=False\
            )\
        \
        return \{'success': False, 'message': 'Streak non valido per bonus'\}\
    \
    # ========================================================================\
    # HELPER METHODS\
    # ========================================================================\
    \
    def _crea_user_gamification(self, user_id):\
        """Crea record UserGamification per nuovo utente"""\
        user_gam = UserGamification(user_id=user_id)\
        db.session.add(user_gam)\
        \
        # Crea anche leaderboard\
        leaderboard = Leaderboard(user_gamification_id=user_gam.id)\
        db.session.add(leaderboard)\
        \
        db.session.commit()\
        return user_gam\
    \
    def _check_daily_limit(self, user_gam, source, amount):\
        """Verifica se l'utente ha raggiunto il limite giornaliero per la categoria"""\
        oggi = datetime.utcnow().date()\
        \
        # Ottieni XP guadagnati oggi per questa source\
        xp_oggi = db.session.query(func.sum(XPLog.amount)).filter(\
            XPLog.user_gamification_id == user_gam.id,\
            XPLog.source == source,\
            func.date(XPLog.timestamp) == oggi\
        ).scalar() or 0\
        \
        # Check limiti\
        if source == 'messaggio':\
            return (xp_oggi + amount) <= self.XP_CONFIG['max_xp_messaggi']\
        elif source == 'chatbot':\
            return (xp_oggi + amount) <= self.XP_CONFIG['max_xp_chatbot']\
        \
        return True  # Altre fonti no limit\
    \
    def _applica_moltiplicatori(self, user_gam, amount):\
        """Applica moltiplicatori attivi (power-ups, eventi, prime time)"""\
        multiplier = 1.0\
        \
        # Check power-ups attivi\
        power_ups_attivi = UserPowerUp.query.filter(\
            UserPowerUp.user_gamification_id == user_gam.id,\
            UserPowerUp.attivo == True,\
            UserPowerUp.scade_at > datetime.utcnow()\
        ).all()\
        \
        for pu in power_ups_attivi:\
            if pu.power_up.effetto.get('type') == 'xp_boost':\
                multiplier *= pu.power_up.effetto.get('multiplier', 1.0)\
        \
        # Prime time bonus (14-18)\
        ora_attuale = datetime.utcnow().hour\
        if 14 <= ora_attuale <= 18:\
            multiplier += self.XP_CONFIG['prime_time']\
        \
        # TODO: Check eventi attivi con moltiplicatori\
        \
        return int(amount * multiplier)\
    \
    def _aggiorna_leaderboard(self, user_gam, amount):\
        """Aggiorna leaderboard con nuovi XP"""\
        leaderboard = Leaderboard.query.filter_by(\
            user_gamification_id=user_gam.id\
        ).first()\
        \
        if not leaderboard:\
            leaderboard = Leaderboard(user_gamification_id=user_gam.id)\
            db.session.add(leaderboard)\
        \
        leaderboard.xp_giornaliero += amount\
        leaderboard.xp_settimanale += amount\
        leaderboard.xp_mensile += amount\
        leaderboard.xp_stagionale += amount\
        leaderboard.xp_lifetime += amount\
        leaderboard.updated_at = datetime.utcnow()\
    \
    def _crea_notifica_rank_up(self, user_gam, nuovo_rango):\
        """Crea notifica per rank up"""\
        notifica = Notification(\
            user_gamification_id=user_gam.id,\
            tipo='rank_up',\
            titolo=f'\uc0\u55356 \u57225  Nuovo Rango: \{nuovo_rango.value\}!',\
            messaggio=f'Congratulazioni! Sei diventato \{nuovo_rango.value\}!',\
            icon='\uc0\u55357 \u56401 ',\
            metadata=\{'nuovo_rango': nuovo_rango.value\}\
        )\
        db.session.add(notifica)\
    \
    def _check_badge_unlock(self, user_gam):\
        """Verifica se l'utente ha sbloccato nuovi badge"""\
        # TODO: Implementare logica controllo badge\
        # Per ora return None\
        return None\
    \
    def _rank_order(self, rango):\
        """Restituisce ordine numerico del rango"""\
        order = \{\
            RangoEnum.GERMOGLIO: 1,\
            RangoEnum.CADETTO: 2,\
            RangoEnum.CAVALIERE: 3,\
            RangoEnum.GUARDIANO: 4,\
            RangoEnum.CAMPIONE: 5,\
            RangoEnum.LEGGENDA: 6,\
            RangoEnum.MAESTRO: 7,\
            RangoEnum.GRANDE_MAESTRO: 8,\
            RangoEnum.IMMORTALE: 9\
        \}\
        return order.get(rango, 0)\
    \
    # ========================================================================\
    # STATISTICHE\
    # ========================================================================\
    \
    def get_user_stats(self, user_id):\
        """Ottieni statistiche complete utente"""\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if not user_gam:\
            return None\
        \
        leaderboard = Leaderboard.query.filter_by(\
            user_gamification_id=user_gam.id\
        ).first()\
        \
        return \{\
            'xp_totale': user_gam.xp_totale,\
            'xp_stagionale': user_gam.xp_stagionale,\
            'xp_settimanale': user_gam.xp_settimanale,\
            'xp_giornaliero': user_gam.xp_giornaliero,\
            'rango': user_gam.rango.value,\
            'rango_max': user_gam.rango_max_raggiunto.value,\
            'streak': user_gam.streak_giorni,\
            'streak_max': user_gam.streak_max,\
            'messaggi_totali': user_gam.messaggi_inviati,\
            'chatbot_totali': user_gam.chatbot_interazioni,\
            'aiuti_totali': user_gam.compagni_aiutati,\
            'posizione_classe': leaderboard.posizione_classe if leaderboard else None,\
            'posizione_scuola': leaderboard.posizione_scuola if leaderboard else None,\
        \}\
    \
    # ========================================================================\
    # RESET PERIODICI (chiamati da scheduler)\
    # ========================================================================\
    \
    def reset_xp_giornaliero(self):\
        """Reset XP giornalieri (chiamato da scheduler a mezzanotte)"""\
        try:\
            UserGamification.query.update(\{UserGamification.xp_giornaliero: 0\})\
            Leaderboard.query.update(\{Leaderboard.xp_giornaliero: 0\})\
            db.session.commit()\
            print("\uc0\u9989  Reset XP giornaliero completato")\
        except Exception as e:\
            db.session.rollback()\
            print(f"\uc0\u10060  Errore reset XP giornaliero: \{e\}")\
    \
    def reset_xp_settimanale(self):\
        """Reset XP settimanali (chiamato da scheduler ogni luned\'ec)"""\
        try:\
            UserGamification.query.update(\{UserGamification.xp_settimanale: 0\})\
            Leaderboard.query.update(\{Leaderboard.xp_settimanale: 0\})\
            db.session.commit()\
            print("\uc0\u9989  Reset XP settimanale completato")\
        except Exception as e:\
            db.session.rollback()\
            print(f"\uc0\u10060  Errore reset XP settimanale: \{e\}")\
    \
    def update_streak(self, user_id):\
        """Aggiorna streak giornaliero utente"""\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if not user_gam:\
            return\
        \
        oggi = datetime.utcnow().date()\
        ultimo_accesso = user_gam.ultimo_accesso.date()\
        \
        # Check se \'e8 passato 1 giorno esatto\
        if (oggi - ultimo_accesso).days == 1:\
            # Incrementa streak\
            user_gam.streak_giorni += 1\
            \
            # Aggiorna max streak\
            if user_gam.streak_giorni > user_gam.streak_max:\
                user_gam.streak_max = user_gam.streak_giorni\
            \
            # Assegna bonus streak se milestone\
            if user_gam.streak_giorni in [3, 7, 14, 30]:\
                self.xp_streak_bonus(user_id, user_gam.streak_giorni)\
        \
        elif (oggi - ultimo_accesso).days > 1:\
            # Streak rotto :(\
            user_gam.streak_giorni = 1  # Reset a 1 (oggi conta)\
        \
        # Aggiorna ultimo accesso\
        user_gam.ultimo_accesso = datetime.utcnow()\
        db.session.commit()\
\
\
# ============================================================================\
# INSTANCE GLOBALE\
# ============================================================================\
\
xp_manager = XPManager()}