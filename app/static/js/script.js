// Mejoras de usabilidad para dispositivos móviles
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Inicializar popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })

    // Auto-ocultar alerts después de 5 segundos
    const alerts = document.querySelectorAll('.alert')
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert)
            bsAlert.close()
        }, 5000)
    })

    // Mejorar usabilidad de dropdowns en móviles
    if ('ontouchstart' in document.documentElement) {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.addEventListener('click', function(e) {
                e.stopPropagation()
            })
        })
    }

    // Prevenir zoom en inputs en iOS
    document.addEventListener('touchstart', function() {
        if (document.activeElement.tagName === 'INPUT') {
            document.activeElement.blur()
        }
    })

    // Optimizar tablas para móviles
    function optimizeTablesForMobile() {
        if (window.innerWidth < 768) {
            document.querySelectorAll('table').forEach(table => {
                if (!table.classList.contains('table-responsive')) {
                    table.classList.add('table-responsive')
                }
            })
        }
    }

    // Ejecutar al cargar y al redimensionar
    optimizeTablesForMobile()
    window.addEventListener('resize', optimizeTablesForMobile)

    // Mejorar experiencia de formularios en móviles
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            // Ocultar teclado virtual después de enviar formulario en móviles
            if ('ontouchstart' in document.documentElement) {
                document.activeElement.blur()
            }
        })
    })

    // Smooth scrolling para anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault()
            const target = document.querySelector(this.getAttribute('href'))
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                })
            }
        })
    })

    // Cerrar menú al hacer clic en un enlace (en móviles)
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function() {
            const navbarCollapse = document.querySelector('.navbar-collapse')
            if (navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse)
                bsCollapse.hide()
            }
        })
    })
})

// Detectar tipo de dispositivo
function getDeviceType() {
    const ua = navigator.userAgent
    if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
        return "tablet"
    } else if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
        return "mobile"
    }
    return "desktop"
}

// Ajustar interfaz según el dispositivo
function adjustUIForDevice() {
    const deviceType = getDeviceType()
    
    if (deviceType === 'mobile') {
        // Optimizaciones específicas para móviles
        document.body.classList.add('mobile-device')
    } else if (deviceType === 'tablet') {
        // Optimizaciones específicas para tablets
        document.body.classList.add('tablet-device')
    }
}

// Ejecutar al cargar la página
adjustUIForDevice()