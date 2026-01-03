
content = """{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Hola, {{ aliado.nombre_visible }}</h2>
        <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" id="switchDisponibilidad" {% if aliado.esta_disponible %}checked{% endif %}>
            <label class="form-check-label" for="switchDisponibilidad">Disponible para chats</label>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12 mb-3 text-end">
            <a href="{% url 'aliado_registro_web' %}" class="btn btn-success">
                <i class="fas fa-user-plus"></i> Registrar Nuevo Aliado
            </a>
        </div>
        <div class="col-md-12">
            <div class="card shadow-sm">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0">Chats Activos</h5>
                </div>
                <div class="card-body p-0">
                    <div class="list-group list-group-flush" id="listaSesiones">
                        {% for sesion in sesiones %}
                        <a href="{% url 'aliado_chat_web' sesion.id %}"
                            class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">{{ sesion.usuario.alias }}</h6>
                                <small class="text-muted"><i class="fas fa-map-marker-alt"></i> {{
                                    sesion.usuario.zona|default:"Ubicación desconocida" }}</small>
                            </div>
                            <span class="badge bg-primary rounded-pill">Abrir Chat</span>
                        </a>
                        {% empty %}
                        <div class="p-4 text-center text-muted">
                            No tienes chats activos en este momento.
                            <br>
                            <small>Mantente "Disponible" para recibir nuevas solicitudes.</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Manejo del Switch de Disponibilidad
    document.getElementById('switchDisponibilidad').addEventListener('change', function () {
        const isChecked = this.checked;
        fetch("{% url 'aliado_toggle_status_web' %}", {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ disponible: isChecked })
        })
            .then(response => response.json())
            .then(data => {
                if (data.estado) {
                    console.log("Estado actualizado: " + data.estado);
                }
            });
    });

    // Auto-recarga simple para ver si entran nuevos chats (cada 10 seg)
    setTimeout(() => {
        window.location.reload();
    }, 15000);
</script>
{% endblock %}
"""

import os
file_path = os.path.join("core", "templates", "aliado_dashboard.html")
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("File rewritten successfully.")
