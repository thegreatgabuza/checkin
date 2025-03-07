/**
 * Student Check-in System
 * Main JavaScript file
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add current year to footer if available
    const currentYearElement = document.querySelector('.current-year');
    if (currentYearElement) {
        currentYearElement.textContent = new Date().getFullYear();
    }
    
    // Handle the date in the footer
    const footerYear = document.querySelector('footer p');
    if (footerYear) {
        const yearText = footerYear.textContent;
        footerYear.textContent = yearText.replace('{{ now.year }}', new Date().getFullYear());
    }
    
    // Add mobile navigation toggle if needed
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Add flash message auto-dismissal
    const flashMessages = document.querySelectorAll('.flash-message');
    
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.classList.add('fade-out');
                setTimeout(() => {
                    message.remove();
                }, 300);
            }, 5000);
        });
    }
    
    // RFID simulation for demonstration purposes
    const rfidSimulation = document.getElementById('rfid-simulation');
    if (rfidSimulation) {
        // Listen for keyboard events to simulate RFID card scan
        document.addEventListener('keypress', function(e) {
            // Simulate RFID card scan when 'R' key is pressed
            if (e.key.toLowerCase() === 'r') {
                simulateRFIDScan();
            }
        });
    }
    
    /**
     * Simulates an RFID card scan for demonstration purposes
     */
    function simulateRFIDScan() {
        const statusElement = document.getElementById('status-message');
        if (!statusElement) return;
        
        statusElement.textContent = "RFID Card detected! Processing...";
        statusElement.style.color = "#90caf9";
        
        setTimeout(() => {
            // Simulate successful authentication
            statusElement.textContent = "Authentication successful! Welcome, Student #12345";
            statusElement.style.color = "#a5d6a7";
            
            // Redirect to a success page or dashboard after a delay
            setTimeout(() => {
                window.location.href = "/dashboard?auth=rfid&id=12345";
            }, 2000);
        }, 1500);
    }
    
    /**
     * Function to handle form validation
     * @param {HTMLFormElement} form - The form to validate
     * @returns {boolean} - Whether the form is valid
     */
    function validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('error');
                
                // Create error message if it doesn't exist
                let errorMessage = input.nextElementSibling;
                if (!errorMessage || !errorMessage.classList.contains('error-message')) {
                    errorMessage = document.createElement('div');
                    errorMessage.className = 'error-message';
                    errorMessage.textContent = 'This field is required';
                    input.parentNode.insertBefore(errorMessage, input.nextSibling);
                }
            } else {
                input.classList.remove('error');
                
                // Remove error message if it exists
                const errorMessage = input.nextElementSibling;
                if (errorMessage && errorMessage.classList.contains('error-message')) {
                    errorMessage.remove();
                }
            }
        });
        
        return isValid;
    }
    
    // Add validation to forms with the 'validate' class
    const formsToValidate = document.querySelectorAll('form.validate');
    
    formsToValidate.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
});

// Firebase initialization (if directly needed in frontend)
function initFirebase() {
    // This function would initialize Firebase client if needed
    // Note: Most Firebase operations should be done server-side for security
    console.log('Firebase initialized in the frontend (for demonstration only)');
}

// LandingAI integration helpers
const LandingAI = {
    // These functions would interact with your backend which in turn would call LandingAI APIs
    uploadImage: async function(imageData, userId) {
        try {
            const response = await fetch('/api/landing-ai/train', {
                method: 'POST',
                body: imageData
            });
            return await response.json();
        } catch (error) {
            console.error('Error uploading to LandingAI:', error);
            throw error;
        }
    },
    
    predict: async function(imageData) {
        try {
            const response = await fetch('/api/landing-ai/predict', {
                method: 'POST',
                body: imageData
            });
            return await response.json();
        } catch (error) {
            console.error('Error getting prediction from LandingAI:', error);
            throw error;
        }
    }
}; 