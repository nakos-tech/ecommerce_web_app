/**
 * main.js — XypherLux
 * Handles: auth modals, cart modal, form validation, AJAX submissions.
 */

'use strict';

// ============================================================
// DOM REFERENCES
// ============================================================

const modals = {
    login:          document.getElementById('loginModal'),
    signup:         document.getElementById('signupModal'),
    generateCode:   document.getElementById('generateCodeModal'),
    verifyCode:     document.getElementById('verifyCodeModal'),
    setNewPassword: document.getElementById('setNewPasswordModal'),
    cart:           document.getElementById('cartModal'),
};

// ============================================================
// MODAL HELPERS
// ============================================================

function openModal(modal) {
    if (!modal) return;
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove('is-open');
    document.body.style.overflow = '';
}

function closeAllAuthModals() {
    ['login', 'signup', 'generateCode', 'verifyCode', 'setNewPassword'].forEach(key => {
        closeModal(modals[key]);
    });
    document.body.style.overflow = '';
}

function closeCartModal() {
    closeModal(modals.cart);
    document.body.style.overflow = '';
}

// Close modals on backdrop click
Object.values(modals).forEach(modal => {
    if (!modal) return;
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            if (modal === modals.cart) {
                closeCartModal();
            } else {
                closeAllAuthModals();
            }
        }
    });
});

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAllAuthModals();
        closeCartModal();
    }
});

// Close buttons with data-close-modal attribute
document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', closeAllAuthModals);
});

// ============================================================
// MODAL TRIGGER BINDINGS
// ============================================================

const bind = (id, fn) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', (e) => { e.preventDefault(); fn(); });
};

bind('showLogin',               () => { closeAllAuthModals(); openModal(modals.login); });
bind('showSignup',              () => { closeAllAuthModals(); openModal(modals.signup); });
bind('showLoginFromSignup',     () => { closeAllAuthModals(); openModal(modals.login); });
bind('forgotPasswordLink',      () => { closeAllAuthModals(); openModal(modals.generateCode); });
bind('showLoginFromGenerateCode', () => { closeAllAuthModals(); openModal(modals.login); });
bind('resendCode',              () => { closeAllAuthModals(); openModal(modals.generateCode); });
bind('openCartBtn',             () => { openModal(modals.cart); showCartView(); });

bind('accountBtn', () => {
    const btn = document.getElementById('accountBtn');
    if (btn.dataset.authenticated === 'true') {
        window.location.href = btn.dataset.profileUrl;
    } else {
        closeAllAuthModals();
        openModal(modals.login);
    }
})

// ============================================================
// UTILITY — FORM HELPERS
// ============================================================

function getCSRFToken() {
    const el = document.querySelector('[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
}

function showAlert(id, message, type = 'error') {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = message;
    el.className = `alert alert--${type} visible`;
}

function hideAlert(id) {
    const el = document.getElementById(id);
    if (el) { el.classList.remove('visible'); el.innerHTML = ''; }
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errEl = document.getElementById(fieldId + '_error');
    if (field) { field.classList.add('field-error'); field.classList.remove('field-success'); }
    if (errEl) { errEl.textContent = message; errEl.classList.add('visible'); }
}

function showFieldSuccess(fieldId) {
    const field = document.getElementById(fieldId);
    const errEl = document.getElementById(fieldId + '_error');
    if (field) { field.classList.add('field-success'); field.classList.remove('field-error'); }
    if (errEl) { errEl.classList.remove('visible'); errEl.textContent = ''; }
}

function clearFieldStates() {
    document.querySelectorAll('.form-control').forEach(el => {
        el.classList.remove('field-error', 'field-success');
    });
    document.querySelectorAll('.field-error-msg').forEach(el => {
        el.classList.remove('visible');
        el.textContent = '';
    });
}

// ============================================================
// VALIDATION
// ============================================================

const VALIDATORS = {
    email:    (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
    password: (v) => /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/.test(v),
    phone:    (v) => /^[\d\s\-+()]{7,15}$/.test(v.trim()),
};

function validateSignupForm() {
    clearFieldStates();
    let valid = true;

    const firstName = document.getElementById('first_name').value.trim();
    const lastName  = document.getElementById('last_name').value.trim();
    const email     = document.getElementById('email').value.trim();
    const phone     = document.getElementById('phone_number').value.trim();
    const password  = document.getElementById('password_signup').value;
    const confirm   = document.getElementById('password_confirm').value;

    if (!firstName || firstName.length < 2) {
        showFieldError('first_name', 'First name must be at least 2 characters.');
        valid = false;
    } else { showFieldSuccess('first_name'); }

    if (!lastName || lastName.length < 2) {
        showFieldError('last_name', 'Last name must be at least 2 characters.');
        valid = false;
    } else { showFieldSuccess('last_name'); }

    if (!email || !VALIDATORS.email(email)) {
        showFieldError('email', 'Please enter a valid email address.');
        valid = false;
    } else { showFieldSuccess('email'); }

    if (!phone || !VALIDATORS.phone(phone)) {
        showFieldError('phone_number', 'Please enter a valid phone number.');
        valid = false;
    } else { showFieldSuccess('phone_number'); }

    if (!password || !VALIDATORS.password(password)) {
        showFieldError('password_signup', 'Min 8 chars, one uppercase letter and one number.');
        valid = false;
    } else { showFieldSuccess('password_signup'); }

    if (!confirm) {
        showFieldError('password_confirm', 'Please confirm your password.');
        valid = false;
    } else if (password !== confirm) {
        showFieldError('password_confirm', 'Passwords do not match.');
        valid = false;
    } else { showFieldSuccess('password_confirm'); }

    return valid;
}

// Real-time password match feedback
['password_signup', 'password_confirm'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
        const pw  = document.getElementById('password_signup').value;
        const cfm = document.getElementById('password_confirm').value;
        if (cfm) {
            if (pw !== cfm) showFieldError('password_confirm', 'Passwords do not match.');
            else showFieldSuccess('password_confirm');
        }
    });
});

