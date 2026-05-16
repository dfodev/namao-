// ===== ANIMAÇÕES GLOBAIS =====
document.addEventListener('DOMContentLoaded', () => {
    // AOS já está inicializado no base.html

    // Fechar modais com ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-custom, .profile-sidebar').forEach(modal => {
                modal.classList.remove('open');
                modal.style.display = 'none';
            });
        }
    });

    // Máscara para telefone
    const telefoneInputs = document.querySelectorAll('input[type="tel"], input[name="telefone"]');
    telefoneInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);
            e.target.value = value;
        });
    });
});

// ===== FUNÇÃO PARA TOAST NOTIFICATIONS =====
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.style.minWidth = '250px';
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        ${message}
        <button type="button" class="btn-close float-end" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ===== TOGGLE PASSWORD =====
function togglePassword(inputId, buttonElement) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        buttonElement.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        input.type = 'password';
        buttonElement.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// ===== CONFIRM ACTION =====
function confirmAction(message, url) {
    if (confirm(message)) {
        window.location.href = url;
    }
    return false;
}