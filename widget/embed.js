/**
 * Travel.ai Voice Widget - Embed Script
 * Add this single line to any website to enable the voice assistant
 */

(function() {
    'use strict';
    
    // Configuration
    const WIDGET_CONFIG = {
        widgetUrl: 'http://localhost:4000',
        version: '1.0.0'
    };

    // Prevent multiple initializations
    if (window.__MYTRIP_WIDGET_LOADED__) {
        console.warn('Travel.ai widget already loaded');
        return;
    }
    window.__MYTRIP_WIDGET_LOADED__ = true;

    // Load CSS
    function loadCSS(url) {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }

    // Load JavaScript
    function loadJS(url) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // Initialize widget
    async function initWidget() {
        try {
            console.log('🎙️ Loading Travel.ai Voice Widget...');

            // Load Vapi SDK first
            await loadJS('https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.0.2/dist/index.umd.js');
            console.log('✅ Vapi SDK loaded');

            // Load widget styles
            await loadCSS(`${WIDGET_CONFIG.widgetUrl}/src/styles/widget.css`);
            console.log('✅ Widget styles loaded');

            // Load widget script
            await loadJS(`${WIDGET_CONFIG.widgetUrl}/src/widget.js`);
            console.log('✅ Widget script loaded');

            console.log('🎉 Travel.ai Voice Widget ready!');
        } catch (error) {
            console.error('Failed to load Travel.ai widget:', error);
        }
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidget);
    } else {
        initWidget();
    }
})();