// ============================================================
// AJAX FETCH WRAPPER
// ============================================================
async function apiFetch(form, bodyData = null) {
    const data = bodyData || new FormData(form);
    try {
        const res = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: data,
        });
        const result = await res.json();
        return { ok: res.ok, result, status: res.status };
    } catch (err) {
        console.error('apiFetch error:', err);
        return { ok: false, result: { message: 'Network error. Please try again.' }, status: 500 };
    }
}

// ============================================================
// FORM SUBMISSIONS
// ============================================================

// 1. Login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('loginError');
        const { ok, result, status } = await apiFetch(loginForm);
        if (ok && result.redirect_url) {
            window.location.href = result.redirect_url;
        } else {
            showAlert('loginError', result.message || `Error (${status})`);
        }
    });
}

// 2. Signup
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('signupError');

        if (!validateSignupForm()) {
            showAlert('signupError', 'Please correct the highlighted fields.');
            return;
        }

        const btn = document.getElementById('signupSubmitBtn');
        const origText = btn.textContent;
        btn.disabled = true;
        btn.textContent = 'Creating Account…';

        // Build FormData manually for clarity
        const fd = new FormData();
        fd.append('csrfmiddlewaretoken', getCSRFToken());
        fd.append('first_name',    document.getElementById('first_name').value.trim());
        fd.append('last_name',     document.getElementById('last_name').value.trim());
        fd.append('email',         document.getElementById('email').value.trim());
        fd.append('country_code',  document.getElementById('country_code').value);
        fd.append('phone_number',  document.getElementById('phone_number').value.trim());
        fd.append('password',      document.getElementById('password_signup').value);
        fd.append('password_confirm', document.getElementById('password_confirm').value);

        const { ok, result, status } = await apiFetch(signupForm, fd);

        btn.disabled = false;
        btn.textContent = origText;

        if (ok) {
            closeAllAuthModals();
            openModal(modals.login);
            showAlert('loginError', '<strong>Success!</strong> Account created. Please sign in.', 'success');
        } else {
            let msg = result.message || 'Registration failed.';
            if (result.errors) {
                let detail = '<strong>Please fix the following:</strong><br>';
                for (const [field, errors] of Object.entries(result.errors)) {
                    const err = Array.isArray(errors) ? errors[0] : errors;
                    if (typeof err === 'string') {
                        detail += `&bull; <strong>${field.replace(/_/g, ' ')}</strong>: ${err}<br>`;
                        if (document.getElementById(field)) showFieldError(field, err);
                    }
                }
                msg = detail;
            }
            showAlert('signupError', msg);
        }
    });
}

