"""
SKAILA - Cyberpunk Presence System Routes
Demo page for the enhanced presence visualization
"""

from flask import Blueprint, render_template
from shared.middleware.auth import require_auth

cyberpunk_presence_bp = Blueprint('cyberpunk_presence', __name__)

@cyberpunk_presence_bp.route('/cyberpunk-presence-demo')
@require_auth
def cyberpunk_presence_demo():
    """
    Demo page for the Cyberpunk Presence System
    Shows real-time online users with 3D depth, neon glow, and GSAP animations
    """
    return render_template('cyberpunk_presence_demo.html')
