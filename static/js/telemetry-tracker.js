/**
 * SKAJLA Behavioral Telemetry Tracker
 * Automatically tracks student learning behaviors for early warning system
 * Part of Feature #1: Smart AI-Tutoring & Early-Warning Engine
 */

class TelemetryTracker {
    constructor() {
        this.sessionId = null;
        this.eventQueue = [];
        this.batchSize = 5;
        this.batchInterval = 10000; // Send batch every 10 seconds
        this.pageStartTime = Date.now();
        this.currentTaskStartTime = null;
        this.currentTaskId = null;
        this.eventIdCounter = 0; // For generating stable event IDs
        this.STORAGE_KEY = 'skaila_telemetry_queue'; // localStorage key
        
        this.init();
    }
    
    async init() {
        // CRITICAL: Restore persisted queue from localStorage first
        this._restoreQueueFromStorage();
        
        try {
            // Start telemetry session
            const response = await fetch('/api/telemetry/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_type: this.getDeviceType()
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('✅ Telemetry session started:', this.sessionId);
                
                // CRITICAL: Flush restored queue from previous session
                if (this.eventQueue.length > 0) {
                    console.log(`🔄 Retrying ${this.eventQueue.length} events from previous session`);
                    this.flushQueue(false);
                }
            }
        } catch (error) {
            console.warn('⚠️ Failed to start telemetry session:', error);
        }
        
        // Auto-track page view
        this.trackPageView();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Start batch processor
        this.startBatchProcessor();
    }
    