// 3. Forgot Password (Generate Code)
const generateCodeForm = document.getElementById('generateCodeForm');
if (generateCodeForm) {
    generateCodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('generateCodeError');
        const { ok, result, status } = await apiFetch(generateCodeForm);
        if (ok) { closeAllAuthModals(); openModal(modals.verifyCode); }
        else { showAlert('generateCodeError', result.message || `Error (${status})`); }
    });
}

// 4. Verify Code
const verifyCodeForm = document.getElementById('verifyCodeForm');
if (verifyCodeForm) {
    verifyCodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('verifyCodeError');
        const { ok, result, status } = await apiFetch(verifyCodeForm);
        if (ok) { closeAllAuthModals(); openModal(modals.setNewPassword); }
        else { showAlert('verifyCodeError', result.message || 'Invalid or expired code.'); }
    });
}

// 5. Set New Password
const setNewPasswordForm = document.getElementById('setNewPasswordForm');
if (setNewPasswordForm) {
    setNewPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert('setPasswordError');
        const { ok, result, status } = await apiFetch(setNewPasswordForm);
        if (ok) {
            if (result.redirect_url) { window.location.href = result.redirect_url; }
            else {
                closeAllAuthModals();
                openModal(modals.login);
                showAlert('loginError', result.message || 'Password updated! Please sign in.', 'success');
            }
        } else { showAlert('setPasswordError', result.message || `Error (${status})`); }
    });
}

// ============================================================
// CART STATE & DISPLAY
// ============================================================

let cartItems = [];
let currentEditingItem = null;

function getAllCartViews() {
    return document.querySelectorAll('.cart-modal-view');
}

function hideAllCartViews() {
    getAllCartViews().forEach(v => v.classList.add('hidden'));
}

function showCartView() {
    hideAllCartViews();
    updateCartDisplay();

    if (cartItems.length === 0) {
        document.getElementById('emptyCartView').classList.remove('hidden');
    } else {
        document.getElementById('cartView').classList.remove('hidden');
    }
}

function showEmptyCartView() {
    hideAllCartViews();
    document.getElementById('emptyCartView').classList.remove('hidden');
}

function showUpdateCartItemView(itemId) {
    currentEditingItem = cartItems.find(item => item.id === itemId);
    if (!currentEditingItem) { console.error('Item not found:', itemId); showCartView(); return; }

    hideAllCartViews();
    document.getElementById('updateCartView').classList.remove('hidden');
    populateUpdateForm(currentEditingItem);
}

function showRemoveItemView(itemId) {
    currentEditingItem = cartItems.find(item => item.id === itemId);
    if (!currentEditingItem) { console.error('Item not found:', itemId); showCartView(); return; }

    hideAllCartViews();
    document.getElementById('removeItemView').classList.remove('hidden');
    document.getElementById('removeItemDetails').innerHTML = buildMiniItemCard(currentEditingItem);
}

function showEmptyCartConfirm() {
    hideAllCartViews();
    document.getElementById('emptyCartConfirmView').classList.remove('hidden');
    document.getElementById('emptyCartCount').textContent = cartItems.length;
}

function buildMiniItemCard(item) {
    return `
        <div style="display:flex;align-items:center;gap:1rem;justify-content:center;">
            <img src="${item.image}" alt="${item.name}" style="width:64px;height:64px;object-fit:cover;border-radius:8px;">
            <div style="text-align:left;">
                <p style="font-weight:600;">${item.name}</p>
                <p style="font-size:0.875rem;color:var(--color-gray-500);">Qty: ${item.quantity}</p>
                <p style="font-size:0.875rem;color:var(--color-primary);font-weight:700;">
                    $${(item.price * item.quantity).toFixed(2)}
                </p>
            </div>
        </div>
    `;
}

function populateUpdateForm(item) {
    document.getElementById('updateItemDetails').innerHTML = buildMiniItemCard(item);
    document.getElementById('updateSize').value    = item.size  || 'M';
    document.getElementById('updateColor').value   = item.color || 'Black';
    document.getElementById('updateQuantity').value = item.quantity;
}

function incrementUpdateQuantity() {
    const input = document.getElementById('updateQuantity');
    input.value = parseInt(input.value || 1) + 1;
}

function decrementUpdateQuantity() {
    const input = document.getElementById('updateQuantity');
    const val   = parseInt(input.value || 1);
    if (val > 1) input.value = val - 1;
}

