// Função exemplo para destacar um marcador específico
function focusMarker(pontoId) {
    const marker = markers.find(m => m.pontoId == pontoId);
    if (marker) {
        map.setView(marker.getLatLng(), 14);
        marker.openPopup();
    }
}

// Carregar alertas ativos via AJAX (exemplo básico)
async function carregarAlertasAtivos() {
    try {
        const res = await fetch('/api/alertas-ativos/');
        const alertas = await res.json();
        // TODO: Inserir lógica para exibir alertas dinamicamente no frontend
    } catch (err) {
        console.error('Erro ao carregar alertas ativos:', err);
    }
}

document.addEventListener('DOMContentLoaded', carregarAlertasAtivos);
