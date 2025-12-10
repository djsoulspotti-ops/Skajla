/**
 * SKAJLA - Interactive Classmate Spirals Visualization
 * Real-time visualization of online classmates as interactive moving spirals
 * Privacy-first: ONLY shows users from the same class (classe_id filtering)
 * 
 * Features:
 * - Canvas-based rendering for performance
 * - Smooth spiral animations with organic movement
 * - Mouse interaction (spirals react to cursor)
 * - Real-time Socket.IO updates
 * - Low CPU usage (<5%)
 */

class ClassmateSpirals {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }
        
        this.options = {
            canvasWidth: window.innerWidth,
            canvasHeight: window.innerHeight,
            spiralSegments: 30,        // Number of points in spiral
            spiralTurns: 2.5,          // Number of complete rotations
            spiralSpeed: 0.0008,       // Rotation speed (radians per frame)
            driftSpeed: 0.0003,        // Random drift speed
            mouseInfluence: 80,        // Pixels of mouse influence radius
            maxSpirals: 20,            // Maximum concurrent spirals
            updateInterval: 30000,     // API refresh interval (30s)
            opacity: 0.15,             // Base opacity for subtlety
            lineWidth: 2,              // Spiral line thickness
            ...options
        };
        
        this.classmates = [];
        this.spirals = [];
        this.canvas = null;
        this.ctx = null;
        this.socket = null;
        this.updateTimer = null;
        this.animationId = null;
        this.mouseX = 0;
        this.mouseY = 0;
        this.isRunning = false;
        
        this.init();
    }
    
    init() {
        console.log('🌀 Initializing Classmate Spirals...');
        
        // Prevent multiple instances
        if (this.container._spiralsInstance) {
            console.warn('⚠️ Destroying existing spiral instance');
            this.container._spiralsInstance.destroy();
        }
        this.container._spiralsInstance = this;
        
        // Create canvas element
        this.createCanvas();
        
        // Setup mouse tracking (use bound function for cleanup)
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleResize = this.handleResize.bind(this);
        document.addEventListener('mousemove', this.handleMouseMove);
        window.addEventListener('resize', this.handleResize);
        
        // Fetch initial classmates from API
        this.fetchClassmates();
        
        // Setup Socket.IO listeners for real-time updates
        this.setupSocketListeners();
        
        // Start animation loop
        this.startAnimation();
        
        // Periodic API refresh
        this.startPeriodicUpdates();
    }
    
    handleMouseMove(e) {
        const rect = this.container.getBoundingClientRect();
        this.mouseX = e.clientX - rect.left;
        this.mouseY = e.clientY - rect.top;
    }
    
    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.options.canvasWidth;
        this.canvas.height = this.options.canvasHeight;
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';  // Allow clicks to pass through
        this.canvas.style.zIndex = '0';
        this.canvas.classList.add('classmate-spirals-canvas');
        
        this.ctx = this.canvas.getContext('2d', { alpha: true });
        this.container.appendChild(this.canvas);
        
        console.log('✅ Canvas created:', this.canvas.width, 'x', this.canvas.height);
    }
    
    
    async fetchClassmates() {
        try {
            const response = await fetch('/api/online-classmates');
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            this.classmates = data.classmates || [];
            
            console.log(`👥 Fetched ${this.classmates.length} online classmates`);
            
            // Update spirals based on new classmate data
            this.updateSpirals();
            
        } catch (error) {
            console.error('❌ Error fetching classmates:', error);
            this.classmates = [];
        }
    }
    
    setupSocketListeners() {
        // Connect to Socket.IO (assumes global socket connection exists)
        if (typeof io !== 'undefined' && window.socket) {
            this.socket = window.socket;
            
            // Listen for user connected events
            this.socket.on('user_connected', (data) => {
                console.log('🟢 Classmate connected:', data);
                this.fetchClassmates(); // Refresh classmate list
            });
            
            // Listen for user disconnected events
            this.socket.on('user_disconnected', (data) => {
                console.log('🔴 Classmate disconnected:', data);
                this.fetchClassmates(); // Refresh classmate list
            });
            
            console.log('✅ Socket.IO listeners attached');
        } else {
            console.warn('⚠️ Socket.IO not available, real-time updates disabled');
        }
    }
    
    updateSpirals() {
        const targetCount = Math.min(this.classmates.length, this.options.maxSpirals);
        
        // Remove excess spirals if classmates decreased
        while (this.spirals.length > targetCount) {
            this.spirals.pop();
        }
        
        // Add new spirals if classmates increased
        while (this.spirals.length < targetCount) {
            const classmateIndex = this.spirals.length;
            const classmate = this.classmates[classmateIndex];
            
            this.spirals.push(this.createSpiral(classmate));
        }
        
        console.log(`🌀 Updated spirals count: ${this.spirals.length}`);
    }
    
    createSpiral(classmate) {
        return {
            classmate: classmate,
            centerX: Math.random() * this.canvas.width,
            centerY: Math.random() * this.canvas.height,
            rotation: Math.random() * Math.PI * 2,
            scale: 0.8 + Math.random() * 0.4,  // 0.8 - 1.2x scale
            driftAngle: Math.random() * Math.PI * 2,
            driftPhase: Math.random() * 1000,
            color: classmate.avatar_color || this.getRandomColor(),
            opacity: this.options.opacity
        };
    }
    
    startAnimation() {
        if (this.isRunning) {
            console.warn('⚠️ Animation already running');
            return;
        }
        this.isRunning = true;
        this.animate();
    }
    
    stopAnimation() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    animate() {
        if (!this.isRunning) return;
        
        // Clear canvas with transparency
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw all spirals
        this.spirals.forEach(spiral => {
            this.drawSpiral(spiral);
            this.updateSpiralPosition(spiral);
        });
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    drawSpiral(spiral) {
        this.ctx.save();
        
        // Translate to spiral center
        this.ctx.translate(spiral.centerX, spiral.centerY);
        this.ctx.rotate(spiral.rotation);
        this.ctx.scale(spiral.scale, spiral.scale);
        
        // Calculate mouse distance for interactivity
        const dx = this.mouseX - spiral.centerX;
        const dy = this.mouseY - spiral.centerY;
        const distanceToMouse = Math.sqrt(dx * dx + dy * dy);
        
        // Increase opacity and size when mouse is near (capped at 0.3 max opacity)
        let interactiveOpacity = spiral.opacity;
        let interactiveScale = 1;
        
        if (distanceToMouse < this.options.mouseInfluence) {
            const influence = 1 - (distanceToMouse / this.options.mouseInfluence);
            // Cap max opacity at 0.3 for subtlety
            interactiveOpacity = Math.min(spiral.opacity + (0.15 * influence), 0.3);
            interactiveScale = 1 + (0.15 * influence);
        }
        
        this.ctx.scale(interactiveScale, interactiveScale);
        
        // Draw spiral path
        this.ctx.beginPath();
        this.ctx.strokeStyle = spiral.color;
        this.ctx.globalAlpha = interactiveOpacity;
        this.ctx.lineWidth = this.options.lineWidth;
        this.ctx.lineCap = 'round';
        
        // Generate spiral points using parametric equation
        const maxRadius = 60;  // Maximum spiral radius
        
        for (let i = 0; i <= this.options.spiralSegments; i++) {
            const t = i / this.options.spiralSegments;
            const angle = t * this.options.spiralTurns * Math.PI * 2;
            const radius = t * maxRadius;
            
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.stroke();
        
        // Draw center dot (classmate indicator)
        this.ctx.beginPath();
        this.ctx.arc(0, 0, 4, 0, Math.PI * 2);
        this.ctx.fillStyle = spiral.color;
        this.ctx.globalAlpha = interactiveOpacity + 0.2;
        this.ctx.fill();
        
        this.ctx.restore();
    }
    
    updateSpiralPosition(spiral) {
        // Rotate spiral
        spiral.rotation += this.options.spiralSpeed;
        
        // Organic drift movement
        spiral.driftPhase += this.options.driftSpeed;
        const driftX = Math.cos(spiral.driftPhase) * 0.5;
        const driftY = Math.sin(spiral.driftPhase * 1.3) * 0.5;
        
        spiral.centerX += driftX;
        spiral.centerY += driftY;
        
        // Bounce off edges with soft boundaries
        const margin = 100;
        if (spiral.centerX < -margin) spiral.centerX = this.canvas.width + margin;
        if (spiral.centerX > this.canvas.width + margin) spiral.centerX = -margin;
        if (spiral.centerY < -margin) spiral.centerY = this.canvas.height + margin;
        if (spiral.centerY > this.canvas.height + margin) spiral.centerY = -margin;
    }
    
    startPeriodicUpdates() {
        // Refresh classmate data every 30 seconds
        this.updateTimer = setInterval(() => {
            this.fetchClassmates();
        }, this.options.updateInterval);
    }
    
    handleResize() {
        if (!this.canvas) return;
        
        // Update canvas size on window resize
        this.options.canvasWidth = this.container.clientWidth;
        this.options.canvasHeight = this.container.clientHeight;
        this.canvas.width = this.options.canvasWidth;
        this.canvas.height = this.options.canvasHeight;
        
        console.log('📐 Canvas resized:', this.canvas.width, 'x', this.canvas.height);
    }
    
    getRandomColor() {
        const colors = [
            '#003B73',  // Navy blue
            '#0074D9',  // Blue
            '#7FDBFF',  // Light blue
            '#39CCCC',  // Teal
            '#2ECC40',  // Green
            '#FF851B',  // Orange
            '#F012BE',  // Fuchsia
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    destroy() {
        console.log('🗑️ Destroying Classmate Spirals...');
        
        // Stop animation loop
        this.stopAnimation();
        
        // Clear periodic update timer
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
        
        // Remove event listeners
        if (this.handleMouseMove) {
            document.removeEventListener('mousemove', this.handleMouseMove);
        }
        if (this.handleResize) {
            window.removeEventListener('resize', this.handleResize);
        }
        
        // Remove socket listeners
        if (this.socket) {
            this.socket.off('user_connected');
            this.socket.off('user_disconnected');
        }
        
        // Remove canvas
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.remove();
            this.canvas = null;
            this.ctx = null;
        }
        
        // Clear instance reference
        if (this.container) {
            delete this.container._spiralsInstance;
        }
        
        // Clear arrays
        this.spirals = [];
        this.classmates = [];
        
        console.log('✅ Classmate Spirals destroyed');
    }
}

// Export for use in other scripts
window.ClassmateSpirals = ClassmateSpirals;