function updateCartDisplay() {
    const container = document.getElementById('cartItemsContainer');
    const countEl   = document.getElementById('cartItemCount');
    const headerCountEl = document.getElementById('headerCartCount');

    const total = cartItems.reduce((sum, item) => sum + item.quantity, 0);
    if (countEl)      countEl.textContent     = `${total} item${total !== 1 ? 's' : ''} in your cart`;
    if (headerCountEl) headerCountEl.textContent = total;

    if (!container) return;

    if (cartItems.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = cartItems.map(item => `
        <div style="display:flex;align-items:center;gap:1rem;padding:1rem 0;border-bottom:1px solid var(--color-gray-100);">
            <img src="${item.image}" alt="${item.name}"
                 style="width:72px;height:72px;object-fit:cover;border-radius:8px;flex-shrink:0;">
            <div style="flex:1;min-width:0;">
                <p style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${item.name}</p>
                <p style="font-size:0.8rem;color:var(--color-gray-400);">
                    ${item.size ? `Size: ${item.size}` : ''}
                    ${item.color ? ` &bull; Color: ${item.color}` : ''}
                </p>
                <p style="color:var(--color-primary);font-weight:700;">$${(item.price * item.quantity).toFixed(2)}</p>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:0.5rem;">
                <span style="font-size:0.8rem;color:var(--color-gray-500);">×${item.quantity}</span>
                <button onclick="showUpdateCartItemView(${item.id})"
                        style="font-size:0.75rem;color:var(--color-primary);background:none;border:none;cursor:pointer;">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="showRemoveItemView(${item.id})"
                        style="font-size:0.75rem;color:var(--color-danger);background:none;border:none;cursor:pointer;">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');

    // Totals
    const SHIPPING = 5;
    const TAX_RATE = 0.08;
    const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const tax      = subtotal * TAX_RATE;
    const total_price   = subtotal + tax + (subtotal > 0 ? SHIPPING : 0);

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('cartSubtotal', `$${subtotal.toFixed(2)}`);
    set('cartShipping', subtotal > 0 ? `$${SHIPPING.toFixed(2)}` : '$0.00');
    set('cartTax',      `$${tax.toFixed(2)}`);
    set('cartTotal',    `$${total_price.toFixed(2)}`);
}

function confirmRemoveItem() {
    if (!currentEditingItem) return;
    cartItems = cartItems.filter(item => item.id !== currentEditingItem.id);
    currentEditingItem = null;
    showCartView();
}

function confirmEmptyCart() {
    cartItems = [];
    showEmptyCartView();
    updateCartDisplay();
}

function proceedToCheckout() {
    console.log('Proceeding to checkout with:', cartItems);
    window.location.href = '/checkout/';
}

// Update cart form submission
const updateCartForm = document.getElementById('updateCartForm');
if (updateCartForm) {
    updateCartForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!currentEditingItem) return;

        const idx = cartItems.findIndex(i => i.id === currentEditingItem.id);
        if (idx !== -1) {
            cartItems[idx].size     = document.getElementById('updateSize').value;
            cartItems[idx].color    = document.getElementById('updateColor').value;
            cartItems[idx].quantity = parseInt(document.getElementById('updateQuantity').value) || 1;
        }
        currentEditingItem = null;
        showCartView();
    });
}

// Expose cart functions globally so inline onclick attributes work
window.showCartView         = showCartView;
window.showEmptyCartView    = showEmptyCartView;
window.showUpdateCartItemView = showUpdateCartItemView;
window.showRemoveItemView   = showRemoveItemView;
window.showEmptyCartConfirm = showEmptyCartConfirm;
window.confirmRemoveItem    = confirmRemoveItem;
window.confirmEmptyCart     = confirmEmptyCart;
window.proceedToCheckout    = proceedToCheckout;
window.closeCartModal       = closeCartModal;
window.incrementUpdateQuantity = incrementUpdateQuantity;
window.decrementUpdateQuantity = decrementUpdateQuantity;

// ============================================================
// INIT — auto-dismiss Django message toasts
// ============================================================
document.querySelectorAll('.message-toast').forEach(toast => {
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s ease';
        toast.style.opacity    = '0';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
});

function sortProducts(value) {
    const grid  = document.getElementById('productsGrid');
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll('.product-card'));

    cards.sort((a, b) => {
        if (value === 'price-low')  return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
        if (value === 'price-high') return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
        if (value === 'name')       return a.dataset.name.localeCompare(b.dataset.name);
        return 0;
    });

    cards.forEach(card => grid.appendChild(card));
}

function addToCart(productId) {
    fetch("{% url 'xypher_lux:add_to_cart' %}", {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `product_id=${productId}&quantity=1`
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Update cart badge in header
            const badge = document.getElementById('headerCartCount');
            if (badge) badge.textContent = data.cart_total_items;
            alert(data.message);
        } else {
            alert(data.message || 'Could not add to cart.');
        }
    })
    .catch(() => alert('Something went wrong. Please try again.'));
}

// Header search expand
const searchForm  = document.querySelector('.header-search-form');
const searchInput = document.getElementById('headerSearchInput');
const searchBtn   = searchForm ? searchForm.querySelector('.header-icon-btn') : null;

if (searchBtn && searchInput) {
    searchBtn.addEventListener('click', (e) => {
        if (!searchForm.classList.contains('is-open')) {
            e.preventDefault();              // don't submit yet
            searchForm.classList.add('is-open');
            searchInput.focus();
        }
        // if already open and input has text → let form submit normally
    });

    // Close if user clicks outside
    document.addEventListener('click', (e) => {
        if (searchForm && !searchForm.contains(e.target)) {
            searchForm.classList.remove('is-open');
        }
    });
}


// profile section 

document.querySelectorAll('.nav-link[data-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.profile-section').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.target).classList.add('active');
    });
  });
 
  // ── Helper: AJAX form submit ────────────────────────────────────
  async function submitForm(form, btnId, errorId, successId) {
    const btn = document.getElementById(btnId);
    const errorEl = document.getElementById(errorId);
    const successEl = document.getElementById(successId);
 
    errorEl.style.display = 'none';
    successEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Saving…';
 
    const { ok, result } = await apiFetch(form);
 
    btn.disabled = false;
    btn.textContent = btn.id === 'passwordBtn' ? 'Update password' : 'Save changes';
 
    if (ok) {
      successEl.textContent = result.message;
      successEl.style.display = 'block';
      if (btn.id === 'passwordBtn') form.reset();
    } else {
      errorEl.textContent = result.message;
      errorEl.style.display = 'block';
    }
  }
 
  // ── Profile form ────────────────────────────────────────────────


  // ── Sidebar navigation ──────────────────────────────────────────
  document.querySelectorAll('.nav-link[data-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.profile-section').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.target).classList.add('active');
    });
  });

  // ── Helper: AJAX form submit ────────────────────────────────────
  async function submitForm(form, btnId, errorId, successId) {
    const btn       = document.getElementById(btnId);
    const errorEl   = document.getElementById(errorId);
    const successEl = document.getElementById(successId);

    // reset messages
    errorEl.style.display   = 'none';
    successEl.style.display = 'none';

    btn.disabled    = true;
    btn.textContent = 'Saving…';

    const { ok, result } = await apiFetch(form);

    btn.disabled = false;
    btn.textContent = btnId === 'passwordBtn' ? 'Update password' : 'Save changes';

    if (ok) {
      successEl.textContent    = result.message;
      successEl.style.display  = 'block';
      if (btnId === 'passwordBtn') form.reset();
    } else {
      errorEl.textContent   = result.message;
      errorEl.style.display = 'block';
    }
  }

  // ── Profile form ────────────────────────────────────────────────
  document.getElementById('profileForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm(this, 'profileBtn', 'profileError', 'profileSuccess');
  });

  // ── Password form ───────────────────────────────────────────────
  document.getElementById('passwordForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm(this, 'passwordBtn', 'passwordError', 'passwordSuccess');
  });

  // ── Delete account ──────────────────────────────────────────────
  document.getElementById('deleteAccountBtn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to permanently delete your account? This cannot be undone.')) return;

    try {
      const res    = await fetch("{% url 'xypher_lux:delete_account' %}", {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
      const result = await res.json();
      if (res.ok) window.location.href = result.redirect_url;
    } catch (err) {
      console.error('Delete account error:', err);
      alert('Something went wrong. Please try again.');
    }
  });

  // ── Deep-link to a tab via URL hash e.g. /profile/#manage ──────
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    const target = document.querySelector(`.nav-link[data-target="${hash}"]`);
    if (target) target.click();
  }