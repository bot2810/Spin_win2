document.addEventListener('DOMContent', function() {
    // Check if we're on login page
    if (document.getElementById('login-form')) {
        const loginForm = document.getElementById('login-form');
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const userId = document.getElementById('user-id').value;
            
            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `user_id=${userId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = '/';
                }
            });
        });
        return;
    }

    // Main game logic
    const wheel = document.getElementById('wheel');
    const spinBtn = document.getElementById('spin-btn');
    const resultMessage = document.getElementById('result-message');
    const spinCountElement = document.getElementById('spin-count');
    const totalEarnedElement = document.getElementById('total-earned');
    const scratchContainer = document.getElementById('scratch-container');
    const scratchCard = document.getElementById('scratch-card');
    const scratchArea = document.getElementById('scratch-area');
    const scratchPrize = document.getElementById('scratch-prize');
    const scratchBtn = document.getElementById('scratch-btn');
    const spinSound = document.getElementById('spin-sound');
    const winSound = document.getElementById('win-sound');
    const scratchSound = document.getElementById('scratch-sound');
    
    let isSpinning = false;
    let spinCount = 0;
    let totalEarned = 0;
    let lastSpinDate = new Date().toISOString().split('T')[0];
    
    // Check for ad blocker
    let adBlockDetected = false;
    
    // Initialize game state
    function initGameState() {
        fetch('/check-state')
            .then(response => response.json())
            .then(data => {
                spinCount = data.spin_count || 0;
                totalEarned = data.total_earned || 0;
                lastSpinDate = data.last_spin_date || new Date().toISOString().split('T')[0];
                
                spinCountElement.textContent = spinCount;
                totalEarnedElement.textContent = totalEarned.toFixed(2);
                
                if (spinCount >= 15 && !data.scratch_used) {
                    scratchContainer.classList.remove('hidden');
                }
            });
    }
    
    initGameState();
    
    // Spin wheel function
    function spinWheel() {
        if (isSpinning) return;
        
        // Check for ad blocker
        if (adBlockDetected) {
            resultMessage.textContent = "Please disable ad blocker to spin!";
            return;
        }
        
        isSpinning = true;
        spinBtn.disabled = true;
        
        // Play spin sound
        spinSound.currentTime = 0;
        spinSound.play();
        
        // Random rotation (3-5 full rotations plus segment offset)
        const segmentAngle = 120; // 3 segments
        const extraRotations = 3 + Math.floor(Math.random() * 3);
        const randomSegment = Math.floor(Math.random() * 3);
        const targetAngle = (extraRotations * 360) + (randomSegment * segmentAngle) + (Math.random() * segmentAngle * 0.5);
        
        wheel.style.transform = `rotate(${-targetAngle}deg)`;
        
        // Send spin request to server after animation starts
        setTimeout(() => {
            fetch('/spin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ad_blocked: adBlockDetected
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ad_blocked') {
                    resultMessage.textContent = "Ad blocker detected! Please disable to earn rewards.";
                    resetWheel();
                    return;
                }
                
                if (data.status === 'limit_reached') {
                    resultMessage.textContent = "You've reached your daily spin limit!";
                    if (!scratchContainer.classList.contains('hidden')) {
                        scratchContainer.classList.remove('hidden');
                    }
                    resetWheel();
                    return;
                }
                
                // Update UI after animation completes
                setTimeout(() => {
                    isSpinning = false;
                    spinBtn.disabled = false;
                    
                    // Play win sound
                    winSound.currentTime = 0;
                    winSound.play();
                    
                    // Update spin count and total
                    spinCount = data.spin_count;
                    totalEarned = data.total_earned;
                    
                    spinCountElement.textContent = spinCount;
                    totalEarnedElement.textContent = totalEarned.toFixed(2);
                    
                    resultMessage.textContent = `You won ₹${data.reward.toFixed(2)}!`;
                    
                    // Show scratch card if reached limit
                    if (spinCount >= 15) {
                        scratchContainer.classList.remove('hidden');
                    }
                }, 4000);
            });
        }, 100);
    }
    
    function resetWheel() {
        setTimeout(() => {
            wheel.style.transition = 'none';
            wheel.style.transform = 'rotate(0deg)';
            setTimeout(() => {
                wheel.style.transition = 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)';
                isSpinning = false;
                spinBtn.disabled = false;
            }, 10);
        }, 4000);
    }
    
    // Scratch card functionality
    let isScratching = false;
    let canvas;
    let ctx;
    
    function initScratchCard() {
        // Create canvas for scratch effect
        canvas = document.createElement('canvas');
        canvas.width = scratchCard.offsetWidth;
        canvas.height = scratchCard.offsetHeight;
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'none';
        
        scratchArea.innerHTML = '';
        scratchArea.appendChild(canvas);
        
        ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ddd';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.globalCompositeOperation = 'destination-out';
        
        // Add event listeners for scratching
        scratchArea.addEventListener('mousedown', startScratching);
        scratchArea.addEventListener('touchstart', startScratching);
        scratchArea.addEventListener('mousemove', scratch);
        scratchArea.addEventListener('touchmove', scratch);
        scratchArea.addEventListener('mouseup', endScratching);
        scratchArea.addEventListener('touchend', endScratching);
        scratchArea.addEventListener('mouseleave', endScratching);
    }
    
    function startScratching(e) {
        isScratching = true;
        scratchSound.currentTime = 0;
        scratchSound.play();
        scratch(e);
    }
    
    function scratch(e) {
        if (!isScratching) return;
        
        const rect = scratchArea.getBoundingClientRect();
        let x, y;
        
        if (e.type.includes('touch')) {
            x = e.touches[0].clientX - rect.left;
            y = e.touches[0].clientY - rect.top;
        } else {
            x = e.clientX - rect.left;
            y = e.clientY - rect.top;
        }
        
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, Math.PI * 2);
        ctx.fill();
        
        // Check if enough has been scratched to reveal prize
        checkScratchProgress();
    }
    
    function endScratching() {
        isScratching = false;
    }
    
    function checkScratchProgress() {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        let transparentPixels = 0;
        
        for (let i = 3; i < pixels.length; i += 4) {
            if (pixels[i] === 0) {
                transparentPixels++;
            }
        }
        
        const percentScratched = (transparentPixels / (pixels.length / 4)) * 100;
        
        if (percentScratched > 30) {
            revealPrize();
        }
    }
    
    function revealPrize() {
        // Disable scratching
        isScratching = false;
        scratchArea.style.pointerEvents = 'none';
        
        // Get prize from server
        fetch('/scratch', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                scratchPrize.textContent = `₹${data.reward.toFixed(2)}`;
                scratchPrize.classList.remove('hidden');
                
                // Update total earned
                totalEarned += data.reward;
                totalEarnedElement.textContent = totalEarned.toFixed(2);
            }
        });
    }
    
    // Initialize scratch card when shown
    if (scratchContainer) {
        scratchContainer.addEventListener('DOMNodeInserted', initScratchCard);
    }
    
    // Event listeners
    if (spinBtn) {
        spinBtn.addEventListener('click', spinWheel);
    }
    
    if (scratchBtn) {
        scratchBtn.addEventListener('click', initScratchCard);
    }
    
    // Ad block detection
    function checkAdBlock() {
        // Simple detection - try to load an ad script
        const fakeAd = document.createElement('div');
        fakeAd.className = 'ad ads advertisement adsbox doubleclick ad-placement';
        fakeAd.style.height = '1px';
        document.body.appendChild(fakeAd);
        
        setTimeout(() => {
            const styles = window.getComputedStyle(fakeAd);
            adBlockDetected = styles.display === 'none' || 
                             styles.visibility === 'hidden' || 
                             styles.height === '0px';
            
            if (adBlockDetected) {
                console.log('Ad blocker detected');
                document.querySelectorAll('.ad').forEach(ad => {
                    ad.innerHTML = '<p>Please disable ad blocker to earn rewards</p>';
                });
            }
            
            document.body.removeChild(fakeAd);
        }, 100);
    }
    
    // Run ad block check on load
    window.addEventListener('load', checkAdBlock);
});
