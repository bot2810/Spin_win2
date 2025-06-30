
// Ad management and adblock detection
class AdManager {
constructor() {
this.adBlockDetected = false;
this.init();
}

init() {  
    this.detectAdBlock();  
    this.setupAdClickHandlers();  
    this.preventAutoClick();  
}  

detectAdBlock() {  
    // Create a test ad element  
    const testAd = document.createElement('div');  
    testAd.innerHTML = '&nbsp;';  
    testAd.className = 'adsbox';  
    testAd.style.position = 'absolute';  
    testAd.style.left = '-9999px';  
    document.body.appendChild(testAd);  

    // Check if ad blocker is active  
    setTimeout(() => {  
        if (testAd.offsetHeight === 0) {  
            this.adBlockDetected = true;  
            this.showAdBlockWarning();  
        }  
        document.body.removeChild(testAd);  
    }, 100);  

    // Additional detection methods  
    this.detectByRequest();  
}  

detectByRequest() {  
    // Try to load a common ad script  
    const script = document.createElement('script');  
    script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';  
    script.onerror = () => {  
        this.adBlockDetected = true;  
        this.showAdBlockWarning();  
    };  
    document.head.appendChild(script);  
}  

showAdBlockWarning() {  
    const warning = document.createElement('div');  
    warning.style.cssText = `  
        position: fixed;  
        top: 0;  
        left: 0;  
        width: 100%;  
        height: 100%;  
        background: rgba(0,0,0,0.9);  
        color: white;  
        display: flex;  
        align-items: center;  
        justify-content: center;  
        z-index: 10000;  
        font-family: Arial, sans-serif;  
        text-align: center;  
    `;  
    warning.innerHTML = `  
        <div>  
            <h2>🚫 AdBlock Detected!</h2>  
            <p>Please disable your ad blocker to continue playing.</p>  
            <p>Ads help us provide this free service.</p>  
            <button onclick="location.reload()" style="  
                background: #ff6b6b;  
                color: white;  
                border: none;  
                padding: 10px 20px;  
                border-radius: 5px;  
                cursor: pointer;  
                margin-top: 20px;  
            ">Reload Page</button>  
        </div>  
    `;  
    document.body.appendChild(warning);  
}  

setupAdClickHandlers() {  
    // Top ad click handler  
    document.getElementById('topAd').addEventListener('click', () => {  
        this.simulateAdClick('top');  
    });  

    // Bottom ad click handler  
    document.getElementById('bottomAd').addEventListener('click', () => {  
        this.simulateAdClick('bottom');  
    });  

    // Left sidebar ad click handler  
    document.getElementById('leftAd').addEventListener('click', () => {  
        this.simulateAdClick('left');  
    });  

    // Right sidebar ad click handler  
    document.getElementById('rightAd').addEventListener('click', () => {  
        this.simulateAdClick('right');  
    });  
}  

simulateAdClick(position) {  
    // Simulate ad click behavior  
    console.log(`Ad clicked: ${position}`);  

    // Add visual feedback  
    const ad = document.getElementById(`${position}Ad`);  
    const originalTransform = ad.style.transform;  
    ad.style.transform = 'scale(0.95)';  

    setTimeout(() => {  
        ad.style.transform = originalTransform;  
    }, 150);  

    // Track ad clicks (could send to analytics)  
    this.trackAdClick(position);  
}  

trackAdClick(position) {  
    // Send ad click data to backend  
    fetch('/track-ad-click', {  
        method: 'POST',  
        headers: {  
            'Content-Type': 'application/json',  
        },  
        body: JSON.stringify({  
            position: position,  
            timestamp: new Date().toISOString()  
        })  
    }).catch(error => {  
        console.log('Ad tracking failed:', error);  
    });  
}  

preventAutoClick() {  
    let clickCount = 0;  
    let lastClickTime = 0;  

    // Monitor click patterns  
    document.addEventListener('click', (event) => {  
        const currentTime = Date.now();  
        const timeDiff = currentTime - lastClickTime;  

        if (timeDiff < 100) { // Too fast clicking  
            clickCount++;  
            if (clickCount > 5) {  
                this.showBotWarning();  
                event.preventDefault();  
                event.stopPropagation();  
                return false;  
            }  
        } else {  
            clickCount = 0;  
        }  

        lastClickTime = currentTime;  
    });  

    // Detect automation tools  
    this.detectAutomation();  
}  

detectAutomation() {  
    // Check for common automation indicators  
    if (navigator.webdriver) {  
        this.showBotWarning();  
        return;  
    }  

    // Check for headless browsers  
    if (window.navigator.languages === undefined) {  
        this.showBotWarning();  
        return;  
    }  

    // Check for phantom.js  
    if (window.callPhantom || window._phantom) {  
        this.showBotWarning();  
        return;  
    }  

    // Mouse movement detection  
    let mouseEvents = 0;  
    document.addEventListener('mousemove', () => {  
        mouseEvents++;  
    });  

    // Check if user has natural mouse movement after 10 seconds  
    setTimeout(() => {  
        if (mouseEvents < 5) {  
            console.warn('Suspicious: Low mouse activity detected');  
        }  
    }, 10000);  
}  

showBotWarning() {  
    const warning = document.createElement('div');  
    warning.style.cssText = `  
        position: fixed;  
        top: 0;  
        left: 0;  
        width: 100%;  
        height: 100%;  
        background: rgba(255,0,0,0.9);  
        color: white;  
        display: flex;  
        align-items: center;  
        justify-content: center;  
        z-index: 10000;  
        font-family: Arial, sans-serif;  
        text-align: center;  
    `;  
    warning.innerHTML = `  
        <div>  
            <h2>🤖 Bot/Automation Detected!</h2>  
            <p>Please use the site manually without automation tools.</p>  
            <p>Your account may be suspended for automated usage.</p>  
        </div>  
    `;  
    document.body.appendChild(warning);  

    // Disable all interactions  
    document.body.style.pointerEvents = 'none';  
}  

// Check if ads are properly loaded  
checkAdLoad() {  
    const ads = [  
        document.getElementById('topAd'),  
        document.getElementById('bottomAd'),  
        document.getElementById('leftAd'),  
        document.getElementById('rightAd')  
    ];  

    ads.forEach((ad, index) => {  
        if (!ad || ad.offsetHeight === 0) {  
            console.warn(`Ad ${index} failed to load properly`);  
        }  
    });  
}

}

