// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('active');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.navbar')) {
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                }
            }
        });
    }

    // User dropdown on mobile
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        userDropdown.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                this.classList.toggle('active');
            }
        });
    }

    const loginDropdown = document.querySelector('.login-dropdown');
    if (loginDropdown) {
        const loginTrigger = loginDropdown.querySelector('.login-dropdown-trigger');
        const loginMenu = loginDropdown.querySelector('.login-dropdown-menu');

        if (loginTrigger && loginMenu) {
            loginTrigger.addEventListener('click', function() {
                const isOpen = loginDropdown.classList.toggle('active');
                loginMenu.classList.toggle('open', isOpen);
                loginTrigger.setAttribute('aria-expanded', String(isOpen));
            });

            document.addEventListener('click', function(e) {
                if (!loginDropdown.contains(e.target)) {
                    loginDropdown.classList.remove('active');
                    loginMenu.classList.remove('open');
                    loginTrigger.setAttribute('aria-expanded', 'false');
                }
            });

            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && loginDropdown.classList.contains('active')) {
                    loginDropdown.classList.remove('active');
                    loginMenu.classList.remove('open');
                    loginTrigger.setAttribute('aria-expanded', 'false');
                    loginTrigger.focus();
                }
            });
        }
    }

    // AJAX Search with suggestions
    const searchInput = document.getElementById('searchInput');
    const suggestionsDiv = document.getElementById('searchSuggestions');
    let searchTimeout;

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(function() {
                    fetchSearchResults(query);
                }, 300);
            } else {
                if (suggestionsDiv) {
                    suggestionsDiv.style.display = 'none';
                }
            }
        });

        // Close suggestions on outside click
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.hero-search')) {
                if (suggestionsDiv) {
                    suggestionsDiv.style.display = 'none';
                }
            }
        });
    }

    function fetchSearchResults(query) {
        fetch(`/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    let html = '';
                    data.results.forEach(product => {
                        html += `
                            <a href="/product/${product.slug}/" class="search-suggestion-item">
                                ${product.image ? `<img src="${product.image}" alt="${product.name}" class="suggestion-image">` : ''}
                                <div class="suggestion-info">
                                    <div class="suggestion-name">${product.name}</div>
                                    <div class="suggestion-price">
                                        $${product.price}
                                        ${product.discount > 0 ? `<span class="suggestion-discount">-${product.discount}%</span>` : ''}
                                    </div>
                                </div>
                            </a>
                        `;
                    });
                    suggestionsDiv.innerHTML = html;
                    suggestionsDiv.style.display = 'block';
                } else {
                    suggestionsDiv.innerHTML = `
                        <div class="search-suggestion-item" style="cursor: default;">
                            <span>No products found</span>
                        </div>
                    `;
                    suggestionsDiv.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Search error:', error);
            });
    }

    // Add to Cart buttons
    document.querySelectorAll('.btn-add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            // This will be handled by the form submit
            // But we can add a loading state
            const originalText = this.innerHTML;
            this.innerHTML = 'Adding...';
            this.disabled = true;
            
            // Reset after 2 seconds if not submitted
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 2000);
        });
    });

    // Auto-dismiss messages after 5 seconds
    document.querySelectorAll('.message').forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                msg.remove();
            }, 500);
        }, 5000);
    });

    // Image lazy loading
    if ('IntersectionObserver' in window) {
        const images = document.querySelectorAll('.product-image');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => {
            if (img.dataset.src) {
                imageObserver.observe(img);
            }
        });
    }

    // Quantity input validation
    document.querySelectorAll('.quantity-selector input').forEach(input => {
        input.addEventListener('change', function() {
            const max = parseInt(this.max) || 999;
            let value = parseInt(this.value) || 1;
            
            if (value < 1) {
                this.value = 1;
            } else if (value > max) {
                this.value = max;
                alert(`Only ${max} items available in stock.`);
            }
        });
    });

    // Update cart quantity hidden input
    const quantityInput = document.getElementById('quantity');
    const cartQuantity = document.getElementById('cartQuantity');
    
    if (quantityInput && cartQuantity) {
        quantityInput.addEventListener('change', function() {
            cartQuantity.value = this.value;
        });
    }

    // Product image gallery
    const mainImage = document.getElementById('mainProductImage');
    const thumbnails = document.querySelectorAll('.thumbnail');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const img = this.querySelector('img');
            if (img && mainImage) {
                mainImage.src = img.src;
                mainImage.alt = img.alt || 'Product image';
                
                // Remove active class from all thumbnails
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    // Add active class to first thumbnail
    if (thumbnails.length > 0) {
        thumbnails[0].classList.add('active');
    }
});

// Utility functions
function showLoginAlert() {
    alert('Please login to add items to cart or buy now.');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Scroll to top button
window.addEventListener('scroll', function() {
    const scrollBtn = document.getElementById('scrollTopBtn');
    if (scrollBtn) {
        if (window.scrollY > 300) {
            scrollBtn.style.display = 'block';
        } else {
            scrollBtn.style.display = 'none';
        }
    }
});
// Get CSRF token from cookie
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
