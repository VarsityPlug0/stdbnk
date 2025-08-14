// User Activity Tracking Library
// This library automatically tracks user interactions and sends them to the server

(function() {
    'use strict';
    
    // Configuration object for tracking settings
    const trackingConfig = {
        endpoint: '/api/track',  // API endpoint for sending tracking data
        trackPageViews: true,  // Whether to track page views
        trackButtonClicks: true,  // Whether to track button clicks
        trackFormSubmissions: true,  // Whether to track form submissions
        trackInputFocus: true,  // Whether to track input field focus events
        debounceTime: 300,  // Delay in milliseconds to prevent spam tracking
        maxRetries: 3,  // Maximum number of retry attempts for failed requests
        debug: false  // Enable debug logging
    };
    
    // Debounce function to limit the rate of function calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);  // Clear the timeout
                func(...args);  // Execute the function
            };
            clearTimeout(timeout);  // Clear any existing timeout
            timeout = setTimeout(later, wait);  // Set a new timeout
        };
    }
    
    // Function to log debug messages if debug mode is enabled
    function debugLog(message, data = null) {
        if (trackingConfig.debug) {
            console.log('[Tracking]', message, data);  // Log debug information
        }
    }
    
    // Function to send tracking data to the server
    function sendTrackingData(actionType, elementId = null, additionalData = null, retryCount = 0) {
        // Prepare tracking payload
        const trackingData = {
            action_type: actionType,  // Type of action being tracked
            page: window.location.pathname,  // Current page path
            element_id: elementId,  // ID of the element that was interacted with
            additional_data: additionalData ? JSON.stringify(additionalData) : null  // Extra data as JSON string
        };
        
        debugLog('Sending tracking data:', trackingData);
        
        // Send tracking data via fetch API
        fetch(trackingConfig.endpoint, {
            method: 'POST',  // Use POST method
            headers: {
                'Content-Type': 'application/json',  // Set content type to JSON
            },
            body: JSON.stringify(trackingData)  // Convert tracking data to JSON string
        })
        .then(response => {
            if (!response.ok) {  // Check if response is not successful
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            debugLog('Tracking data sent successfully');
            return response.json();  // Parse response as JSON
        })
        .catch(error => {
            debugLog('Error sending tracking data:', error);
            
            // Retry logic for failed requests
            if (retryCount < trackingConfig.maxRetries) {
                debugLog(`Retrying... (${retryCount + 1}/${trackingConfig.maxRetries})`);
                setTimeout(() => {
                    sendTrackingData(actionType, elementId, additionalData, retryCount + 1);
                }, 1000 * (retryCount + 1));  // Exponential backoff: 1s, 2s, 3s
            } else {
                console.warn('Failed to send tracking data after', trackingConfig.maxRetries, 'attempts:', error);
            }
        });
    }
    
    // Debounced version of sendTrackingData to prevent spam
    const debouncedSendTracking = debounce(sendTrackingData, trackingConfig.debounceTime);
    
    // Function to get unique identifier for an element
    function getElementIdentifier(element) {
        // Try to get ID first, then class, then tag name with index
        if (element.id) {
            return element.id;  // Use element ID if available
        }
        
        if (element.className) {
            return `${element.tagName.toLowerCase()}.${element.className.split(' ')[0]}`;  // Use tag + first class
        }
        
        // Use tag name with index as fallback
        const siblings = Array.from(element.parentNode?.children || []);
        const index = siblings.indexOf(element);
        return `${element.tagName.toLowerCase()}[${index}]`;  // Use tag name with index
    }
    
    // Function to track button clicks and other clickable elements
    function trackClick(event) {
        const element = event.target;  // Get the clicked element
        const elementId = getElementIdentifier(element);  // Get unique identifier
        const elementType = element.tagName.toLowerCase();  // Get element type
        
        // Additional data about the click
        const additionalData = {
            element_type: elementType,  // Type of element clicked
            element_text: element.textContent?.trim().substring(0, 100) || '',  // First 100 chars of text
            element_value: element.value || '',  // Value if it's an input
            timestamp: new Date().toISOString()  // Timestamp of the click
        };
        
        debugLog('Click tracked:', {
            elementId: elementId,
            elementType: elementType,
            text: additionalData.element_text
        });
        
        // Send tracking data for button click
        debouncedSendTracking('button_click', elementId, additionalData);
    }
    
    // Function to track form submissions
    function trackFormSubmission(event) {
        const form = event.target;  // Get the form element
        const formId = getElementIdentifier(form);  // Get unique identifier for form
        
        // Additional data about the form submission
        const additionalData = {
            form_method: form.method || 'GET',  // Form submission method
            form_action: form.action || window.location.href,  // Form action URL
            form_fields_count: form.elements.length,  // Number of form fields
            timestamp: new Date().toISOString()  // Timestamp of submission
        };
        
        debugLog('Form submission tracked:', {
            formId: formId,
            method: additionalData.form_method,
            fieldsCount: additionalData.form_fields_count
        });
        
        // Send tracking data for form submission
        sendTrackingData('form_submission', formId, additionalData);
    }
    
    // Function to track input field focus events
    function trackInputFocus(event) {
        const element = event.target;  // Get the focused element
        const elementId = getElementIdentifier(element);  // Get unique identifier
        
        // Only track actual input elements
        if (!['input', 'textarea', 'select'].includes(element.tagName.toLowerCase())) {
            return;  // Skip non-input elements
        }
        
        // Additional data about the input focus
        const additionalData = {
            input_type: element.type || 'text',  // Input type
            input_name: element.name || '',  // Input name attribute
            placeholder: element.placeholder || '',  // Placeholder text
            timestamp: new Date().toISOString()  // Timestamp of focus
        };
        
        debugLog('Input focus tracked:', {
            elementId: elementId,
            inputType: additionalData.input_type,
            inputName: additionalData.input_name
        });
        
        // Send tracking data for input focus
        debouncedSendTracking('input_focus', elementId, additionalData);
    }
    
    // Function to initialize tracking when DOM is ready
    function initializeTracking() {
        debugLog('Initializing user activity tracking');
        
        // Track page view when tracking is initialized
        if (trackingConfig.trackPageViews) {
            const additionalData = {
                referrer: document.referrer || '',  // Referring page
                user_agent: navigator.userAgent,  // Browser user agent
                screen_resolution: `${screen.width}x${screen.height}`,  // Screen resolution
                viewport_size: `${window.innerWidth}x${window.innerHeight}`,  // Viewport size
                timestamp: new Date().toISOString()  // Timestamp of page view
            };
            
            debugLog('Page view tracked:', {
                page: window.location.pathname,
                referrer: additionalData.referrer
            });
            
            sendTrackingData('page_view', null, additionalData);
        }
        
        // Set up click tracking for buttons and other clickable elements
        if (trackingConfig.trackButtonClicks) {
            document.addEventListener('click', function(event) {
                const element = event.target;
                
                // Track clicks on buttons, links, and elements with click handlers
                if (element.tagName === 'BUTTON' || 
                    element.tagName === 'A' || 
                    element.type === 'submit' ||
                    element.type === 'button' ||
                    element.onclick ||
                    element.getAttribute('onclick') ||
                    element.classList.contains('clickable')) {
                    
                    trackClick(event);  // Track the click event
                }
            }, true);  // Use capture phase to catch all clicks
        }
        
        // Set up form submission tracking
        if (trackingConfig.trackFormSubmissions) {
            document.addEventListener('submit', trackFormSubmission, true);
        }
        
        // Set up input focus tracking
        if (trackingConfig.trackInputFocus) {
            document.addEventListener('focus', trackInputFocus, true);
        }
        
        debugLog('Tracking initialized successfully');
    }
    
    // Function to update tracking configuration
    function updateConfig(newConfig) {
        Object.assign(trackingConfig, newConfig);  // Merge new config with existing
        debugLog('Tracking configuration updated:', trackingConfig);
    }
    
    // Expose public API for manual tracking and configuration
    window.UserTracking = {
        // Manual tracking functions
        track: sendTrackingData,  // Manual tracking function
        trackClick: trackClick,  // Manual click tracking
        trackFormSubmission: trackFormSubmission,  // Manual form submission tracking
        
        // Configuration functions
        config: updateConfig,  // Update configuration
        debug: (enabled) => { trackingConfig.debug = enabled; },  // Toggle debug mode
        
        // Status functions
        isEnabled: () => true,  // Check if tracking is enabled
        getConfig: () => ({ ...trackingConfig })  // Get current configuration (copy)
    };
    
    // Initialize tracking when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTracking);  // Wait for DOM to load
    } else {
        initializeTracking();  // DOM is already loaded, initialize immediately
    }
    
    debugLog('User tracking library loaded');
    
})();  // Immediately invoked function expression to create isolated scope
