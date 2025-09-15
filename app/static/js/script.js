document.addEventListener('DOMContentLoaded', function () {
    // Inicializar tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Inicializar popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })

    // Auto-ocultar alerts después de 5 segundos
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert)
            bsAlert.close()
        }, 5000)
    })

    // Mejorar usabilidad de dropdowns en móviles
    if ('ontouchstart' in document.documentElement) {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.addEventListener('click', function (e) {
                e.stopPropagation()
            })
        })
    }

    // Prevenir zoom en inputs en iOS
    document.addEventListener('touchstart', function () {
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
    optimizeTablesForMobile()
    window.addEventListener('resize', optimizeTablesForMobile)

    // Mejorar experiencia de formularios en móviles
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function () {
            if ('ontouchstart' in document.documentElement) {
                document.activeElement.blur()
            }
        })
    })

    // Smooth scrolling para anchors válidos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        const href = anchor.getAttribute('href')
        if (href.length > 1 && document.querySelector(href)) {
            anchor.addEventListener('click', function (e) {
                e.preventDefault()
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                })
            })
        }
    })

    // Cerrar menú al hacer clic en un enlace (solo en móviles, excepto dropdowns)
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function (e) {
            const isDropdownToggle = link.classList.contains('dropdown-toggle');

            if (!isDropdownToggle) {
                const navbarCollapse = document.querySelector('.navbar-collapse')
                if (navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse)
                    bsCollapse.hide()
                }
            }
        })
    })

    // Detectar tipo de dispositivo forma simple
    function getDeviceType() {
        const width = window.innerWidth
        if (width < 768) return "mobile"
        if (width < 1024) return "tablet"
        return "desktop"
    }

    //Más dispotivos
    // function getDeviceType() {
    //     const ua = navigator.userAgent
    //     if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
    //         return "tablet"
    //     } else if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
    //         return "mobile"
    //     }
    //     return "desktop"
    // }

    // Ajustar interfaz según el dispositivo
    function adjustUIForDevice() {
        const deviceType = getDeviceType()
        if (deviceType === 'mobile') {
            document.body.classList.add('mobile-device')
        } else if (deviceType === 'tablet') {
            document.body.classList.add('tablet-device')
        }
    } try {
        adjustUIForDevice()
    } catch (error) {
        console.error('Error adjusting UI for device:', error)
    }
})

document.querySelector('form').addEventListener('submit', function (e) {
    const productos = [];
    let total = 0;
    document.querySelectorAll('.producto-row').forEach(row => {
        const select = row.querySelector('.producto-select');
        const cantidadInput = row.querySelector('.cantidad-input');
        if (select.value && cantidadInput.value) {
            const precio = parseFloat(select.options[select.selectedIndex].dataset.precio);
            const cantidad = parseInt(cantidadInput.value);
            productos.push({
                producto_id: parseInt(select.value),
                cantidad: cantidad
            });
            total += precio * cantidad;
        }
    });
    document.getElementById('productos-json').value = JSON.stringify(productos);
    document.getElementById('total-hidden').value = total.toFixed(2); // 👈 aquí llenamos el total
});

document.addEventListener('DOMContentLoaded', function () {
    const tiendaSelect = document.getElementById('tienda_id');
    const proveedorSelect = document.getElementById('proveedor_id');

    function toggleFields() {
        if (tiendaSelect.value && tiendaSelect.value !== '-1') {
            proveedorSelect.disabled = true;
            proveedorSelect.value = '-1';
        } else if (proveedorSelect.value && proveedorSelect.value !== '-1') {
            tiendaSelect.disabled = true;
            tiendaSelect.value = '-1';
        } else {
            tiendaSelect.disabled = false;
            proveedorSelect.disabled = false;
        }
    }

    tiendaSelect.addEventListener('change', toggleFields);
    proveedorSelect.addEventListener('change', toggleFields);

    // Ejecutar al cargar la página por si hay valores pre-seleccionados
    toggleFields();
});