/**
 * Vapi SDK Loader - Official CDN
 * Loads the Vapi SDK from official CDN and makes it globally available
 */

console.log('📦 Loading Vapi SDK from official CDN...');

// Load Vapi SDK from official CDN (recommended by Vapi)
(function() {
    const script = document.createElement('script');
    
    // Official Vapi SDK URL
    script.src = 'https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js';
    script.async = true;
    script.defer = true;
    
    script.onload = () => {
        console.log('✅ Vapi SDK loaded successfully from official CDN');
        
        // Check if vapiSDK is available globally
        if (typeof window.vapiSDK !== 'undefined') {
            console.log('✅ vapiSDK is available globally');
            window.dispatchEvent(new CustomEvent('vapiSDKReady'));
        } else {
            console.warn('⚠️ Vapi SDK loaded but vapiSDK not found - retrying...');
            setTimeout(() => {
                if (typeof window.vapiSDK !== 'undefined') {
                    console.log('✅ vapiSDK is now available');
                    window.dispatchEvent(new CustomEvent('vapiSDKReady'));
                } else {
                    console.error('❌ vapiSDK still not available after delay');
                    window.dispatchEvent(new CustomEvent('vapiSDKLoadFailed'));
                }
            }, 1000);
        }
    };
    
    script.onerror = () => {
        console.error('❌ Failed to load Vapi SDK from official CDN');
        window.dispatchEvent(new CustomEvent('vapiSDKLoadFailed'));
    };
    
    document.head.appendChild(script);
})();

export default { loaded: true };