// Initialize ad manager
document.addEventListener('DOMContentLoaded', () => {
const adManager = new AdManager();

// Check ad load after page is fully loaded  
window.addEventListener('load', () => {  
    setTimeout(() => {  
        adManager.checkAdLoad();  
    }, 1000);  
});

});

// DNS/Proxy detection
function detectProxy() {
// Check for common proxy headers in a real implementation
// This would require server-side detection
const suspiciousUAs = [
'bot', 'crawler', 'spider', 'scraper', 'automation'
];

const userAgent = navigator.userAgent.toLowerCase();  

for (const suspicious of suspiciousUAs) {  
    if (userAgent.includes(suspicious)) {  
        console.warn('Suspicious user agent detected');  
        return true;  
    }  
}  

return false;

}

// Initialize proxy detection
if (detectProxy()) {
console.warn('Proxy/Bot detected');
}

// Real-time ad monitoring
setInterval(() => {
const adElements = document.querySelectorAll('.ad-banner, .ad-sidebar');
let visibleAds = 0;

adElements.forEach(ad => {  
    if (ad.offsetHeight > 0 && ad.offsetWidth > 0) {  
        visibleAds++;  
    }  
});  

if (visibleAds < 4) {  
    console.warn('Some ads are not visible - possible ad blocking');  
}

}, 5000);
