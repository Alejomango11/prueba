/**
 * Sistema Académico de Administración de Tareas - JavaScript Frontend
 * =================================================================
 */

// Estado global
let tareas = [];
let calendarConnected = false;

// ============================================================================
// Inicialización
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {
    // Cargar datos iniciales
    cargarTareas();
    cargarEstadisticas();
    cargarAlertas();
    verificarEstadoCalendar();

    // Configurar fecha mínima en el formulario
    const fechaInput = document.getElementById('fecha');
    if (fechaInput) {
        const hoy = new Date().toISOString().split('T')[0];
        fechaInput.min = hoy;
        fechaInput.value = hoy;
    }
});

// ============================================================================
// Gestión de Tareas
// ============================================================================

async function cargarTareas() {
    try {
        const filtro = document.getElementById('filterSelect').value;
        const response = await fetch(`/api/tareas?filtro=${filtro}`);
        const data = await response.json();

        if (data.success) {
            tareas = data.tareas;
            renderizarTareas(tareas);
        } else {
            mostrarToast('Error al cargar tareas', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error de conexión', 'error');
    }
}

function renderizarTareas(tareas) {
    const container = document.getElementById('tareasList');

    if (tareas.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-list"></i>
                <h3>No hay tareas</h3>
                <p>Agrega tu primera tarea usando el botón "Nueva Tarea"</p>
            </div>
        `;
        return;
    }

    container.innerHTML = tareas.map((tarea, index) => crearTareaHTML(tarea, index)).join('');
}

function crearTareaHTML(tarea, index) {
    const hoy = new Date();
    const fechaEntrega = new Date(tarea.fecha_entrega);
    const diasRestantes = Math.ceil((fechaEntrega - hoy) / (1000 * 60 * 60 * 24));

    let diasClass = 'futura';
    let diasTexto = `${diasRestantes} días restantes`;

    if (diasRestantes < 0) {
        diasClass = 'vencida';
        diasTexto = `Vencida hace ${Math.abs(diasRestantes)} días`;
    } else if (diasRestantes === 0) {
        diasClass = 'hoy';
        diasTexto = 'Vence hoy';
    } else if (diasRestantes <= 3) {
        diasClass = 'proxima';
        diasTexto = `${diasRestantes} días restantes`;
    }

    const syncIcon = tarea.google_event_id
        ? '<span class="tarea-sync" title="Sincronizado con Google Calendar"><i class="fab fa-google"></i></span>'
        : '';

    return `
        <div class="tarea-item ${tarea.estado}" data-index="${index}">
            <div class="tarea-prioridad ${tarea.prioridad}"></div>
            <div class="tarea-content">
                <div class="tarea-nombre">
                    ${tarea.nombre} ${syncIcon}
                </div>
                <div class="tarea-meta">
                    <span><i class="fas fa-calendar"></i> ${formatearFecha(tarea.fecha_entrega)}</span>
                    <span class="tarea-estado ${tarea.estado}">${tarea.estado}</span>
                    <span class="tarea-dias ${diasClass}">${diasTexto}</span>
                </div>
            </div>
            <div class="tarea-actions">
                ${tarea.estado === 'pendiente'
                    ? `<button class="btn-action complete" onclick="completarTarea(${index})" title="Marcar como completada">
                        <i class="fas fa-check"></i>
                       </button>`
                    : ''}
                <button class="btn-action delete" onclick="eliminarTarea(${index})" title="Eliminar tarea">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
}

async function agregarTarea(event) {
    event.preventDefault();

    const nombre = document.getElementById('nombre').value.trim();
    const fecha = document.getElementById('fecha').value;
    const prioridad = document.getElementById('prioridad').value;
    const syncCalendar = document.getElementById('syncCalendar').checked;

    if (!nombre || !fecha || !prioridad) {
        mostrarToast('Por favor complete todos los campos', 'warning');
        return false;
    }

    try {
        const response = await fetch('/api/tareas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre,
                fecha,
                prioridad,
                sync_calendar: syncCalendar
            })
        });

        const data = await response.json();

        if (data.success) {
            mostrarToast(
                data.synced
                    ? '✅ Tarea agregada y sincronizada con Google Calendar'
                    : '✅ Tarea agregada exitosamente',
                'success'
            );
            closeModal('modalAdd');
            document.getElementById('formAddTarea').reset();
            cargarTareas();
            cargarEstadisticas();
            cargarAlertas();
        } else {
            mostrarToast(data.error || 'Error al agregar tarea', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error de conexión', 'error');
    }

    return false;
}

async function completarTarea(index) {
    try {
        const response = await fetch(`/api/tareas/${index}/completar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sync_calendar: calendarConnected })
        });

        const data = await response.json();

        if (data.success) {
            mostrarToast('✅ Tarea completada', 'success');
            cargarTareas();
            cargarEstadisticas();
        } else {
            mostrarToast(data.error || 'Error al completar tarea', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error de conexión', 'error');
    }
}

async function eliminarTarea(index) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta tarea?')) {
        return;
    }

    try {
        const response = await fetch(`/api/tareas/${index}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sync_calendar: calendarConnected })
        });

        const data = await response.json();

        if (data.success) {
            mostrarToast('🗑️ Tarea eliminada', 'success');
            cargarTareas();
            cargarEstadisticas();
            cargarAlertas();
        } else {
            mostrarToast(data.error || 'Error al eliminar tarea', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('Error de conexión', 'error');
    }
}

// ============================================================================
// Estadísticas
// ============================================================================

async function cargarEstadisticas() {
    try {
        const response = await fetch('/api/estadisticas');
        const data = await response.json();

        if (data.success) {
            const stats = data.estadisticas;
            document.getElementById('statTotal').textContent = stats.total;
            document.getElementById('statCompletadas').textContent = stats.completadas;
            document.getElementById('statPendientes').textContent = stats.pendientes;
            document.getElementById('statProductividad').textContent = stats.productividad + '%';
        }
    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// ============================================================================
// Alertas
// ============================================================================

async function cargarAlertas() {
    try {
        const response = await fetch('/api/alertas');
        const data = await response.json();

        if (data.success && data.alertas.length > 0) {
            const container = document.getElementById('alertasContainer');
            const list = document.getElementById('alertasList');

            list.innerHTML = data.alertas.map(alerta => {
                const tipoClass = alerta.tipo;
                const icono = alerta.tipo === 'vencida' ? '🔴' :
                             alerta.tipo === 'urgente' ? '🟠' : '🟡';
                const mensaje = alerta.dias_restantes < 0
                    ? `Vencida hace ${Math.abs(alerta.dias_restantes)} días`
                    : alerta.dias_restantes === 0
                    ? 'Vence hoy'
                    : `Vence en ${alerta.dias_restantes} días`;

                return `
                    <div class="alerta-item ${tipoClass}">
                        <span>${icono}</span>
                        <div>
                            <strong>${alerta.tarea.nombre}</strong>
                            <small> - ${mensaje}</small>
                        </div>
                    </div>
                `;
            }).join('');

            container.classList.remove('hidden');
        } else {
            document.getElementById('alertasContainer').classList.add('hidden');
        }
    } catch (error) {
        console.error('Error al cargar alertas:', error);
    }
}

function verAlertas() {
    cargarAlertasModal();
    openModal('modalAlertas');
}

async function cargarAlertasModal() {
    try {
        const response = await fetch('/api/alertas');
        const data = await response.json();

        const container = document.getElementById('modalAlertasContent');

        if (data.success && data.alertas.length > 0) {
            container.innerHTML = data.alertas.map(alerta => {
                const icono = alerta.tipo === 'vencida' ? '🔴' :
                             alerta.tipo === 'urgente' ? '🟠' : '🟡';
                const clase = alerta.tipo;
                const mensaje = alerta.dias_restantes < 0
                    ? `Vencida hace ${Math.abs(alerta.dias_restantes)} días`
                    : alerta.dias_restantes === 0
                    ? 'Vence hoy'
                    : `Vence en ${alerta.dias_restantes} días`;

                return `
                    <div class="alerta-item ${clase}" style="margin-bottom: 0.75rem;">
                        <span style="font-size: 1.25rem;">${icono}</span>
                        <div>
                            <strong>${alerta.tarea.nombre}</strong>
                            <div style="font-size: 0.875rem; color: #64748b;">
                                Fecha límite: ${formatearFecha(alerta.tarea.fecha_entrega)}<br>
                                <strong>${mensaje}</strong>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state" style="padding: 2rem;">
                    <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                    <h3>¡Todo en orden!</h3>
                    <p>No hay tareas vencidas ni próximas a vencer.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ============================================================================
// Google Calendar
// ============================================================================

async function verificarEstadoCalendar() {
    try {
        const response = await fetch('/calendar/status');
        const data = await response.json();

        calendarConnected = data.connected;
        updateCalendarUI();
    } catch (error) {
        console.error('Error al verificar estado de Calendar:', error);
    }
}

function updateCalendarUI() {
    const btn = document.getElementById('btnCalendar');
    const status = document.getElementById('calendarStatus');

    if (calendarConnected) {
        btn.classList.add('connected');
        status.textContent = 'Google Calendar Conectado';
        document.getElementById('calendarConnected').classList.remove('hidden');
        document.getElementById('calendarDisconnected').classList.add('hidden');
    } else {
        btn.classList.remove('connected');
        status.textContent = 'Conectar Google Calendar';
        document.getElementById('calendarConnected').classList.add('hidden');
        document.getElementById('calendarDisconnected').classList.remove('hidden');
    }
}

function toggleCalendarModal() {
    verificarEstadoCalendar();
    openModal('modalCalendar');
}

// ============================================================================
// Utilidades
// ============================================================================

function formatearFecha(fechaStr) {
    const opciones = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(fechaStr).toLocaleDateString('es-ES', opciones);
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Cerrar modal al hacer clic fuera
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// ============================================================================
// Toast Notifications
// ============================================================================

function mostrarToast(mensaje, tipo = 'info') {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;

    const iconos = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <span style="font-size: 1.25rem;">${iconos[tipo]}</span>
        <span>${mensaje}</span>
    `;

    container.appendChild(toast);

    // Auto-eliminar después de 4 segundos
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================================================
// Atajos de teclado
// ============================================================================

document.addEventListener('keydown', function(e) {
    // ESC para cerrar modales
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    // Ctrl/Cmd + N para nueva tarea
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        openModal('modalAdd');
    }
});
