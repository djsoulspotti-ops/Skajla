"""
SKAILA - Esempi Pratici Nuovi Moduli
Dimostrazioni di come utilizzare i moduli centralizzati
"""

from datetime import datetime, date, timedelta
from shared.validators.input_validators import validator, sql_protector
from shared.formatters.date_formatters import date_formatter
from shared.formatters.file_formatters import file_formatter
from core.config.settings import AppSettings, SecuritySettings, FileUploadSettings
from core.config.gamification_config import XPConfig, LevelConfig, BadgeConfig

def demo_validators():
    """Dimostra l'uso dei validatori"""
    print("\n" + "="*60)
    print("📋 DEMO VALIDATORI INPUT")
    print("="*60)
    
    # Validazione Email
    print("\n✅ Validazione Email:")
    emails = [
        "studente@skaila.edu",
        "invalid-email",
        "test@test@test.com",
        ""
    ]
    for email in emails:
        is_valid, error = validator.validate_email(email)
        status = "✅ VALIDA" if is_valid else f"❌ ERRORE: {error}"
        print(f"  {email:30s} -> {status}")
    
    # Validazione Password
    print("\n🔐 Validazione Password:")
    passwords = [
        "Password123",      # ✅ Valida
        "weak",            # ❌ Troppo corta
        "NoNumbers",       # ❌ Senza numeri
        "Test@2024!"       # ✅ Valida
    ]
    for pwd in passwords:
        is_valid, error = validator.validate_password(pwd)
        status = "✅ SICURA" if is_valid else f"❌ {error}"
        print(f"  {pwd:20s} -> {status}")
    
    # Protezione SQL Injection
    print("\n🛡️ Protezione SQL Injection:")
    inputs = [
        "Mario Rossi",
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "studente@test.com"
    ]
    for inp in inputs:
        is_safe = sql_protector.is_safe(inp)
        status = "✅ SICURO" if is_safe else "⚠️ PERICOLOSO - BLOCCATO"
        print(f"  {inp:30s} -> {status}")
    
    # Sanitizzazione HTML (Anti-XSS)
    print("\n🧹 Sanitizzazione HTML (previene XSS):")
    dangerous_html = "<script>alert('XSS')</script>Ciao"
    sanitized = validator.sanitize_html(dangerous_html)
    print(f"  Input:  {dangerous_html}")
    print(f"  Output: {sanitized}")
    
    # Validazione Voti
    print("\n📊 Validazione Voti (scala 1-10):")
    grades = [8.5, 11, 0, 7, "10", "invalid"]
    for grade in grades:
        is_valid, value = validator.validate_grade(grade)
        if is_valid:
            print(f"  {str(grade):10s} -> ✅ Voto valido: {value}")
        else:
            print(f"  {str(grade):10s} -> ❌ Non valido")

def demo_date_formatters():
    """Dimostra l'uso dei formattatori date"""
    print("\n" + "="*60)
    print("📅 DEMO FORMATTATORI DATE")
    print("="*60)
    
    now = datetime.now()
    
    # Formattazione date
    print("\n🗓️ Formattazione Standard:")
    print(f"  Data:     {date_formatter.format_date(now)}")
    print(f"  DateTime: {date_formatter.format_datetime(now)}")
    print(f"  Time:     {date_formatter.format_time(now)}")
    
    # Date relative
    print("\n⏰ Date Relative:")
    test_dates = [
        (now, "Adesso"),
        (now - timedelta(minutes=5), "5 minuti fa"),
        (now - timedelta(hours=2), "2 ore fa"),
        (now - timedelta(days=1), "Ieri"),
        (now - timedelta(days=3), "3 giorni fa"),
        (now - timedelta(days=15), "2 settimane fa"),
        (now - timedelta(days=60), "2 mesi fa")
    ]
    for dt, expected in test_dates:
        relative = date_formatter.format_relative(dt)
        print(f"  {relative}")
    
    # Anno scolastico
    print(f"\n🎓 Anno Scolastico Corrente: {date_formatter.get_school_year()}")
    
    # Weekend check
    print("\n📆 Verifica Weekend:")
    for i in range(7):
        day = date.today() + timedelta(days=i)
        is_weekend = date_formatter.is_weekend(day)
        status = "🎉 WEEKEND" if is_weekend else "📚 Giorno feriale"
        print(f"  {day.strftime('%A')} -> {status}")

def demo_file_formatters():
    """Dimostra l'uso dei formattatori file"""
    print("\n" + "="*60)
    print("📁 DEMO FORMATTATORI FILE")
    print("="*60)
    
    # Formattazione dimensioni file
    print("\n💾 Formattazione Dimensioni:")
    sizes = [0, 512, 1024, 1536, 1024*1024, int(5.5*1024*1024), 1024*1024*1024]
    for size in sizes:
        formatted = file_formatter.format_file_size(size)
        print(f"  {size:12d} bytes -> {formatted}")
    
    # Icone file
    print("\n🎨 Icone per Tipo File:")
    files = [
        "documento.pdf",
        "presentazione.pptx",
        "foglio_calcolo.xlsx",
        "immagine.png",
        "video.mp4",
        "archivio.zip",
        "codice.py"
    ]
    for filename in files:
        icon = file_formatter.get_file_icon(filename)
        ext = file_formatter.get_file_extension(filename)
        print(f"  {icon} {filename:25s} (.{ext})")
    
    # Troncamento nomi file
    print("\n✂️ Troncamento Nomi Lunghi:")
    long_name = "questo_è_un_nome_file_molto_molto_molto_lungo_che_deve_essere_troncato.pdf"
    truncated = file_formatter.truncate_filename(long_name, max_length=40)
    print(f"  Originale: {long_name}")
    print(f"  Troncato:  {truncated}")

