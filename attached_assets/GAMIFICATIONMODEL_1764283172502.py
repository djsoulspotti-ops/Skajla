{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 """\
Modelli Database per Sistema Gamification Skaila\
Scuole Medie (11-14 anni)\
"""\
\
from datetime import datetime\
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, JSON\
from sqlalchemy.orm import relationship\
from flask_sqlalchemy import SQLAlchemy\
import enum\
\
db = SQLAlchemy()\
\
# ============================================================================\
# ENUMS\
# ============================================================================\
\
class RangoEnum(enum.Enum):\
    GERMOGLIO = "Germoglio"\
    CADETTO = "Cadetto"\
    CAVALIERE = "Cavaliere"\
    GUARDIANO = "Guardiano"\
    CAMPIONE = "Campione"\
    LEGGENDA = "Leggenda"\
    MAESTRO = "Maestro"\
    GRANDE_MAESTRO = "Grande Maestro"\
    IMMORTALE = "Immortale"\
\
class RaritaBadgeEnum(enum.Enum):\
    COMUNE = "comune"\
    RARO = "raro"\
    EPICO = "epico"\
    LEGGENDARIO = "leggendario"\
    SEGRETO = "segreto"\
    STAGIONALE = "stagionale"\
\
class TipoSfidaEnum(enum.Enum):\
    GIORNALIERA = "giornaliera"\
    SETTIMANALE = "settimanale"\
    CLASSE = "classe"\
    EVENTO = "evento"\
    STORIA = "storia"\
\
class DifficoltaSfidaEnum(enum.Enum):\
    FACILE = "facile"\
    MEDIA = "media"\
    DIFFICILE = "difficile"\
    EPICA = "epica"\
\
class TipoEventoEnum(enum.Enum):\
    HALLOWEEN = "halloween"\
    CHRISTMAS = "christmas"\
    VALENTINE = "valentine"\
    SPRING = "spring"\
    EASTER = "easter"\
    FINALS = "finals"\
    ENDYEAR = "endyear"\
    FLASH = "flash"\
\
# ============================================================================\
# MODELLO UTENTE GAMIFICATION (estende User esistente)\
# ============================================================================\
\
class UserGamification(db.Model):\
    __tablename__ = 'user_gamification'\
    \
    id = Column(Integer, primary_key=True)\
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)\
    \
    # XP e Livelli\
    xp_totale = Column(Integer, default=0)\
    xp_stagionale = Column(Integer, default=0)\
    xp_settimanale = Column(Integer, default=0)\
    xp_giornaliero = Column(Integer, default=0)\
    \
    # Rango\
    rango = Column(Enum(RangoEnum), default=RangoEnum.GERMOGLIO)\
    rango_max_raggiunto = Column(Enum(RangoEnum), default=RangoEnum.GERMOGLIO)\
    \
    # Streak\
    streak_giorni = Column(Integer, default=0)\
    streak_max = Column(Integer, default=0)\
    ultimo_accesso = Column(DateTime, default=datetime.utcnow)\
    \
    # Battle Pass\
    battle_pass_livello = Column(Integer, default=0)\
    battle_pass_premium = Column(Boolean, default=False)\
    \
    # Statistiche\
    messaggi_inviati = Column(Integer, default=0)\
    chatbot_interazioni = Column(Integer, default=0)\
    compagni_aiutati = Column(Integer, default=0)\
    gruppi_studio_creati = Column(Integer, default=0)\
    reactions_ricevute = Column(Integer, default=0)\
    \
    # Personalizzazione\
    avatar_id = Column(String(50))\
    tema_colore = Column(String(50))\
    titolo = Column(String(100))\
    cornice_profilo = Column(String(50))\
    effetto_messaggio = Column(String(50))\
    pet_id = Column(String(50))\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow)\
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\
    \
    # Relazioni\
    user = relationship("User", backref="gamification")\
    xp_logs = relationship("XPLog", back_populates="user_gamification", cascade="all, delete-orphan")\
    user_badges = relationship("UserBadge", back_populates="user_gamification", cascade="all, delete-orphan")\
    user_challenges = relationship("UserChallenge", back_populates="user_gamification", cascade="all, delete-orphan")\
