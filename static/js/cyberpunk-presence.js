/**
 * SKAILA - Cyberpunk Presence System
 * 3D floating particle network for online user visualization
 * Uses GSAP for smooth physics-like animations with parallax depth
 */

class CyberpunkPresence {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }
        
        this.options = {
            maxUsers: 12,
            canvasWidth: 600,
            canvasHeight: 600,
            particleSize: 40,
            updateInterval: 30000,
            enableParallax: true,
            glowIntensity: 0.8,
            ...options
        };
        
        this.onlineUsers = [];
        this.particles = [];
        this.socket = null;
        this.updateTimer = null;
        this.canvas = null;
        this.ctx = null;
        this.mouseX = 0;
        this.mouseY = 0;
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        // Check if GSAP is loaded
        if (typeof gsap === 'undefined') {
            console.warn('⚠️ GSAP not loaded, falling back to CSS animations');
            this.useGSAP = false;
        } else {
            this.useGSAP = true;
            console.log('✨ GSAP loaded - using advanced animations');
        }
        
        // Setup container
        this.container.classList.add('cyberpunk-presence-container');
        
        // Create canvas for particle effects
        this.createCanvas();
        
        // Setup mouse tracking for parallax
        if (this.options.enableParallax) {
            this.setupParallax();
        }
        
        // Fetch initial online users
        this.fetchOnlineUsers();
        
        // Setup Socket.IO listeners
        this.setupSocketListeners();
        
        // Start periodic updates
        this.startPeriodicUpdates();
    }
    
    createCanvas() {
        // Create SVG container for better quality
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'cyberpunk-canvas');
        svg.setAttribute('width', this.options.canvasWidth);
        svg.setAttribute('height', this.options.canvasHeight);
        svg.setAttribute('viewBox', `0 0 ${this.options.canvasWidth} ${this.options.canvasHeight}`);
        
        // Add gradient definitions for neon glow
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Neon gradient filters
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'neon-glow');
        filter.innerHTML = `
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        `;
        defs.appendChild(filter);
        
        svg.appendChild(defs);
        this.container.appendChild(svg);
        this.svg = svg;
    }
    
    setupParallax() {
        // Track mouse for parallax effect
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouseX = (e.clientX - rect.left - rect.width / 2) / rect.width;
            this.mouseY = (e.clientY - rect.top - rect.height / 2) / rect.height;
        });
        
        this.container.addEventListener('mouseleave', () => {
            this.mouseX = 0;
            this.mouseY = 0;
        });
    }
    
    async fetchOnlineUsers() {
        try {
            const response = await fetch('/api/online-users');
            if (!response.ok) {
                throw new Error('Failed to fetch online users');
            }
            
            const data = await response.json();
            this.onlineUsers = data.users || [];
            this.createParticles();
        } catch (error) {
            console.error('Error fetching online users:', error);
        }
    }
    
    setupSocketListeners() {
        if (typeof io !== 'undefined' && window.socket) {
            this.socket = window.socket;
            
            this.socket.on('user_connected', (data) => {
                console.log('🌐 User connected:', data);
                this.fetchOnlineUsers();
            });
            
            this.socket.on('user_disconnected', (data) => {
                console.log('🌐 User disconnected:', data);
                this.fetchOnlineUsers();
            });
        }
    }
    
    startPeriodicUpdates() {
        this.updateTimer = setInterval(() => {
            this.fetchOnlineUsers();
        }, this.options.updateInterval);
    }
    
    createParticles() {
        // Clear existing particles
        this.particles.forEach(p => {
            if (p.element) p.element.remove();
        });
        this.particles = [];
        
        const usersToDisplay = this.onlineUsers.slice(0, this.options.maxUsers);
        
        if (usersToDisplay.length === 0) {
            return;
        }
        
        // Cyberpunk neon colors
        const neonColors = [
            { base: '#00D9FF', glow: '#00F0FF', name: 'cyan' },      // Electric cyan
            { base: '#0066FF', glow: '#0088FF', name: 'blue' },      // Electric blue
            { base: '#9D00FF', glow: '#B833FF', name: 'violet' },    // Neon violet
            { base: '#FF00FF', glow: '#FF33FF', name: 'magenta' },   // Hot magenta
            { base: '#00FFAA', glow: '#00FFCC', name: 'teal' },      // Matrix green-cyan
            { base: '#FF0080', glow: '#FF33AA', name: 'pink' },      // Hot pink
        ];
        
        usersToDisplay.forEach((user, index) => {
            const color = neonColors[index % neonColors.length];
            
            // Create particle with 3D depth layers
            const particle = {
                user: user,
                color: color,
                // Random starting position
                x: Math.random() * (this.options.canvasWidth - 100) + 50,
                y: Math.random() * (this.options.canvasHeight - 100) + 50,
                // Z-depth for parallax (0 = far, 1 = close)
                z: Math.random() * 0.6 + 0.4,
                // Velocity for floating motion
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                // Rotation
                rotation: Math.random() * 360,
                rotationSpeed: (Math.random() - 0.5) * 2,
                // Pulse animation
                pulse: 0,
                pulseSpeed: 0.02 + Math.random() * 0.03,
                element: null
            };
            
            // Create SVG element
            particle.element = this.createParticleElement(particle);
            this.svg.appendChild(particle.element);
            
            this.particles.push(particle);
            
            // Animate with GSAP if available
            if (this.useGSAP) {
                this.animateParticleWithGSAP(particle);
            }
        });
        
        // Start animation loop
        if (!this.animationId) {
            this.animate();
        }
    }
    
    createParticleElement(particle) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', 'cyberpunk-particle');
        group.setAttribute('data-user-id', particle.user.id);
        
        // Outer glow ring
        const outerGlow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        outerGlow.setAttribute('class', 'particle-glow-outer');
        outerGlow.setAttribute('cx', particle.x);
        outerGlow.setAttribute('cy', particle.y);
        outerGlow.setAttribute('r', this.options.particleSize * particle.z);
        outerGlow.setAttribute('fill', 'none');
        outerGlow.setAttribute('stroke', particle.color.glow);
        outerGlow.setAttribute('stroke-width', '2');
        outerGlow.setAttribute('opacity', '0.3');
        outerGlow.setAttribute('filter', 'url(#neon-glow)');
        
        // Middle glow ring
        const middleGlow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        middleGlow.setAttribute('class', 'particle-glow-middle');
        middleGlow.setAttribute('cx', particle.x);
        middleGlow.setAttribute('cy', particle.y);
        middleGlow.setAttribute('r', this.options.particleSize * 0.7 * particle.z);
        middleGlow.setAttribute('fill', particle.color.glow);
        middleGlow.setAttribute('opacity', '0.15');
        middleGlow.setAttribute('filter', 'url(#neon-glow)');
        
        // Core circle
        const core = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        core.setAttribute('class', 'particle-core');
        core.setAttribute('cx', particle.x);
        core.setAttribute('cy', particle.y);
        core.setAttribute('r', this.options.particleSize * 0.5 * particle.z);
        core.setAttribute('fill', particle.color.base);
        core.setAttribute('stroke', particle.color.glow);
        core.setAttribute('stroke-width', '2');
        core.setAttribute('filter', 'url(#neon-glow)');
        
        // User initials
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'particle-initials');
        text.setAttribute('x', particle.x);
        text.setAttribute('y', particle.y);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('fill', 'white');
        text.setAttribute('font-size', 14 * particle.z);
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('font-family', 'Inter, sans-serif');
        text.textContent = particle.user.initials;
        
        // Connection lines (will be drawn in animate loop)
        const connectionLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        connectionLine.setAttribute('class', 'particle-connection');
        connectionLine.setAttribute('stroke', particle.color.glow);
        connectionLine.setAttribute('stroke-width', '1');
        connectionLine.setAttribute('opacity', '0');
        
        group.appendChild(outerGlow);
        group.appendChild(middleGlow);
        group.appendChild(connectionLine);
        group.appendChild(core);
        group.appendChild(text);
        
        // Tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'cyberpunk-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-name">${particle.user.name}</div>
            <div class="tooltip-role">${particle.user.role}</div>
        `;
        tooltip.style.left = `${particle.x}px`;
        tooltip.style.top = `${particle.y - 60}px`;
        this.container.appendChild(tooltip);
        
        // Hover interactions
        group.addEventListener('mouseenter', () => {
            tooltip.classList.add('visible');
            if (this.useGSAP) {
                gsap.to(core, { r: this.options.particleSize * 0.6 * particle.z, duration: 0.3 });
                gsap.to(outerGlow, { opacity: 0.6, duration: 0.3 });
            }
        });
        
        group.addEventListener('mouseleave', () => {
            tooltip.classList.remove('visible');
            if (this.useGSAP) {
                gsap.to(core, { r: this.options.particleSize * 0.5 * particle.z, duration: 0.3 });
                gsap.to(outerGlow, { opacity: 0.3, duration: 0.3 });
            }
        });
        
        particle.tooltip = tooltip;
        
        return group;
    }
    
    animateParticleWithGSAP(particle) {
        // Floating motion with GSAP
        const floatX = particle.x + (Math.random() - 0.5) * 200;
        const floatY = particle.y + (Math.random() - 0.5) * 200;
        
        gsap.to(particle, {
            x: floatX,
            y: floatY,
            duration: 8 + Math.random() * 4,
            ease: 'sine.inOut',
            repeat: -1,
            yoyo: true,
            onUpdate: () => {
                this.updateParticlePosition(particle);
            }
        });
        
        // Rotation animation
        gsap.to(particle, {
            rotation: particle.rotation + 360,
            duration: 20 + Math.random() * 10,
            ease: 'none',
            repeat: -1
        });
        
        // Pulse animation
        gsap.to(particle, {
            pulse: 1,
            duration: 2 + Math.random(),
            ease: 'sine.inOut',
            repeat: -1,
            yoyo: true
        });
    }
    
    updateParticlePosition(particle) {
        if (!particle.element) return;
        
        const elements = particle.element.querySelectorAll('circle, text');
        const core = particle.element.querySelector('.particle-core');
        const text = particle.element.querySelector('.particle-initials');
        
        // Apply parallax offset based on mouse
        const parallaxX = this.mouseX * 30 * particle.z;
        const parallaxY = this.mouseY * 30 * particle.z;
        
        const finalX = particle.x + parallaxX;
        const finalY = particle.y + parallaxY;
        
        // Update all elements
        elements.forEach(el => {
            if (el.tagName === 'circle') {
                el.setAttribute('cx', finalX);
                el.setAttribute('cy', finalY);
            } else if (el.tagName === 'text') {
                el.setAttribute('x', finalX);
                el.setAttribute('y', finalY);
            }
        });
        
        // Update tooltip position
        if (particle.tooltip) {
            particle.tooltip.style.left = `${finalX}px`;
            particle.tooltip.style.top = `${finalY - 60}px`;
        }
        
        // Pulse effect
        if (core) {
            const pulseScale = 1 + particle.pulse * 0.1;
            core.setAttribute('r', this.options.particleSize * 0.5 * particle.z * pulseScale);
        }
    }
    
    animate() {
        // Animation loop for non-GSAP updates
        if (!this.useGSAP) {
            this.particles.forEach(particle => {
                // Simple floating motion
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                // Bounce off edges
                if (particle.x < 50 || particle.x > this.options.canvasWidth - 50) particle.vx *= -1;
                if (particle.y < 50 || particle.y > this.options.canvasHeight - 50) particle.vy *= -1;
                
                // Update pulse
                particle.pulse += particle.pulseSpeed;
                if (particle.pulse > 1 || particle.pulse < 0) particle.pulseSpeed *= -1;
                
                this.updateParticlePosition(particle);
            });
        } else {
            // Just update parallax
            this.particles.forEach(particle => {
                this.updateParticlePosition(particle);
            });
        }
        
        // Draw connection lines between nearby particles
        this.drawConnections();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    drawConnections() {
        // Draw lines between particles that are close together
        const connectionDistance = 150;
        
        this.particles.forEach((p1, i) => {
            this.particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < connectionDistance) {
                    const line = p1.element.querySelector('.particle-connection');
                    if (line) {
                        line.setAttribute('x1', p1.x);
                        line.setAttribute('y1', p1.y);
                        line.setAttribute('x2', p2.x);
                        line.setAttribute('y2', p2.y);
                        
                        // Fade based on distance
                        const opacity = (1 - distance / connectionDistance) * 0.3;
                        line.setAttribute('opacity', opacity);
                    }
                }
            });
        });
    }
    
    destroy() {
        // Cleanup
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.socket) {
            this.socket.off('user_connected');
            this.socket.off('user_disconnected');
        }
        
        this.particles.forEach(p => {
            if (p.element) p.element.remove();
            if (p.tooltip) p.tooltip.remove();
        });
        
        if (this.svg) {
            this.svg.remove();
        }
    }
}

// Make available globally
window.CyberpunkPresence = CyberpunkPresence;