def demo_configurations():
    """Dimostra l'uso delle configurazioni centralizzate"""
    print("\n" + "="*60)
    print("⚙️ DEMO CONFIGURAZIONI CENTRALIZZATE (SSoT)")
    print("="*60)
    
    # Configurazioni App
    print("\n📱 Configurazioni App:")
    print(f"  Nome App:    {AppSettings.APP_NAME}")
    print(f"  Versione:    {AppSettings.VERSION}")
    print(f"  Environment: {AppSettings.ENVIRONMENT}")
    print(f"  Debug Mode:  {AppSettings.DEBUG}")
    
    # Configurazioni Sicurezza
    print("\n🔒 Configurazioni Sicurezza:")
    print(f"  Max Login Attempts: {SecuritySettings.MAX_LOGIN_ATTEMPTS}")
    print(f"  Lockout Duration:   {SecuritySettings.LOGIN_LOCKOUT_DURATION}s")
    print(f"  Session Lifetime:   {SecuritySettings.PERMANENT_SESSION_LIFETIME}s (30 giorni)")
    print(f"  CSRF Enabled:       {SecuritySettings.CSRF_ENABLED}")
    
    # Configurazioni Upload
    print("\n📤 Configurazioni Upload:")
    print(f"  Max File Size: {file_formatter.format_file_size(FileUploadSettings.MAX_FILE_SIZE)}")
    print(f"  Estensioni Documenti: {', '.join(list(FileUploadSettings.ALLOWED_EXTENSIONS['documents'])[:5])}")
    print(f"  Estensioni Immagini:  {', '.join(FileUploadSettings.ALLOWED_EXTENSIONS['images'])}")
    
    # Test validazione file
    test_files = ["documento.pdf", "immagine.jpg", "script.exe", "video.mp4"]
    print("\n  Validazione File:")
    for filename in test_files:
        is_allowed = FileUploadSettings.is_allowed_file(filename)
        status = "✅ CONSENTITO" if is_allowed else "❌ BLOCCATO"
        print(f"    {filename:20s} -> {status}")

def demo_gamification_config():
    """Dimostra l'uso delle configurazioni gamification"""
    print("\n" + "="*60)
    print("🎮 DEMO CONFIGURAZIONI GAMIFICATION (SSoT)")
    print("="*60)
    
    # XP per azioni
    print("\n⭐ XP per Azione:")
    actions = ['login_daily', 'quiz_completed', 'ai_question', 'help_peer']
    for action in actions:
        xp = XPConfig.ACTIONS.get(action, 0)
        print(f"  {action:20s} -> +{xp} XP")
    
    # Sistema Livelli
    print("\n📊 Sistema Livelli (esempi):")
    xp_examples = [0, 250, 1000, 5000, 25000, 100000]
    for xp in xp_examples:
        level = LevelConfig.get_level_from_xp(xp)
        xp_next = LevelConfig.get_xp_for_next_level(xp)
        title = LevelConfig.TITLES.get(level, "Studente")
        print(f"  {xp:7d} XP -> Livello {level:2d} ({title:15s}) | Mancano {xp_next} XP")
    
    # Badge System
    print("\n🏆 Sistema Badge:")
    for badge_id, badge_data in list(BadgeConfig.BADGES.items())[:5]:
        rarity = badge_data['rarity']
        color = BadgeConfig.RARITY_COLORS[rarity]
        print(f"  {badge_data['icon']} {badge_data['name']:25s} [{rarity:10s}] +{badge_data['xp_reward']} XP")

def demo_before_after():
    """Mostra confronto PRIMA/DOPO"""
    print("\n" + "="*60)
    print("🔄 CONFRONTO PRIMA/DOPO - BENEFICI REFACTORING")
    print("="*60)
    
    print("\n❌ PRIMA (codice duplicato):")
    print("""
    # In file A
    if len(password) < 8 or not any(c.isupper() for c in password):
        return False
    
    # In file B
    if len(password) < 8 or not any(c.isupper() for c in password):
        return False
    
    # In file C
    if len(password) < 8 or not any(c.isupper() for c in password):
        return False
    """)
    
    print("\n✅ DOPO (modulo centralizzato):")
    print("""
    from shared.validators.input_validators import validator
    
    is_valid, error = validator.validate_password(password)
    if not is_valid:
        return error
    """)
    
    print("\n🎯 VANTAGGI:")
    print("  • ✅ Codice DRY (Don't Repeat Yourself)")
    print("  • ✅ Facile da testare (un solo posto)")
    print("  • ✅ Facile da modificare (un solo posto)")
    print("  • ✅ Consistenza garantita in tutta l'app")
    print("  • ✅ Messaggi d'errore uniformi")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 SKAILA - DEMO NUOVI MODULI CENTRALIZZATI")
    print("="*60)
    
    demo_validators()
    demo_date_formatters()
    demo_file_formatters()
    demo_configurations()
    demo_gamification_config()
    demo_before_after()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETATA!")
    print("="*60)
    print("\n💡 Questi moduli migliorano:")
    print("  • Sicurezza (validazione centralizzata)")
    print("  • Manutenibilità (codice DRY)")
    print("  • Scalabilità (facile aggiungere funzionalità)")
    print("  • Testabilità (moduli indipendenti)")
    print("  • Consistenza (SSoT per configurazioni)")
    print("\n")