\
    def __repr__(self):\
        return f'<UserGamification \{self.user_id\} - \{self.rango.value\} - \{self.xp_totale\} XP>'\
\
# ============================================================================\
# XP LOG - Traccia tutte le transazioni XP\
# ============================================================================\
\
class XPLog(db.Model):\
    __tablename__ = 'xp_logs'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    \
    amount = Column(Integer, nullable=False)  # Pu\'f2 essere negativo per penalit\'e0\
    source = Column(String(100), nullable=False)  # 'messaggio', 'chatbot', 'sfida', 'bonus', etc.\
    description = Column(Text)\
    metadata = Column(JSON)  # Info extra (es. challenge_id, message_id, etc.)\
    \
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", back_populates="xp_logs")\
\
    def __repr__(self):\
        return f'<XPLog \{self.amount\} XP from \{self.source\}>'\
\
# ============================================================================\
# BADGES - Definizione Badge\
# ============================================================================\
\
class Badge(db.Model):\
    __tablename__ = 'badges'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Info Badge\
    codice = Column(String(50), unique=True, nullable=False)  # es. 'chiacchierone'\
    nome = Column(String(100), nullable=False)\
    descrizione = Column(Text, nullable=False)\
    icon = Column(String(20))  # Emoji o riferimento icona\
    \
    # Rarit\'e0 e Tipo\
    rarita = Column(Enum(RaritaBadgeEnum), default=RaritaBadgeEnum.COMUNE)\
    stagionale = Column(Boolean, default=False)\
    stagione_id = Column(Integer, ForeignKey('seasons.id'), nullable=True)\
    segreto = Column(Boolean, default=False)\
    \
    # Condizioni di Unlock (JSON)\
    condizioni = Column(JSON)  # Es: \{"messaggi_inviati": 100\}\
    \
    # Reward\
    reward_xp = Column(Integer, default=0)\
    reward_titolo = Column(String(100))\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow)\
    \
    # Relazioni\
    user_badges = relationship("UserBadge", back_populates="badge")\
    stagione = relationship("Season", backref="badges")\
\
    def __repr__(self):\
        return f'<Badge \{self.nome\} (\{self.rarita.value\})>'\
\
# ============================================================================\
# USER BADGES - Badge Sbloccati da Utenti\
# ============================================================================\
\
class UserBadge(db.Model):\
    __tablename__ = 'user_badges'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    badge_id = Column(Integer, ForeignKey('badges.id'), nullable=False)\
    \
    unlocked_at = Column(DateTime, default=datetime.utcnow)\
    notified = Column(Boolean, default=False)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", back_populates="user_badges")\
    badge = relationship("Badge", back_populates="user_badges")\
    \
    # Constraint: un utente pu\'f2 sbloccare un badge una sola volta\
    __table_args__ = (\
        db.UniqueConstraint('user_gamification_id', 'badge_id', name='unique_user_badge'),\
    )\
\
    def __repr__(self):\
        return f'<UserBadge User:\{self.user_gamification_id\} Badge:\{self.badge_id\}>'\
