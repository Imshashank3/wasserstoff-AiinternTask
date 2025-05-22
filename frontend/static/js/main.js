// Main JavaScript for Document Research & Theme Identification Chatbot

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabs = {
        'documents': document.getElementById('documents-view'),
        'query': document.getElementById('query-view'),
        'themes': document.getElementById('themes-view'),
        'settings': document.getElementById('settings-view')
    };
    
    const tabButtons = {
        'documents': document.getElementById('tab-documents'),
        'query': document.getElementById('tab-query'),
        'themes': document.getElementById('tab-themes'),
        'settings': document.getElementById('tab-settings')
    };
    
    const navButtons = {
        'documents': document.getElementById('btn-documents'),
        'query': document.getElementById('btn-query'),
        'themes': document.getElementById('btn-themes'),
        'settings': document.getElementById('btn-settings')
    };
    
    function switchTab(tabName) {
        // Hide all tabs
        Object.values(tabs).forEach(tab => {
            if (tab) tab.classList.add('hidden');
        });
        
        // Remove active class from all tab buttons
        Object.values(tabButtons).forEach(button => {
            if (button) button.classList.remove('tab-active');
            if (button) button.classList.add('text-gray-500');
            if (button) button.classList.remove('text-gray-800');
        });
        
        // Show selected tab and activate button
        if (tabs[tabName]) {
            tabs[tabName].classList.remove('hidden');
        }
        
        if (tabButtons[tabName]) {
            tabButtons[tabName].classList.add('tab-active');
            tabButtons[tabName].classList.remove('text-gray-500');
            tabButtons[tabName].classList.add('text-gray-800');
        }
    }
    
    // Add click event listeners to tab buttons
    Object.entries(tabButtons).forEach(([name, button]) => {
        if (button) {
            button.addEventListener('click', () => switchTab(name));
        }
    });
    
    // Add click event listeners to nav buttons
    Object.entries(navButtons).forEach(([name, button]) => {
        if (button) {
            button.addEventListener('click', () => switchTab(name));
        }
    });
    
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Document selection functionality
    const documentCards = document.querySelectorAll('.document-card');
    documentCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Prevent triggering when clicking buttons inside the card
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
            
            // Toggle selected state
            this.classList.toggle('document-selected');
            
            // Update selection count
            updateSelectionCount();
        });
    });

    function updateSelectionCount() {
        const selectedCount = document.querySelectorAll('.document-selected').length;
        const selectionCounter = document.getElementById('selection-counter');
        if (selectionCounter) {
            selectionCounter.textContent = selectedCount;
            selectionCounter.parentElement.classList.toggle('hidden', selectedCount === 0);
        }
    }

    // Simulate query submission
    const queryForm = document.getElementById('query-form');
    if (queryForm) {
        queryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const resultsContainer = document.getElementById('query-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = `
                    <div class="flex justify-center items-center p-12">
                        <div class="loading-spinner"></div>
                        <p class="ml-4 text-gray-600">Processing query...</p>
                    </div>
                `;
            }
            
            // Simulate API call delay
            setTimeout(() => {
                // Switch to results view
                if (resultsContainer) {
                    resultsContainer.classList.remove('hidden');
                    // Results would be populated here in a real implementation
                }
            }, 1500);
        });
    }

    // Theme visualization placeholder
    const themeVisualization = document.querySelector('.theme-visualization');
    if (themeVisualization) {
        // In a real implementation, this would initialize a visualization library
        // like D3.js or Chart.js to render the theme network
    }

    // Citation highlighting
    const citationBadges = document.querySelectorAll('.citation-badge');
    citationBadges.forEach(badge => {
        badge.addEventListener('click', function() {
            // In a real implementation, this would highlight the cited text
            // or open a modal with the citation context
            alert('Citation details would be shown here');
        });
    });

    // Document upload simulation
    const uploadButton = document.querySelector('button:has(i.fa-upload)');
    if (uploadButton) {
        uploadButton.addEventListener('click', function() {
            // In a real implementation, this would open a file picker
            // and handle the upload process
            alert('Document upload functionality would be triggered here');
        });
    }

    // Filter reset functionality
    const resetFiltersButton = document.querySelector('button:contains("Reset Filters")');
    if (resetFiltersButton) {
        resetFiltersButton.addEventListener('click', function() {
            // Reset all filter dropdowns to default values
            const filterSelects = document.querySelectorAll('.filter-bar select');
            filterSelects.forEach(select => {
                select.selectedIndex = 0;
            });
            
            // Clear tag input
            const tagInput = document.querySelector('.filter-bar input[type="text"]');
            if (tagInput) {
                tagInput.value = '';
            }
        });
    }
});
