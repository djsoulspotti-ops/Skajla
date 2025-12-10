/**
 * SKAJLA Vertical Feed Component
 * TikTok-style vertical scrolling feed with swipeable cards
 * Part of Feature #2: Gen-Z Mobile-First UX
 */

class VerticalFeed {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        this.options = {
            cardHeight: options.cardHeight || '85vh',
            gap: options.gap || '1rem',
            enableInfiniteScroll: options.enableInfiniteScroll !== false,
            enablePullToRefresh: options.enablePullToRefresh !== false,
            onCardView: options.onCardView || null,
            onLoadMore: options.onLoadMore || null,
            onRefresh: options.onRefresh || null,
            ...options
        };

        this.currentCardIndex = 0;
        this.isLoading = false;
        this.cards = [];

        this.init();
    }

    init() {
        this.container.classList.add('vertical-feed');
        this.container.style.setProperty('--feed-card-height', this.options.cardHeight);
        this.container.style.setProperty('--feed-gap', this.options.gap);

        this.setupScrollObserver();
        
        if (this.options.enableInfiniteScroll) {
            this.setupInfiniteScroll();
        }

        if (this.options.enablePullToRefresh) {
            this.setupPullToRefresh();
        }

        if ('IntersectionObserver' in window) {
            this.setupCardViewTracking();
        }

        this.addTouchGestures();
    }

    setupScrollObserver() {
        let scrollTimeout;
        this.container.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.updateCurrentCard();
            }, 100);
        });
    }

    updateCurrentCard() {
        const cards = this.container.querySelectorAll('.feed-card');
        const containerRect = this.container.getBoundingClientRect();
        const centerY = containerRect.top + containerRect.height / 2;

        let closestCard = null;
        let closestDistance = Infinity;

        cards.forEach((card, index) => {
            const cardRect = card.getBoundingClientRect();
            const cardCenterY = cardRect.top + cardRect.height / 2;
            const distance = Math.abs(centerY - cardCenterY);

            if (distance < closestDistance) {
                closestDistance = distance;
                closestCard = { element: card, index };
            }
        });

        if (closestCard && closestCard.index !== this.currentCardIndex) {
            this.currentCardIndex = closestCard.index;
            
            if (this.options.onCardView) {
                this.options.onCardView(closestCard.element, closestCard.index);
            }
        }
    }

    setupInfiniteScroll() {
        const loader = document.createElement('div');
        loader.className = 'infinite-scroll-loader';
        loader.innerHTML = '<div class="infinite-scroll-spinner"></div>';
        loader.style.display = 'none';
        this.container.appendChild(loader);

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.isLoading) {
                    this.loadMore();
                }
            });
        }, {
            root: this.container,
            rootMargin: '200px'
        });

        observer.observe(loader);
        this.infiniteScrollLoader = loader;
    }

    async loadMore() {
        if (!this.options.onLoadMore || this.isLoading) return;

        this.isLoading = true;
        this.infiniteScrollLoader.style.display = 'flex';

        try {
            await this.options.onLoadMore();
        } catch (error) {
            console.error('Error loading more content:', error);
        } finally {
            this.isLoading = false;
            this.infiniteScrollLoader.style.display = 'none';
        }
    }

    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let isPulling = false;

        const pullIndicator = document.createElement('div');
        pullIndicator.className = 'pull-to-refresh';
        pullIndicator.innerHTML = '<div class="pull-to-refresh-spinner"></div>';
        this.container.insertBefore(pullIndicator, this.container.firstChild);

        this.container.addEventListener('touchstart', (e) => {
            if (this.container.scrollTop === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        }, { passive: true });

        this.container.addEventListener('touchmove', (e) => {
            if (!isPulling) return;

            currentY = e.touches[0].clientY;
            const pullDistance = currentY - startY;

            if (pullDistance > 0 && pullDistance < 120) {
                pullIndicator.style.transform = `translateX(-50%) translateY(${pullDistance - 100}%)`;
                if (pullDistance > 60) {
                    pullIndicator.classList.add('pulling');
                }
            }
        }, { passive: true });

        this.container.addEventListener('touchend', async () => {
            if (!isPulling) return;

            const pullDistance = currentY - startY;

            if (pullDistance > 80) {
                pullIndicator.style.transform = 'translateX(-50%) translateY(0)';
                
                if (this.options.onRefresh) {
                    try {
                        await this.options.onRefresh();
                    } catch (error) {
                        console.error('Error refreshing:', error);
                    }
                }

                setTimeout(() => {
                    pullIndicator.style.transform = 'translateX(-50%) translateY(-100%)';
                    pullIndicator.classList.remove('pulling');
                }, 1000);
            } else {
                pullIndicator.style.transform = 'translateX(-50%) translateY(-100%)';
                pullIndicator.classList.remove('pulling');
            }

            isPulling = false;
            startY = 0;
            currentY = 0;
        }, { passive: true });
    }

    setupCardViewTracking() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    
                    const cardIndex = Array.from(entry.target.parentNode.children).indexOf(entry.target);
                    if (window.telemetryTracker) {
                        window.telemetryTracker.trackEvent('feed_card_view', {
                            card_index: cardIndex,
                            card_type: entry.target.dataset.cardType || 'unknown'
                        });
                    }
                } else {
                    entry.target.classList.remove('in-view');
                }
            });
        }, {
            root: this.container,
            threshold: 0.5
        });

        this.container.querySelectorAll('.feed-card').forEach(card => {
            observer.observe(card);
        });

        this.cardObserver = observer;
    }

    addTouchGestures() {
        this.container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        this.container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    }

    handleTouchStart(e) {
        const touch = e.touches[0];
        this.touchStartX = touch.clientX;
        this.touchStartY = touch.clientY;
        this.touchStartTime = Date.now();
    }

    handleTouchMove(e) {
        if (!this.touchStartX || !this.touchStartY) return;

        const touch = e.touches[0];
        const deltaX = touch.clientX - this.touchStartX;
        const deltaY = touch.clientY - this.touchStartY;

        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
            e.preventDefault();
        }
    }

    handleTouchEnd(e) {
        if (!this.touchStartX || !this.touchStartY) return;

        const touch = e.changedTouches[0];
        const deltaX = touch.clientX - this.touchStartX;
        const deltaY = touch.clientY - this.touchStartY;
        const deltaTime = Date.now() - this.touchStartTime;

        const isSwipe = deltaTime < 300 && Math.abs(deltaX) > 50 && Math.abs(deltaY) < 50;

        if (isSwipe) {
            if (deltaX > 0) {
                this.onSwipeRight();
            } else {
                this.onSwipeLeft();
            }
        }

        this.touchStartX = null;
        this.touchStartY = null;
        this.touchStartTime = null;
    }

    onSwipeRight() {
        if (window.telemetryTracker) {
            window.telemetryTracker.trackEvent('feed_swipe_right', {
                card_index: this.currentCardIndex
            });
        }
    }

    onSwipeLeft() {
        if (window.telemetryTracker) {
            window.telemetryTracker.trackEvent('feed_swipe_left', {
                card_index: this.currentCardIndex
            });
        }
    }

    addCard(cardHTML) {
        const card = document.createElement('div');
        card.className = 'feed-card';
        card.innerHTML = cardHTML;
        
        if (this.infiniteScrollLoader) {
            this.container.insertBefore(card, this.infiniteScrollLoader);
        } else {
            this.container.appendChild(card);
        }

        if (this.cardObserver) {
            this.cardObserver.observe(card);
        }

        return card;
    }

    prependCard(cardHTML) {
        const card = document.createElement('div');
        card.className = 'feed-card';
        card.innerHTML = cardHTML;
        this.container.insertBefore(card, this.container.firstChild);

        if (this.cardObserver) {
            this.cardObserver.observe(card);
        }

        return card;
    }

    removeCard(index) {
        const cards = this.container.querySelectorAll('.feed-card');
        if (cards[index]) {
            cards[index].remove();
        }
    }

    scrollToCard(index) {
        const cards = this.container.querySelectorAll('.feed-card');
        if (cards[index]) {
            cards[index].scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    clear() {
        const cards = this.container.querySelectorAll('.feed-card');
        cards.forEach(card => card.remove());
        this.currentCardIndex = 0;
    }

    destroy() {
        if (this.cardObserver) {
            this.cardObserver.disconnect();
        }
        this.container.innerHTML = '';
        this.container.classList.remove('vertical-feed');
    }
}

class SwipeableCard {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            onSwipeLeft: options.onSwipeLeft || null,
            onSwipeRight: options.onSwipeRight || null,
            threshold: options.threshold || 100,
            ...options
        };

        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.isDragging = false;

        this.init();
    }

    init() {
        this.element.classList.add('swipeable-card');
        
        this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        this.element.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.element.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });

        this.element.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.element.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.element.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.element.addEventListener('mouseleave', this.handleMouseUp.bind(this));
    }

    handleTouchStart(e) {
        const touch = e.touches[0];
        this.startDrag(touch.clientX, touch.clientY);
    }

    handleTouchMove(e) {
        if (!this.isDragging) return;
        
        const touch = e.touches[0];
        this.updateDrag(touch.clientX, touch.clientY);
        e.preventDefault();
    }

    handleTouchEnd() {
        this.endDrag();
    }

    handleMouseDown(e) {
        this.startDrag(e.clientX, e.clientY);
    }

    handleMouseMove(e) {
        if (!this.isDragging) return;
        this.updateDrag(e.clientX, e.clientY);
    }

    handleMouseUp() {
        this.endDrag();
    }

    startDrag(x, y) {
        this.startX = x;
        this.startY = y;
        this.isDragging = true;
        this.element.classList.add('swiping');
    }

    updateDrag(x, y) {
        this.currentX = x;
        this.currentY = y;

        const deltaX = this.currentX - this.startX;
        const deltaY = this.currentY - this.startY;

        const rotation = deltaX * 0.1;
        
        this.element.style.transform = `translateX(${deltaX}px) rotate(${rotation}deg)`;
        this.element.style.opacity = 1 - Math.abs(deltaX) / 500;

        if (deltaX < -50) {
            this.element.classList.add('show-left-indicator');
            this.element.classList.remove('show-right-indicator');
        } else if (deltaX > 50) {
            this.element.classList.add('show-right-indicator');
            this.element.classList.remove('show-left-indicator');
        } else {
            this.element.classList.remove('show-left-indicator', 'show-right-indicator');
        }
    }

    endDrag() {
        if (!this.isDragging) return;

        const deltaX = this.currentX - this.startX;

        if (Math.abs(deltaX) > this.options.threshold) {
            if (deltaX < 0) {
                this.swipeLeft();
            } else {
                this.swipeRight();
            }
        } else {
            this.reset();
        }

        this.isDragging = false;
        this.element.classList.remove('swiping', 'show-left-indicator', 'show-right-indicator');
    }

    swipeLeft() {
        this.element.classList.add('swiped-left');
        
        if (this.options.onSwipeLeft) {
            this.options.onSwipeLeft(this.element);
        }

        setTimeout(() => {
            this.element.remove();
        }, 300);
    }

    swipeRight() {
        this.element.classList.add('swiped-right');
        
        if (this.options.onSwipeRight) {
            this.options.onSwipeRight(this.element);
        }

        setTimeout(() => {
            this.element.remove();
        }, 300);
    }

    reset() {
        this.element.style.transform = '';
        this.element.style.opacity = '';
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VerticalFeed, SwipeableCard };
}