\
# ============================================================================\
# CHALLENGES - Definizione Sfide\
# ============================================================================\
\
class Challenge(db.Model):\
    __tablename__ = 'challenges'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Info Sfida\
    codice = Column(String(50), unique=True, nullable=False)\
    nome = Column(String(100), nullable=False)\
    descrizione = Column(Text, nullable=False)\
    \
    # Tipo e Difficolt\'e0\
    tipo = Column(Enum(TipoSfidaEnum), nullable=False)\
    difficolta = Column(Enum(DifficoltaSfidaEnum), default=DifficoltaSfidaEnum.MEDIA)\
    \
    # Target Anno Scolastico\
    anno_min = Column(Integer)  # 1, 2, 3 per prima/seconda/terza media (null = tutti)\
    anno_max = Column(Integer)\
    \
    # Obiettivi (JSON)\
    obiettivi = Column(JSON, nullable=False)  # Es: \{"messaggi": 10, "chatbot": 5\}\
    \
    # Reward\
    reward_xp = Column(Integer, nullable=False)\
    reward_badge_id = Column(Integer, ForeignKey('badges.id'), nullable=True)\
    reward_extra = Column(JSON)  # Altri reward (avatar, tema, etc.)\
    \
    # Validit\'e0\
    attiva = Column(Boolean, default=True)\
    stagione_id = Column(Integer, ForeignKey('seasons.id'), nullable=True)\
    data_inizio = Column(DateTime)\
    data_fine = Column(DateTime)\
    \
    # Periodicit\'e0 (per giornaliere/settimanali)\
    reset_giornaliero = Column(Boolean, default=False)\
    reset_settimanale = Column(Boolean, default=False)\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow)\
    \
    # Relazioni\
    user_challenges = relationship("UserChallenge", back_populates="challenge")\
    reward_badge = relationship("Badge")\
    stagione = relationship("Season", backref="challenges")\
\
    def __repr__(self):\
        return f'<Challenge \{self.nome\} (\{self.tipo.value\})>'\
