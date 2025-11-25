"""
SKAILA Telemetry API Routes
Handles behavioral telemetry tracking and early warning system
Part of Feature #1: Smart AI-Tutoring & Early-Warning Engine
"""

from flask import Blueprint, request, jsonify, session, render_template
from services.telemetry.telemetry_engine import telemetry_engine
from shared.middleware.auth import require_login, require_role
from shared.error_handling import get_logger

logger = get_logger(__name__)

telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/telemetry')


@telemetry_bp.route('/events/track', methods=['POST'])
@require_login
def track_single_event():
    """
    Track a single telemetry event
    
    Request JSON:
    {
        "event_type": "task_submit",
        "context": {
            "task_id": 123,
            "subject": "matematica",
            "accuracy": 75.5,
            "duration_seconds": 120,
            "retry_count": 2,
            "errors": 3
        }
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        event_type = data.get('event_type')
        if not event_type:
            return jsonify({"success": False, "error": "event_type required"}), 400
        
        context = data.get('context', {})
        
        # Validate and sanitize context (max 100KB, only allowed keys)
        context = _validate_and_sanitize_context(context, user_id)
        if context is None:
            return jsonify({"success": False, "error": "Invalid context data"}), 400
        
        duration = context.get('duration_seconds')
        accuracy = context.get('accuracy')
        
        context['session_id'] = session.get('telemetry_session_id')
        context['device_type'] = _get_device_type(request.user_agent.string)
        
        event_id = telemetry_engine.track_event(
            user_id=user_id,
            event_type=event_type,
            context=context,
            duration_seconds=duration,
            accuracy_score=accuracy
        )
        
        if not event_id:
            logger.error(
                event_type='event_tracking_failed',
                domain='telemetry_api',
                user_id=user_id,
                event_type_value=event_type
            )
            return jsonify({
                "success": False,
                "error": "Failed to track event. Event may not have been recorded.",
                "retry_after": 3,
                "recoverable": True
            }), 503
        
        return jsonify({
            "success": True,
            "event_id": event_id
        })
        
    except Exception as e:
        logger.error(
            event_type='telemetry_track_failed',
            domain='telemetry_api',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            "success": False,
            "error": "Failed to track event"
        }), 500


@telemetry_bp.route('/events/batch', methods=['POST'])
@require_login
def track_batch_events():
    """
    Track multiple telemetry events in batch (for efficiency)
    
    Request JSON:
    {
        "events": [
            {
                "event_type": "page_view",
                "context": {"page": "/dashboard"}
            },
            {
                "event_type": "task_start",
                "context": {"task_id": 456}
            }
        ]
    }
    """
    try:
        user_id = session.get('user_id')
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        events = data.get('events', [])
        
        # Limit batch size to prevent resource exhaustion
        if len(events) > 100:
            return jsonify({
                "success": False,
                "error": "Batch too large (max 100 events)"
            }), 400
        
        tracked_count = 0
        failed_events = []
        acknowledged_ids = []  # CRITICAL: Explicit positive acknowledgements
        
        for idx, event_data in enumerate(events):
            try:
                # CRITICAL: Use stable client_event_id for correlation (not array index)
                client_event_id = event_data.get('client_event_id', f'server_gen_{idx}')
                
                event_type = event_data.get('event_type')
                if not event_type:
                    failed_events.append({
                        "client_event_id": client_event_id,
                        "reason": "missing_event_type",
                        "event": event_data
                    })
                    continue
                
                context = event_data.get('context', {})
                
                # Validate and sanitize context
                context = _validate_and_sanitize_context(context, user_id)
                if context is None:
                    failed_events.append({
                        "client_event_id": client_event_id,
                        "reason": "invalid_context",
                        "event_type": event_type
                    })
                    continue
                
                duration = event_data.get('duration_seconds') or context.get('duration_seconds')
                accuracy = event_data.get('accuracy_score') or context.get('accuracy')
                
                context['session_id'] = session.get('telemetry_session_id')
                context['device_type'] = _get_device_type(request.user_agent.string)
                
                event_id = telemetry_engine.track_event(
                    user_id=user_id,
                    event_type=event_type,
                    context=context,
                    duration_seconds=duration,
                    accuracy_score=accuracy
                )
                
                if event_id:
                    tracked_count += 1
                    # CRITICAL: Add to acknowledged list (explicit confirmation)
                    acknowledged_ids.append(client_event_id)
                else:
                    failed_events.append({
                        "client_event_id": client_event_id,
                        "reason": "database_insert_failed",
                        "event_type": event_type
                    })
                    
            except Exception as event_error:
                logger.warning(
                    event_type='batch_event_exception',
                    domain='telemetry_api',
                    error=str(event_error),
                    event_index=idx,
                    client_event_id=event_data.get('client_event_id', 'unknown')
                )
                failed_events.append({
                    "client_event_id": event_data.get('client_event_id', f'server_gen_{idx}'),
                    "reason": "exception",
                    "error": str(event_error)
                })
                continue
        
        # CRITICAL: Always return acknowledged_ids for explicit positive confirmation
        # Frontend ONLY removes events in this list
        response_data = {
            "success": tracked_count == len(events),  # True only if ALL succeeded
            "tracked_count": tracked_count,
            "total_events": len(events),
            "acknowledged_ids": acknowledged_ids  # CRITICAL: Explicit positive acks
        }
        
        if failed_events:
            response_data["failed_events"] = failed_events
        
        # Return appropriate status code
        if tracked_count == 0 and len(events) > 0:
            logger.error(
                event_type='batch_complete_failure',
                domain='telemetry_api',
                user_id=user_id,
                total_events=len(events)
            )
            response_data["error"] = "All events failed to track"
            response_data["retry_after"] = 5
            response_data["recoverable"] = True
            return jsonify(response_data), 503
        elif failed_events:
            logger.warning(
                event_type='batch_partial_success',
                domain='telemetry_api',
                tracked=tracked_count,
                failed=len(failed_events)
            )
            # Partial success - use 200 but client checks acknowledged_ids
            return jsonify(response_data), 200
        else:
            # Full success
            return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(
            event_type='telemetry_batch_failed',
            domain='telemetry_api',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            "success": False,
            "error": "Failed to track batch events"
        }), 500


@telemetry_bp.route('/session/start', methods=['POST'])
@require_login
def start_session():
    """Start a new telemetry session"""
    try:
        user_id = session.get('user_id')
        data = request.json or {}
        
        device_type = data.get('device_type') or _get_device_type(request.user_agent.string)
        session_id = telemetry_engine._get_or_create_session(user_id, device_type)
        
        if not session_id:
            logger.error(
                event_type='session_creation_failed',
                domain='telemetry_api',
                user_id=user_id,
                message='Database insert failed or returned no rows'
            )
            return jsonify({
                "success": False,
                "error": "Failed to create telemetry session. Please refresh the page or try again.",
                "retry_after": 5,
                "recoverable": True
            }), 503
        
        session['telemetry_session_id'] = session_id
        
        return jsonify({
            "success": True,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(
            event_type='session_start_failed',
            domain='telemetry_api',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            "success": False,
            "error": "Failed to start session"
        }), 500


def _validate_and_sanitize_context(context: dict, user_id: int) -> dict:
    """
    Validate and sanitize context data to prevent JSONB bloat
    Allows nested structures required by telemetry blueprint
    
    Returns:
        Sanitized context dict or None if invalid
    """
    import json
    
    if not isinstance(context, dict):
        return None
    
    # Size limit: 100KB max (prevents JSONB bloat attacks)
    try:
        context_json = json.dumps(context)
        context_size = len(context_json.encode('utf-8'))
        
        if context_size > 102400:  # 100KB
            logger.warning(
                event_type='context_size_exceeded',
                domain='telemetry_api',
                user_id=user_id,
                size=context_size
            )
            return None
            
    except (TypeError, ValueError) as e:
        logger.warning(
            event_type='context_serialization_failed',
            domain='telemetry_api',
            user_id=user_id,
            error=str(e)
        )
        return None
    
    # Recursive validation: ensure no deeply nested structures (max depth 3)
    def validate_depth(obj, current_depth=0, max_depth=3):
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            for value in obj.values():
                if not validate_depth(value, current_depth + 1, max_depth):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not validate_depth(item, current_depth + 1, max_depth):
                    return False
        elif not isinstance(obj, (str, int, float, bool, type(None))):
            # Disallow objects/functions/etc
            return False
        
        return True
    
    if not validate_depth(context):
        logger.warning(
            event_type='context_depth_exceeded',
            domain='telemetry_api',
            user_id=user_id
        )
        return None
    
    return context


def _get_device_type(user_agent_string: str) -> str:
    """Determine device type from user agent"""
    user_agent_lower = user_agent_string.lower()
    
    if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone']):
        return 'mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        return 'tablet'
    else:
        return 'desktop'