    setupEventListeners() {
        // Track page exit - CRITICAL: Always flush queue even if empty
        window.addEventListener('beforeunload', () => {
            this.trackPageExit();
            this.flushQueue(true); // Synchronous send before leaving
        });
        
        // Additional exit handlers for mobile/tablet
        window.addEventListener('pagehide', () => {
            this.flushQueue(true);
        });
        
        // Track visibility changes (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.trackEvent('page_hidden', {
                    page: window.location.pathname,
                    time_spent: Date.now() - this.pageStartTime
                });
                // CRITICAL: Flush queue when tab hidden (mobile suspend protection)
                this.flushQueue(true);
            } else {
                this.pageStartTime = Date.now();
                this.trackEvent('page_visible', {
                    page: window.location.pathname
                });
            }
        });
        
        // Flush on navigation (SPA protection)
        window.addEventListener('popstate', () => {
            this.flushQueue(false);
        });
    }
    
    startBatchProcessor() {
        // CRITICAL: Always flush queue on interval, even if not full
        // This prevents event loss when queue < batchSize
        setInterval(() => {
            if (this.eventQueue.length > 0) {
                this.flushQueue(false);
            }
        }, this.batchInterval);
    }
    
    trackPageView() {
        this.trackEvent('page_view', {
            page: window.location.pathname,
            referrer: document.referrer,
            screen_width: window.screen.width,
            screen_height: window.screen.height
        });
    }
    
    trackPageExit() {
        const duration = Math.floor((Date.now() - this.pageStartTime) / 1000);
        this.trackEvent('page_exit', {
            page: window.location.pathname,
            duration_seconds: duration
        });
    }
    
    /**
     * Track task start (quiz, exercise, etc.)
     */
    trackTaskStart(taskId, subject, taskType = 'exercise') {
        this.currentTaskId = taskId;
        this.currentTaskStartTime = Date.now();
        
        this.trackEvent('task_start', {
            task_id: taskId,
            subject: subject,
            task_type: taskType
        });
    }
    
    /**
     * Track task submission with performance data
     */
    trackTaskSubmit(taskId, subject, accuracyScore, retryCount = 0, hintsUsed = 0, errorCount = 0) {
        const duration = this.currentTaskStartTime 
            ? Math.floor((Date.now() - this.currentTaskStartTime) / 1000) 
            : null;
        
        this.trackEvent('task_submit', {
            task_id: taskId,
            subject: subject,
            accuracy: accuracyScore,
            retry_count: retryCount,
            hints_used: hintsUsed,
            error_count: errorCount
        }, duration, accuracyScore);
        
        // Reset task tracking
        this.currentTaskId = null;
        this.currentTaskStartTime = null;
    }
    
    /**
     * Track quiz answer (individual question)
     */
    trackQuizAnswer(questionId, subject, isCorrect, timeSpent, hintsUsed = 0) {
        this.trackEvent('quiz_answer', {
            question_id: questionId,
            subject: subject,
            is_correct: isCorrect,
            hints_used: hintsUsed,
            response_time: timeSpent
        }, timeSpent, isCorrect ? 100 : 0);
    }
    
    /**
     * Track material interaction (PDF, video, etc.)
     */
    trackMaterialOpen(materialId, materialType, subject) {
        this.trackEvent('material_open', {
            material_id: materialId,
            material_type: materialType,
            subject: subject
        });
    }
    
    /**
     * Track video watching behavior
     */
    trackVideoWatch(videoId, subject, watchDuration, totalDuration, completionRate) {
        this.trackEvent('video_watch', {
            video_id: videoId,
            subject: subject,
            watch_duration: watchDuration,
            total_duration: totalDuration,
            completion_rate: completionRate
        }, watchDuration);
    }
    
    /**
     * Track AI chat interaction
     */
    trackAIChatInteraction(subject, messageCount, sessionDuration) {
        this.trackEvent('ai_chat_interaction', {
            subject: subject,
            message_count: messageCount,
            session_duration: sessionDuration
        }, sessionDuration);
    }
    
    /**
     * Core event tracking method
     */
    trackEvent(eventType, context, durationSeconds = null, accuracyScore = null) {
        // CRITICAL: Add stable client-side event ID for correlation across retries
        const clientEventId = `evt_${Date.now()}_${this.eventIdCounter++}_${Math.random().toString(36).substr(2, 9)}`;
        
        const event = {
            client_event_id: clientEventId,
            event_type: eventType,
            context: {
                ...context,
                session_id: this.sessionId,
                device_type: this.getDeviceType(),
                timestamp: new Date().toISOString()
            },
            duration_seconds: durationSeconds,
            accuracy_score: accuracyScore
        };
        
        this.eventQueue.push(event);
        
        // CRITICAL: Flush immediately for high-priority events (task submissions)
        if (['task_submit', 'quiz_answer'].includes(eventType)) {
            this.flushQueue(false);
        }
        // Auto-flush if queue reaches batch size
        else if (this.eventQueue.length >= this.batchSize) {
            this.flushQueue(false);
        }
    }
    
    /**
     * Send event queue to server with sendBeacon fallback
     * CRITICAL: Only clears queue after confirming successful send
     */
    async flushQueue(isSync = false) {
        if (this.eventQueue.length === 0) return;
        
        const eventsToSend = [...this.eventQueue];
        
        const payload = { events: eventsToSend };
        
        try {
            if (isSync) {
                // CRITICAL: NEVER use sendBeacon for critical data - always use XHR
                // sendBeacon offers NO confirmation of HTTP response, so we can't verify success
                // ALWAYS use synchronous XHR which allows status/response validation
                const sendResult = this._synchronousFlush(payload);
                
                // CRITICAL: Use explicit acknowledged_ids for positive confirmation
                // ONLY remove events that server explicitly acknowledges
                if (sendResult && sendResult.acknowledged_ids) {
                    const ackedIds = new Set(sendResult.acknowledged_ids);
                    
                    // CRITICAL: Also quarantine failed events (invalid - don't retry)
                    let idsToRemove = new Set(ackedIds);
                    if (sendResult.failed_events && sendResult.failed_events.length > 0) {
                        const failedIds = new Set(sendResult.failed_events.map(f => f.client_event_id));
                        // Add failed events to removal set (quarantine them)
                        failedIds.forEach(id => idsToRemove.add(id));
                        console.error('Quarantined invalid events:', sendResult.failed_events);
                    }
                    
                    // Remove acknowledged events AND quarantined invalid events
                    this.eventQueue = this.eventQueue.filter(e => !idsToRemove.has(e.client_event_id));
                    
                    if (ackedIds.size !== eventsToSend.length) {
                        console.warn(
                            `⚠️ Partial sync success: ${ackedIds.size}/${eventsToSend.length} events acknowledged`
                        );
                    }
                    
                    // CRITICAL: Clear localStorage if queue is now empty
                    if (this.eventQueue.length === 0) {
                        this._clearStorage();
                    } else {
                        // CRITICAL: Persist remaining events for next session
                        this._persistQueueToStorage();
                    }
                } else if (sendResult && !sendResult.success) {
                    // Send failed completely - keep all events for retry
                    console.warn('⚠️ Synchronous flush failed, events retained for retry');
                    // CRITICAL: Persist queue to survive page unload
                    this._persistQueueToStorage();
                } else {
                    // No acknowledged_ids list - safest is to keep all for retry
                    console.warn('⚠️ No acknowledgements received, events retained');
                    // CRITICAL: Persist queue to survive page unload
                    this._persistQueueToStorage();
                }
                
            } else {
                // Standard async fetch with validation
                const response = await fetch('/api/telemetry/events/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) {
                    // Non-OK response - requeue events and retry if recoverable
                    if (response.status === 503) {
                        const data = await response.json();
                        if (data.recoverable && data.retry_after) {
                            // Server says retry after N seconds
                            setTimeout(() => {
                                this.flushQueue(false);
                            }, data.retry_after * 1000);
                        }
                    } else {
                        // Other errors (500, 429, etc.) - log and keep events for next flush
                        console.error(`❌ Telemetry batch failed with ${response.status}`);
                    }
                    return; // Don't clear queue on failure
                }
                
                // CRITICAL: Use explicit acknowledged_ids for positive confirmation
                const data = await response.json();
                
                // ONLY remove events explicitly acknowledged by server
                if (data.acknowledged_ids && Array.isArray(data.acknowledged_ids)) {
                    const ackedIds = new Set(data.acknowledged_ids);
                    this.eventQueue = this.eventQueue.filter(e => !ackedIds.has(e.client_event_id));
                    
                    if (ackedIds.size !== eventsToSend.length) {
                        console.warn(
                            `⚠️ Partial telemetry success: ${ackedIds.size}/${eventsToSend.length} events acknowledged`
                        );
                        if (data.failed_events) {
                            console.error('Failed events:', data.failed_events);
                        }
                    }
                    
                    // CRITICAL: Update localStorage after successful async flush
                    if (this.eventQueue.length === 0) {
                        this._clearStorage();
                    } else {
                        this._persistQueueToStorage();
                    }
                } else {
                    // No acknowledged_ids - keep all events for safety
                    console.warn('⚠️ No acknowledgements received, retaining all events');
                    // CRITICAL: Persist for next attempt
                    this._persistQueueToStorage();
                }
            }
        } catch (error) {
            console.warn('⚠️ Failed to send telemetry batch:', error);
            // Events remain in queue for next flush attempt (automatic retry)
        }
    }
    
    /**
     * Synchronous flush using XMLHttpRequest
     * Returns full response data including per-event failures
     */
    _synchronousFlush(payload) {
        try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/telemetry/events/batch', false); // false = synchronous
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(payload));
            
            // CRITICAL: Check HTTP status and parse full response
            if (xhr.status >= 200 && xhr.status < 300) {
                // Parse response including failed_events details
                try {
                    const response = JSON.parse(xhr.responseText);
                    
                    // CRITICAL: Return full response data including acknowledged_ids
                    return {
                        success: true,
                        tracked_count: response.tracked_count || 0,
                        total_events: payload.events.length,
                        acknowledged_ids: response.acknowledged_ids || [],
                        failed_events: response.failed_events || [],
                        partial_success: (response.tracked_count !== payload.events.length)
                    };
                } catch (parseError) {
                    console.warn('⚠️ Failed to parse sync response:', parseError);
                    return { success: false, retryable: true };
                }
            } else if (xhr.status === 503) {
                // Server says retry - keep all events
                return { success: false, retryable: true };
            } else {
                // Other error (500, 429, etc.) - keep all events for retry
                console.error(`❌ Synchronous flush failed with status ${xhr.status}`);
                return { success: false, retryable: true };
            }
        } catch (error) {
            console.error('❌ Synchronous telemetry flush exception:', error);
            return { success: false, retryable: true };
        }
    }
    
    getDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (/mobile|android|iphone/i.test(userAgent)) {
            return 'mobile';
        } else if (/tablet|ipad/i.test(userAgent)) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }
    
    /**
     * CRITICAL: Restore event queue from localStorage
     * Ensures zero event loss across page navigations
     */
    _restoreQueueFromStorage() {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    this.eventQueue = parsed;
                    console.log(`📦 Restored ${parsed.length} events from localStorage`);
                }
            }
        } catch (error) {
            console.warn('⚠️ Failed to restore queue from localStorage:', error);
        }
    }
    
    /**
     * CRITICAL: Persist event queue to localStorage
     * Called when synchronous flush fails to get acknowledgements
     */
    _persistQueueToStorage() {
        try {
            if (this.eventQueue.length > 0) {
                localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.eventQueue));
                console.log(`💾 Persisted ${this.eventQueue.length} events to localStorage`);
            } else {
                this._clearStorage();
            }
        } catch (error) {
            console.error('❌ Failed to persist queue to localStorage:', error);
        }
    }
    
    /**
     * Clear persisted queue from localStorage after successful flush
     */
    _clearStorage() {
        try {
            localStorage.removeItem(this.STORAGE_KEY);
        } catch (error) {
            console.warn('⚠️ Failed to clear localStorage:', error);
        }
    }
}

// Auto-initialize telemetry tracker globally
let telemetryTracker;

document.addEventListener('DOMContentLoaded', () => {
    telemetryTracker = new TelemetryTracker();
    window.telemetryTracker = telemetryTracker; // Make available globally
    console.log('🎯 SKAJLA Telemetry Tracker initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TelemetryTracker;
}
