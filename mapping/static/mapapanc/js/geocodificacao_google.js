document.addEventListener("DOMContentLoaded", () => {
    // API Key deve ser configurada no backend via settings Django
    const API_KEY = window.LOCATIONIQ_API_KEY || "";

    const inputLoc = document.getElementById("id_localizacao");
    const loader = document.getElementById("endereco-loader");

    const campos = {
        endereco: document.getElementById("id_endereco"),
        bairro: document.getElementById("id_bairro"),
        cidade: document.getElementById("id_cidade"),
        estado: document.getElementById("id_estado")
    };

    function preencherCampos(data) {
        const address = data.address || {};
        campos.endereco.value = address.road || address.name || '';
        campos.bairro.value = address.suburb || address.neighbourhood || address.village || '';
        campos.cidade.value = address.city || address.town || address.village || '';
        campos.estado.value = address.state || address.region || '';
    }

    function reverseGeocode(lat, lon) {
        loader && (loader.style.display = "inline-block");
        fetch(`https://us1.locationiq.com/v1/reverse?key=${API_KEY}&lat=${lat}&lon=${lon}&format=json`)
            .then(response => response.json())
            .then(data => {
                preencherCampos(data);
            })
            .catch(err => console.error("? Erro na LocationIQ:", err))
            .finally(() => loader && (loader.style.display = "none"));
    }

    // Extra��o de coordenadas do campo
    function extrairCoordenadas(valor) {
        const match = valor.match(/^POINT\s*\(([-\d.]+)\s+([-\d.]+)\)$/);
        return match ? { lon: match[1], lat: match[2] } : null;
    }

    // Inicializa��o no clique do mapa
    window.leafletMapInit = function (map, options) {

        map.on("click", function (e) {
            const lat = e.latlng.lat.toFixed(6);
            const lon = e.latlng.lng.toFixed(6);
            const ponto = `POINT (${lon} ${lat})`;

            inputLoc.value = ponto;
            inputLoc.dispatchEvent(new Event("change", { bubbles: true }));

            reverseGeocode(lat, lon);
        });
    };

    // Observa altera��es no campo
    let valorAnterior = "";
    setInterval(() => {
        const val = inputLoc.value;
        if (val && val !== valorAnterior && val.startsWith("POINT")) {
            valorAnterior = val;
            const coords = extrairCoordenadas(val);
            if (coords) reverseGeocode(coords.lat, coords.lon);
        }
    }, 800);
});
