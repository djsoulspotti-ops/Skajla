{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 """\
Challenge Manager - Gestisce le sfide (giornaliere, settimanali, classe)\
Sistema Gamification Skaila\
"""\
\
from datetime import datetime, timedelta\
from sqlalchemy import and_, or_\
from models.gamification_models import (\
    db, Challenge, UserChallenge, UserGamification, Badge,\
    TipoSfidaEnum, DifficoltaSfidaEnum, ClasseChallengeProgress\
)\
from services.xp_manager import xp_manager\
import random\
\
\
class ChallengeManager:\
    """Gestisce assegnazione, validazione e completamento sfide"""\
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
    # ASSEGNAZIONE SFIDE\
    # ========================================================================\
    \
    def assegna_sfida_giornaliera(self, user_id):\
        """\
        Assegna una sfida giornaliera casuale all'utente\
        Tiene conto dell'anno scolastico e del livello\
        """\
        try:\
            user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
            if not user_gam:\
                return \{'success': False, 'message': 'Utente non trovato'\}\
            \
            # Ottieni anno scolastico dell'utente\
            anno = self._get_anno_scolastico(user_id)\
            \
            # Check se ha gi\'e0 una sfida giornaliera attiva oggi\
            oggi = datetime.utcnow().date()\
            sfida_esistente = UserChallenge.query.join(Challenge).filter(\
                UserChallenge.user_gamification_id == user_gam.id,\
                Challenge.tipo == TipoSfidaEnum.GIORNALIERA,\
                Challenge.attiva == True,\
                db.func.date(UserChallenge.assegnata_at) == oggi\
            ).first()\
            \
            if sfida_esistente:\
                return \{\
                    'success': False,\
                    'message': 'Sfida giornaliera gi\'e0 assegnata oggi',\
                    'challenge': self._format_user_challenge(sfida_esistente)\
                \}\
            \
            # Ottieni pool di sfide giornaliere disponibili\
            challenges = Challenge.query.filter(\
                Challenge.tipo == TipoSfidaEnum.GIORNALIERA,\
                Challenge.attiva == True,\
                or_(\
                    Challenge.anno_min == None,\
                    and_(Challenge.anno_min <= anno, Challenge.anno_max >= anno)\
                )\
            ).all()\
            \
            if not challenges:\
                return \{'success': False, 'message': 'Nessuna sfida disponibile'\}\
            \
            # Seleziona casuale (pesata per difficolt\'e0)\
            challenge = self._seleziona_challenge_pesata(challenges, user_gam)\
            \
            # Crea UserChallenge\
            user_challenge = UserChallenge(\
                user_gamification_id=user_gam.id,\
                challenge_id=challenge.id,\
                progresso=self._init_progresso(challenge)\
            )\
            db.session.add(user_challenge)\
            db.session.commit()\
            \
            return \{\
                'success': True,\
                'challenge': self._format_user_challenge(user_challenge)\
            \}\
            \
        except Exception as e:\
            db.session.rollback()\
            print(f"Errore assegnazione sfida giornaliera: \{e\}")\
            return \{'success': False, 'message': str(e)\}\
    \
    def assegna_sfide_settimanali(self, user_id):\
        """\
        Assegna 3 sfide settimanali (facile, media, difficile)\
        Chiamato ogni luned\'ec mattina\
        """\
        try:\
            user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
            if not user_gam:\
                return \{'success': False, 'message': 'Utente non trovato'\}\
            \
            anno = self._get_anno_scolastico(user_id)\
            \
            # Rimuovi sfide settimanali vecchie non completate\
            self._pulisci_sfide_vecchie(user_gam.id, TipoSfidaEnum.SETTIMANALE)\
            \
            sfide_assegnate = []\
            \
            # Assegna una sfida per ogni difficolt\'e0\
            for difficolta in [DifficoltaSfidaEnum.FACILE, DifficoltaSfidaEnum.MEDIA, DifficoltaSfidaEnum.DIFFICILE]:\
                challenge = Challenge.query.filter(\
                    Challenge.tipo == TipoSfidaEnum.SETTIMANALE,\
                    Challenge.difficolta == difficolta,\
                    Challenge.attiva == True,\
                    or_(\
                        Challenge.anno_min == None,\
                        and_(Challenge.anno_min <= anno, Challenge.anno_max >= anno)\
                    )\
                ).order_by(db.func.random()).first()\
                \
                if challenge:\
                    user_challenge = UserChallenge(\
                        user_gamification_id=user_gam.id,\
                        challenge_id=challenge.id,\
                        progresso=self._init_progresso(challenge)\
                    )\
                    db.session.add(user_challenge)\
                    sfide_assegnate.append(challenge)\
            \
            db.session.commit()\
            \
            return \{\
                'success': True,\
                'message': f'\{len(sfide_assegnate)\} sfide settimanali assegnate',\
                'challenges': [self._format_challenge(c) for c in sfide_assegnate]\
            \}\
            \
        except Exception as e:\
            db.session.rollback()\
            print(f"Errore assegnazione sfide settimanali: \{e\}")\
            return \{'success': False, 'message': str(e)\}\
    \
    def assegna_sfida_classe(self, classe_id, challenge_id):\
        """Assegna una sfida collaborativa a tutta la classe"""\
        try:\
            challenge = Challenge.query.get(challenge_id)\
            if not challenge or challenge.tipo != TipoSfidaEnum.CLASSE:\
                return \{'success': False, 'message': 'Sfida non valida'\}\
            \
            # Check se gi\'e0 assegnata\
            existing = ClasseChallengeProgress.query.filter_by(\
                classe_id=classe_id,\
                challenge_id=challenge_id\
            ).first()\
            \
            if existing:\
                return \{'success': False, 'message': 'Sfida gi\'e0 assegnata a questa classe'\}\
            \
            # Crea progress classe\
            progress = ClasseChallengeProgress(\
                classe_id=classe_id,\
                challenge_id=challenge_id,\
                progresso=self._init_progresso(challenge)\
            )\
            db.session.add(progress)\
            db.session.commit()\
            \
            return \{\
                'success': True,\
                'message': 'Sfida assegnata alla classe',\
                'challenge': self._format_challenge(challenge)\
            \}\
            \
        except Exception as e:\
            db.session.rollback()\
            print(f"Errore assegnazione sfida classe: \{e\}")\
            return \{'success': False, 'message': str(e)\}\
    \
    # ========================================================================\
    # VALIDAZIONE E AGGIORNAMENTO PROGRESSO\
    # ========================================================================\
    \
    def aggiorna_progresso(self, user_id, challenge_type, action_data):\
        """\
        Aggiorna il progresso delle sfide attive dell'utente\
        Chiamato ogni volta che l'utente compie un'azione rilevante\
        \
        Args:\
            user_id: ID utente\
            challenge_type: Tipo azione ('messaggio', 'chatbot', 'aiuto', etc.)\
            action_data: Dict con dati azione (es. \{'count': 1, 'tipo': 'gruppo'\})\
        """\
        try:\
            user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
            if not user_gam:\
                return\
            \
            # Ottieni sfide attive non completate\
            user_challenges = UserChallenge.query.join(Challenge).filter(\
                UserChallenge.user_gamification_id == user_gam.id,\
                UserChallenge.completato == False,\
                Challenge.attiva == True\
            ).all()\
            \
            sfide_completate = []\
            \
            for uc in user_challenges:\
                challenge = uc.challenge\
                \
                # Check se questa azione \'e8 rilevante per questa sfida\
                if self._is_action_relevant(challenge, challenge_type, action_data):\
                    # Aggiorna progresso\
                    updated = self._update_challenge_progress(uc, challenge_type, action_data)\
                    \
                    if updated:\
                        # Check se completata\
                        if self._check_challenge_completed(uc):\
                            uc.completato = True\
                            uc.completata_at = datetime.utcnow()\
                            sfide_completate.append(uc)\
            \
            db.session.commit()\
            \
            # Distribuisci reward per sfide completate\
            for uc in sfide_completate:\
                self._distribuisci_reward(uc)\
            \
        except Exception as e:\
            db.session.rollback()\
            print(f"Errore aggiornamento progresso: \{e\}")\
    \
    def _is_action_relevant(self, challenge, action_type, action_data):\
        """Verifica se un'azione \'e8 rilevante per una sfida"""\
        obiettivi = challenge.obiettivi\
        \
        # Esempio: sfida richiede messaggi, action \'e8 messaggio\
        if action_type == 'messaggio' and 'messaggi' in obiettivi:\
            return True\
        \
        if action_type == 'chatbot' and 'chatbot_interazioni' in obiettivi:\
            return True\
        \
        if action_type == 'aiuto' and 'compagni_aiutati' in obiettivi:\
            return True\
        \
        if action_type == 'gruppo_studio' and 'gruppi_studio' in obiettivi:\
            return True\
        \
        # Add more mappings as needed\
        return False\
    \
    def _update_challenge_progress(self, user_challenge, action_type, action_data):\
        """Aggiorna il progresso di una specifica sfida"""\
        progresso = user_challenge.progresso or \{\}\
        obiettivi = user_challenge.challenge.obiettivi\
        \
        updated = False\
        \
        # Mappa action_type -> campo obiettivo\
        mapping = \{\
            'messaggio': 'messaggi',\
            'chatbot': 'chatbot_interazioni',\
            'aiuto': 'compagni_aiutati',\
            'gruppo_studio': 'gruppi_studio',\
            'reaction': 'reactions',\
            'xp': 'xp_accumulati'\
        \}\
        \
        for action_key, obiettivo_key in mapping.items():\
            if action_type == action_key and obiettivo_key in obiettivi:\
                current = progresso.get(obiettivo_key, 0)\
                increment = action_data.get('count', 1)\
                progresso[obiettivo_key] = current + increment\
                updated = True\
        \
        if updated:\
            user_challenge.progresso = progresso\
        \
        return updated\
    \
    def _check_challenge_completed(self, user_challenge):\
        """Verifica se una sfida \'e8 completata"""\
        progresso = user_challenge.progresso or \{\}\
        obiettivi = user_challenge.challenge.obiettivi\
        \
        # Tutti gli obiettivi devono essere raggiunti\
        for key, target in obiettivi.items():\
            current = progresso.get(key, 0)\
            if current < target:\
                return False\
        \
        return True\
    \
    def _distribuisci_reward(self, user_challenge):\
        """Distribuisce reward per sfida completata"""\
        challenge = user_challenge.challenge\
        user_gam = user_challenge.user_gamification\
        \
        # XP\
        if challenge.reward_xp > 0:\
            xp_manager.xp_sfida_completata(\
                user_id=user_gam.user_id,\
                challenge_id=challenge.id,\
                reward_xp=challenge.reward_xp\
            )\
        \
        # Badge\
        if challenge.reward_badge_id:\
            self._assegna_badge(user_gam.id, challenge.reward_badge_id)\
        \
        # Extra rewards (avatar, temi, etc.)\
        if challenge.reward_extra:\
            self._applica_reward_extra(user_gam, challenge.reward_extra)\
        \
        # Crea notifica\
        self._crea_notifica_sfida_completata(user_gam, challenge)\
    \
    # ========================================================================\
    # GET SFIDE\
    # ========================================================================\
    \
    def get_sfide_attive(self, user_id):\
        """Ottieni tutte le sfide attive per un utente"""\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if not user_gam:\
            return []\
        \
        user_challenges = UserChallenge.query.join(Challenge).filter(\
            UserChallenge.user_gamification_id == user_gam.id,\
            UserChallenge.completato == False,\
            Challenge.attiva == True\
        ).all()\
        \
        return [self._format_user_challenge(uc) for uc in user_challenges]\
    \
    def get_sfida_giornaliera(self, user_id):\
        """Ottieni sfida giornaliera attiva"""\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if not user_gam:\
            return None\
        \
        oggi = datetime.utcnow().date()\
        \
        uc = UserChallenge.query.join(Challenge).filter(\
            UserChallenge.user_gamification_id == user_gam.id,\
            Challenge.tipo == TipoSfidaEnum.GIORNALIERA,\
            Challenge.attiva == True,\
            db.func.date(UserChallenge.assegnata_at) == oggi\
        ).first()\
        \
        return self._format_user_challenge(uc) if uc else None\
    \
    def get_sfide_settimanali(self, user_id):\
        """Ottieni sfide settimanali attive"""\
        user_gam = UserGamification.query.filter_by(user_id=user_id).first()\
        if not user_gam:\
            return []\
        \
        user_challenges = UserChallenge.query.join(Challenge).filter(\
            UserChallenge.user_gamification_id == user_gam.id,\
            Challenge.tipo == TipoSfidaEnum.SETTIMANALE,\
            Challenge.attiva == True,\
            UserChallenge.completato == False\
        ).all()\
        \
        return [self._format_user_challenge(uc) for uc in user_challenges]\
    \
    def get_sfide_classe(self, classe_id):\
        """Ottieni sfide attive per una classe"""\
        progress_list = ClasseChallengeProgress.query.join(Challenge).filter(\
            ClasseChallengeProgress.classe_id == classe_id,\
            ClasseChallengeProgress.completato == False,\
            Challenge.attiva == True\
        ).all()\
        \
        return [self._format_classe_challenge(p) for p in progress_list]\
    \
    # ========================================================================\
    # HELPERS\
    # ========================================================================\
    \
    def _get_anno_scolastico(self, user_id):\
        """Ottieni anno scolastico utente (1, 2, 3)"""\
        # TODO: Implementare logica per ottenere anno da tabella users/classi\
        # Per ora return random\
        return random.randint(1, 3)\
    \
    def _seleziona_challenge_pesata(self, challenges, user_gam):\
        """Seleziona challenge considerando difficolt\'e0 e livello utente"""\
        # Per ora random, ma potrebbe essere pesato in base al rango\
        return random.choice(challenges)\
    \
    def _init_progresso(self, challenge):\
        """Inizializza dict progresso per una challenge"""\
        progresso = \{\}\
        for key in challenge.obiettivi.keys():\
            progresso[key] = 0\
        return progresso\
    \
    def _pulisci_sfide_vecchie(self, user_gam_id, tipo):\
        """Rimuove sfide vecchie non completate"""\
        UserChallenge.query.join(Challenge).filter(\
            UserChallenge.user_gamification_id == user_gam_id,\
            Challenge.tipo == tipo,\
            UserChallenge.completato == False\
        ).delete(synchronize_session='fetch')\
    \
    def _assegna_badge(self, user_gam_id, badge_id):\
        """Assegna badge a utente (se non gi\'e0 posseduto)"""\
        from models.gamification_models import UserBadge\
        \
        # Check se gi\'e0 posseduto\
        existing = UserBadge.query.filter_by(\
            user_gamification_id=user_gam_id,\
            badge_id=badge_id\
        ).first()\
        \
        if not existing:\
            user_badge = UserBadge(\
                user_gamification_id=user_gam_id,\
                badge_id=badge_id\
            )\
            db.session.add(user_badge)\
    \
    def _applica_reward_extra(self, user_gam, reward_extra):\
        """Applica reward extra (avatar, temi, etc.)"""\
        # TODO: Implementare logica per sbloccare contenuti extra\
        pass\
    \
    def _crea_notifica_sfida_completata(self, user_gam, challenge):\
        """Crea notifica per sfida completata"""\
        from models.gamification_models import Notification\
        \
        notifica = Notification(\
            user_gamification_id=user_gam.id,\
            tipo='challenge_completed',\
            titolo=f'\uc0\u55356 \u57225  Sfida Completata!',\
            messaggio=f'Hai completato "\{challenge.nome\}"! +\{challenge.reward_xp\} XP',\
            icon='\uc0\u55356 \u57286 ',\
            metadata=\{'challenge_id': challenge.id\}\
        )\
        db.session.add(notifica)\
    \
    def _format_user_challenge(self, uc):\
        """Formatta UserChallenge per output"""\
        if not uc:\
            return None\
        \
        challenge = uc.challenge\
        progresso = uc.progresso or \{\}\
        obiettivi = challenge.obiettivi\
        \
        # Calcola percentuale completamento\
        total_progress = 0\
        total_targets = 0\
        \
        for key, target in obiettivi.items():\
            current = progresso.get(key, 0)\
            total_progress += min(current, target)\
            total_targets += target\
        \
        percentuale = int((total_progress / total_targets) * 100) if total_targets > 0 else 0\
        \
        return \{\
            'id': uc.id,\
            'challenge_id': challenge.id,\
            'nome': challenge.nome,\
            'descrizione': challenge.descrizione,\
            'tipo': challenge.tipo.value,\
            'difficolta': challenge.difficolta.value,\
            'obiettivi': obiettivi,\
            'progresso': progresso,\
            'percentuale': percentuale,\
            'completato': uc.completato,\
            'reward_xp': challenge.reward_xp,\
            'reward_badge': self._get_badge_info(challenge.reward_badge_id) if challenge.reward_badge_id else None,\
            'scade_at': self._calcola_scadenza(uc, challenge)\
        \}\
    \
    def _format_challenge(self, challenge):\
        """Formatta Challenge per output"""\
        return \{\
            'id': challenge.id,\
            'nome': challenge.nome,\
            'descrizione': challenge.descrizione,\
            'tipo': challenge.tipo.value,\
            'difficolta': challenge.difficolta.value,\
            'obiettivi': challenge.obiettivi,\
            'reward_xp': challenge.reward_xp\
        \}\
    \
    def _format_classe_challenge(self, progress):\
        """Formatta ClasseChallengeProgress per output"""\
        challenge = progress.challenge\
        \
        return \{\
            'id': progress.id,\
            'challenge_id': challenge.id,\
            'nome': challenge.nome,\
            'descrizione': challenge.descrizione,\
            'progresso': progress.progresso,\
            'completato': progress.completato,\
            'top_contributors': progress.top_contributors,\
            'reward_xp': challenge.reward_xp\
        \}\
    \
    def _get_badge_info(self, badge_id):\
        """Ottieni info badge"""\
        badge = Badge.query.get(badge_id)\
        if badge:\
            return \{\
                'id': badge.id,\
                'nome': badge.nome,\
                'icon': badge.icon,\
                'rarita': badge.rarita.value\
            \}\
        return None\
    \
    def _calcola_scadenza(self, user_challenge, challenge):\
        """Calcola timestamp scadenza sfida"""\
        if challenge.tipo == TipoSfidaEnum.GIORNALIERA:\
            # Scade a mezzanotte\
            domani = datetime.utcnow().date() + timedelta(days=1)\
            return datetime.combine(domani, datetime.min.time())\
        \
        elif challenge.tipo == TipoSfidaEnum.SETTIMANALE:\
            # Scade luned\'ec prossimo a mezzanotte\
            oggi = datetime.utcnow()\
            giorni_a_lunedi = (7 - oggi.weekday()) % 7\
            if giorni_a_lunedi == 0:\
                giorni_a_lunedi = 7\
            prossimo_lunedi = oggi.date() + timedelta(days=giorni_a_lunedi)\
            return datetime.combine(prossimo_lunedi, datetime.min.time())\
        \
        else:\
            return challenge.data_fine if challenge.data_fine else None\
    \
    # ========================================================================\
    # RESET E MANUTENZIONE (chiamati da scheduler)\
    # ========================================================================\
    \
    def assegna_sfide_giornaliere_globale(self):\
        """Assegna sfida giornaliera a tutti gli utenti attivi"""\
        try:\
            # Ottieni tutti gli utenti gamification\
            users = UserGamification.query.all()\
            \
            count = 0\
            for user_gam in users:\
                result = self.assegna_sfida_giornaliera(user_gam.user_id)\
                if result.get('success'):\
                    count += 1\
            \
            print(f"\uc0\u9989  Assegnate \{count\} sfide giornaliere")\
            \
        except Exception as e:\
            print(f"\uc0\u10060  Errore assegnazione sfide giornaliere globale: \{e\}")\
    \
    def assegna_sfide_settimanali_globale(self):\
        """Assegna sfide settimanali a tutti gli utenti (ogni luned\'ec)"""\
        try:\
            users = UserGamification.query.all()\
            \
            count = 0\
            for user_gam in users:\
                result = self.assegna_sfide_settimanali(user_gam.user_id)\
                if result.get('success'):\
                    count += 1\
            \
            print(f"\uc0\u9989  Assegnate sfide settimanali a \{count\} utenti")\
            \
        except Exception as e:\
            print(f"\uc0\u10060  Errore assegnazione sfide settimanali globale: \{e\}")\
\
\
# ============================================================================\
# INSTANCE GLOBALE\
# ============================================================================\
\
challenge_manager = ChallengeManager()}