\
# ============================================================================\
# USER CHALLENGES - Progresso Sfide Utenti\
# ============================================================================\
\
class UserChallenge(db.Model):\
    __tablename__ = 'user_challenges'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    challenge_id = Column(Integer, ForeignKey('challenges.id'), nullable=False)\
    \
    # Progresso\
    progresso = Column(JSON)  # Es: \{"messaggi": 7, "chatbot": 3\}\
    completato = Column(Boolean, default=False)\
    \
    # Timestamp\
    assegnata_at = Column(DateTime, default=datetime.utcnow)\
    completata_at = Column(DateTime)\
    \
    # Reward ritirato\
    reward_claimed = Column(Boolean, default=False)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", back_populates="user_challenges")\
    challenge = relationship("Challenge", back_populates="user_challenges")\
\
    def __repr__(self):\
        status = "\uc0\u9989 " if self.completato else "\u9203 "\
        return f'<UserChallenge \{status\} User:\{self.user_gamification_id\} Challenge:\{self.challenge_id\}>'\
\
# ============================================================================\
# SEASONS - Stagioni\
# ============================================================================\
\
class Season(db.Model):\
    __tablename__ = 'seasons'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Info Stagione\
    numero = Column(Integer, unique=True, nullable=False)\
    nome = Column(String(100), nullable=False)  # "L'Inizio del Viaggio"\
    tema = Column(String(50))  # "autunno", "inverno", "primavera", "estate"\
    \
    # Date\
    data_inizio = Column(DateTime, nullable=False)\
    data_fine = Column(DateTime, nullable=False)\
    attiva = Column(Boolean, default=False)\
    \
    # Descrizione e Narrativa\
    descrizione = Column(Text)\
    narrativa = Column(Text)\
    \
    # Contenuti Esclusivi\
    moneta_stagionale = Column(String(50))  # "Fiocchi di Neve", "Petali", etc.\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow)\
\
    def __repr__(self):\
        return f'<Season \{self.numero\} - \{self.nome\}>'\
\
# ============================================================================\
# BATTLE PASS - Livelli Battle Pass\
# ============================================================================\
\
class BattlePassLevel(db.Model):\
    __tablename__ = 'battle_pass_levels'\
    \
    id = Column(Integer, primary_key=True)\
    stagione_id = Column(Integer, ForeignKey('seasons.id'), nullable=False)\
    livello = Column(Integer, nullable=False)\
    \
    # Reward Free Track\
    reward_free = Column(JSON)  # Es: \{"type": "xp", "amount": 100\}\
    \
    # Reward Premium Track\
    reward_premium = Column(JSON)  # Es: \{"type": "avatar", "id": "winter_king"\}\
    \
    # XP richiesti per questo livello\
    xp_richiesti = Column(Integer, nullable=False)\
    \
    # Relazioni\
    stagione = relationship("Season", backref="battle_pass_levels")\
    \
    __table_args__ = (\
        db.UniqueConstraint('stagione_id', 'livello', name='unique_season_level'),\
    )\
\
    def __repr__(self):\
        return f'<BattlePassLevel S\{self.stagione_id\} Lv\{self.livello\}>'\
\
# ============================================================================\
# LEADERBOARDS - Classifiche\
# ============================================================================\
\
class Leaderboard(db.Model):\
    __tablename__ = 'leaderboards'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False, unique=True)\
    \
    # XP per periodo\
    xp_giornaliero = Column(Integer, default=0, index=True)\
    xp_settimanale = Column(Integer, default=0, index=True)\
    xp_mensile = Column(Integer, default=0, index=True)\
    xp_stagionale = Column(Integer, default=0, index=True)\
    xp_lifetime = Column(Integer, default=0, index=True)\
    \
    # Posizioni\
    posizione_classe = Column(Integer)\
    posizione_scuola = Column(Integer)\
    posizione_stagionale = Column(Integer)\
    \
    # Statistiche speciali\
    messaggi_totali = Column(Integer, default=0)\
    chatbot_totali = Column(Integer, default=0)\
    aiuti_totali = Column(Integer, default=0)\
    streak_attuale = Column(Integer, default=0)\
    \
    # Timestamp ultimo update\
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", backref="leaderboard")\
\
    def __repr__(self):\
        return f'<Leaderboard User:\{self.user_gamification_id\} XP:\{self.xp_lifetime\}>'\
\
# ============================================================================\
# EVENTS - Eventi Speciali\
# ============================================================================\
\
class Event(db.Model):\
    __tablename__ = 'events'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Info Evento\
    codice = Column(String(50), unique=True, nullable=False)\
    nome = Column(String(100), nullable=False)\
    descrizione = Column(Text)\
    tipo = Column(Enum(TipoEventoEnum), nullable=False)\
    \
    # Date\
    data_inizio = Column(DateTime, nullable=False)\
    data_fine = Column(DateTime, nullable=False)\
    attivo = Column(Boolean, default=False)\
    \
    # Moltiplicatori XP\
    xp_multiplier = Column(Float, default=1.0)  # 2.0 = XP doppi\
    \
    # Contenuti Speciali (JSON)\
    rewards = Column(JSON)  # Badge esclusivi, avatar, etc.\
    sfide_speciali = Column(JSON)  # Riferimenti a challenge_id\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow)\
\
    def __repr__(self):\
        return f'<Event \{self.nome\} (\{self.tipo.value\})>'\
\
# ============================================================================\
# USER EVENT PROGRESS - Progresso Eventi Utenti\
# ============================================================================\
\
class UserEventProgress(db.Model):\
    __tablename__ = 'user_event_progress'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)\
    \
    # Progresso\
    progresso = Column(JSON)  # Specifico per ogni evento\
    completato = Column(Boolean, default=False)\
    \
    # Reward\
    rewards_claimed = Column(JSON)  # Quali reward sono stati ritirati\
    \
    # Timestamp\
    started_at = Column(DateTime, default=datetime.utcnow)\
    completed_at = Column(DateTime)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", backref="event_progress")\
    event = relationship("Event", backref="user_progress")\
\
    def __repr__(self):\
        return f'<UserEventProgress User:\{self.user_gamification_id\} Event:\{self.event_id\}>'\
\
# ============================================================================\
# KUDOS - Sistema Ringraziamenti\
# ============================================================================\
\
class Kudos(db.Model):\
    __tablename__ = 'kudos'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Chi e a chi\
    from_user_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    to_user_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    \
    # Contenuto\
    motivo = Column(Text, nullable=False)\
    \
    # XP reward per chi riceve\
    xp_reward = Column(Integer, default=50)\
    \
    # Reactions\
    reactions = Column(JSON)  # Chi ha reagito e con cosa\
    reactions_count = Column(Integer, default=0)\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow, index=True)\
    \
    # Relazioni\
    from_user = relationship("UserGamification", foreign_keys=[from_user_id], backref="kudos_dati")\
    to_user = relationship("UserGamification", foreign_keys=[to_user_id], backref="kudos_ricevuti")\
\
    def __repr__(self):\
        return f'<Kudos from:\{self.from_user_id\} to:\{self.to_user_id\}>'\
\
# ============================================================================\
# DUELS - Duelli 1v1\
# ============================================================================\
\
class Duel(db.Model):\
    __tablename__ = 'duels'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Partecipanti\
    challenger_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    opponent_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    \
    # Obiettivo\
    obiettivo_tipo = Column(String(50), nullable=False)  # 'xp', 'messaggi', 'chatbot', etc.\
    obiettivo_descrizione = Column(Text)\
    \
    # Progresso\
    challenger_progresso = Column(Integer, default=0)\
    opponent_progresso = Column(Integer, default=0)\
    \
    # Stato\
    accettato = Column(Boolean, default=False)\
    completato = Column(Boolean, default=False)\
    vincitore_id = Column(Integer, ForeignKey('user_gamification.id'))\
    \
    # Date\
    data_inizio = Column(DateTime)\
    data_fine = Column(DateTime)\
    created_at = Column(DateTime, default=datetime.utcnow)\
    \
    # Reward\
    reward_xp = Column(Integer, default=200)\
    \
    # Relazioni\
    challenger = relationship("UserGamification", foreign_keys=[challenger_id], backref="duels_iniziati")\
    opponent = relationship("UserGamification", foreign_keys=[opponent_id], backref="duels_ricevuti")\
    vincitore = relationship("UserGamification", foreign_keys=[vincitore_id])\
\
    def __repr__(self):\
        return f'<Duel \{self.challenger_id\} vs \{self.opponent_id\}>'\
\
# ============================================================================\
# CLASSE PROGRESS - Progresso Sfide di Classe\
# ============================================================================\
\
class ClasseChallengeProgress(db.Model):\
    __tablename__ = 'classe_challenge_progress'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Riferimenti\
    classe_id = Column(Integer, ForeignKey('classi.id'), nullable=False)\
    challenge_id = Column(Integer, ForeignKey('challenges.id'), nullable=False)\
    \
    # Progresso Collettivo\
    progresso = Column(JSON)  # Es: \{"xp_totale": 8450, "target": 10000\}\
    completato = Column(Boolean, default=False)\
    \
    # Contributori\
    top_contributors = Column(JSON)  # Top 3 user_id con XP contribuiti\
    \
    # Timestamp\
    started_at = Column(DateTime, default=datetime.utcnow)\
    completed_at = Column(DateTime)\
    \
    # Relazioni\
    classe = relationship("Classe", backref="challenge_progress")\
    challenge = relationship("Challenge", backref="classe_progress")\
\
    def __repr__(self):\
        return f'<ClasseProgress Classe:\{self.classe_id\} Challenge:\{self.challenge_id\}>'\
\
# ============================================================================\
# NOTIFICATIONS - Sistema Notifiche\
# ============================================================================\
\
class Notification(db.Model):\
    __tablename__ = 'notifications'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    \
    # Contenuto\
    tipo = Column(String(50), nullable=False)  # 'badge', 'rank_up', 'challenge', etc.\
    titolo = Column(String(200), nullable=False)\
    messaggio = Column(Text)\
    icon = Column(String(20))  # Emoji\
    \
    # Metadata\
    metadata = Column(JSON)  # Dati extra (badge_id, challenge_id, etc.)\
    \
    # Stato\
    letta = Column(Boolean, default=False)\
    visualizzata = Column(Boolean, default=False)\
    \
    # Link\
    action_url = Column(String(200))  # Link dove portare l'utente\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow, index=True)\
    read_at = Column(DateTime)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", backref="notifications")\
\
    def __repr__(self):\
        return f'<Notification \{self.tipo\} to User:\{self.user_gamification_id\}>'\
\
# ============================================================================\
# POWER UPS - Power-ups Acquistabili\
# ============================================================================\
\
class PowerUp(db.Model):\
    __tablename__ = 'power_ups'\
    \
    id = Column(Integer, primary_key=True)\
    \
    # Info\
    codice = Column(String(50), unique=True, nullable=False)\
    nome = Column(String(100), nullable=False)\
    descrizione = Column(Text)\
    icon = Column(String(20))\
    \
    # Costo\
    costo_xp = Column(Integer, nullable=False)\
    \
    # Effetto\
    effetto = Column(JSON, nullable=False)  # Es: \{"type": "xp_boost", "multiplier": 2, "duration": 3600\}\
    \
    # Disponibilit\'e0\
    disponibile = Column(Boolean, default=True)\
    stagionale = Column(Boolean, default=False)\
    \
    # Timestamp\
    created_at = Column(DateTime, default=datetime.utcnow)\
\
    def __repr__(self):\
        return f'<PowerUp \{self.nome\} - \{self.costo_xp\} XP>'\
\
# ============================================================================\
# USER POWER UPS - Power-ups Attivi per Utente\
# ============================================================================\
\
class UserPowerUp(db.Model):\
    __tablename__ = 'user_power_ups'\
    \
    id = Column(Integer, primary_key=True)\
    user_gamification_id = Column(Integer, ForeignKey('user_gamification.id'), nullable=False)\
    power_up_id = Column(Integer, ForeignKey('power_ups.id'), nullable=False)\
    \
    # Stato\
    attivo = Column(Boolean, default=True)\
    \
    # Timestamp\
    acquistato_at = Column(DateTime, default=datetime.utcnow)\
    attivato_at = Column(DateTime)\
    scade_at = Column(DateTime)\
    \
    # Relazioni\
    user_gamification = relationship("UserGamification", backref="power_ups_attivi")\
    power_up = relationship("PowerUp")\
\
    def __repr__(self):\
        return f'<UserPowerUp User:\{self.user_gamification_id\} PowerUp:\{self.power_up_id\}>'\
\
# ============================================================================\
# HELPERS\
# ============================================================================\
\
def calcola_rango(xp_totale):\
    """Calcola il rango in base agli XP totali"""\
    if xp_totale < 200:\
        return RangoEnum.GERMOGLIO\
    elif xp_totale < 600:\
        return RangoEnum.CADETTO\
    elif xp_totale < 1200:\
        return RangoEnum.CAVALIERE\
    elif xp_totale < 2200:\
        return RangoEnum.GUARDIANO\
    elif xp_totale < 3800:\
        return RangoEnum.CAMPIONE\
    elif xp_totale < 6000:\
        return RangoEnum.LEGGENDA\
    elif xp_totale < 9000:\
        return RangoEnum.MAESTRO\
    elif xp_totale < 13000:\
        return RangoEnum.GRANDE_MAESTRO\
    else:\
        return RangoEnum.IMMORTALE\
\
def xp_per_prossimo_rango(rango_attuale):\
    """Restituisce gli XP necessari per il prossimo rango"""\
    xp_map = \{\
        RangoEnum.GERMOGLIO: 200,\
        RangoEnum.CADETTO: 600,\
        RangoEnum.CAVALIERE: 1200,\
        RangoEnum.GUARDIANO: 2200,\
        RangoEnum.CAMPIONE: 3800,\
        RangoEnum.LEGGENDA: 6000,\
        RangoEnum.MAESTRO: 9000,\
        RangoEnum.GRANDE_MAESTRO: 13000,\
        RangoEnum.IMMORTALE: 13000  # Cap\
    \}\
    return xp_map.get(rango_attuale, 0)}