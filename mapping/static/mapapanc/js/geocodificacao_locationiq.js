window.addEventListener("DOMContentLoaded", () => {
    const inputLocalizacao = document.getElementById("id_localizacao");
    const loader = document.getElementById("endereco-loader");
    const infoCoordenadas = document.getElementById("coordenadas-exatas");
    const btnDirecionar = document.getElementById("btn-direcionar");

    const campos = {
        endereco: document.getElementById("id_endereco"),
        bairro: document.getElementById("id_bairro"),
        cidade: document.getElementById("id_cidade"),
        estado: document.getElementById("id_estado"),
    };

    function preencherCamposEndereco(addr) {
        if (!addr) return;

        // Preenche os campos com animação suave
        const preencherCampo = (campo, valor) => {
            if (campo && valor) {
                campo.value = valor;
                campo.style.backgroundColor = '#e8f5e9';
                setTimeout(() => {
                    campo.style.transition = 'background-color 0.8s';
                    campo.style.backgroundColor = '';
                }, 100);
            }
        };

        preencherCampo(campos.endereco, addr.road || addr.street || addr.name || '');
        preencherCampo(campos.bairro, addr.suburb || addr.neighbourhood || addr.village || addr.quarter || '');
        preencherCampo(campos.cidade, addr.city || addr.town || addr.municipality || addr.village || '');
        preencherCampo(campos.estado, addr.state || addr.region || addr.state_district || '');
    }

    function reverseGeocode(lat, lon) {
        if (!lat || !lon) return;

        if (loader) {
            loader.style.display = "inline-flex";
            loader.classList.remove('error', 'success');
            loader.classList.add('loading');
            loader.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Buscando endereço...';
        }

        // Usa Nominatim do OpenStreetMap (gratuito e sem necessidade de API key)
        const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`;

        fetch(url, {
            headers: {
                'User-Agent': 'ColaboraPANC/1.0'
            }
        })
            .then(res => {
                if (!res.ok) throw new Error("Erro ao buscar endereço");
                return res.json();
            })
            .then(data => {
                if (data && data.address) {
                    preencherCamposEndereco(data.address);

                    if (loader) {
                        loader.classList.remove('loading', 'error');
                        loader.classList.add('success');
                        loader.innerHTML = '<i class="bi bi-check-circle-fill"></i> Endereço preenchido!';
                        setTimeout(() => {
                            loader.style.display = "none";
                        }, 3000);
                    }
                } else {
                    throw new Error("Endereço não encontrado");
                }
            })
            .catch(err => {
                console.error("Erro no reverse geocoding:", err);

                if (loader) {
                    loader.classList.remove('loading', 'success');
                    loader.classList.add('error');
                    loader.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i> Não foi possível buscar o endereço. Preencha manualmente.';
                    setTimeout(() => {
                        loader.style.display = "none";
                    }, 5000);
                }
            });
    }

    function atualizarExibicaoCoordenadas(lat, lon) {
        if (infoCoordenadas) {
            infoCoordenadas.innerHTML = `<strong class="text-success">Lat:</strong> ${lat} | <strong class="text-success">Lng:</strong> ${lon}`;
        }

        // Habilita o botão do Google Maps
        if (btnDirecionar) {
            btnDirecionar.disabled = false;
            btnDirecionar.classList.remove('btn-outline-secondary');
            btnDirecionar.classList.add('btn-outline-primary');
        }
    }

    // Expõe função globalmente para ser chamada pelo template
    window.fillAddress = function(coords) {
        if (coords && coords.lat && coords.lng) {
            reverseGeocode(coords.lat, coords.lng);
            atualizarExibicaoCoordenadas(coords.lat, coords.lng);
        }
    };

    // Inicializa coordenadas se já existirem
    if (inputLocalizacao && inputLocalizacao.value) {
        const coordsMatch = inputLocalizacao.value.match(/^POINT\s*\(([-\d.]+)\s+([-\d.]+)\)$/);
        if (coordsMatch) {
            const lon = coordsMatch[1];
            const lat = coordsMatch[2];
            if (lat && lon) {
                atualizarExibicaoCoordenadas(lat, lon);
                reverseGeocode(lat, lon);
            }
        }
    }
});
