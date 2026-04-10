document.addEventListener('DOMContentLoaded', function () {
    const nomePopularInput = document.getElementById('id_nome_popular');
    const nomeCientificoInput = document.getElementById('id_nome_cientifico');
    const datalist = document.getElementById('datalist-nome-popular');

    // Loader visual
    let loader = document.createElement('span');
    loader.textContent = " ⏳";
    loader.style.display = "none";
    nomePopularInput && nomePopularInput.parentNode.appendChild(loader);

    // Debounce para evitar requisições demais
    let debounceTimeout;
    const DEBOUNCE_DELAY = 200;
    // Se usuário editou nome científico manualmente, não sobrescrever mais
    let nomeCientificoEditado = false;
    if (nomeCientificoInput) {
        nomeCientificoInput.addEventListener('input', function () {
            nomeCientificoEditado = true;
        });
    }

    // Adiciona eventos para clicar em sugestão (caso browser não suporte datalist)
    function enableDatalistSelection() {
        // Somente para browsers sem suporte
        if (!window.HTMLDataListElement) {
            datalist.style.border = "1px solid #bbb";
            datalist.style.maxHeight = "120px";
            datalist.style.overflowY = "auto";
            datalist.style.position = "absolute";
            datalist.style.background = "#fff";
            datalist.style.zIndex = "11";
            datalist.addEventListener("click", function (e) {
                if (e.target.tagName === "OPTION") {
                    nomePopularInput.value = e.target.value;
                    datalist.innerHTML = "";
                }
            });
        }
    }

    if (nomePopularInput) {
        nomePopularInput.setAttribute("autocomplete", "off");
        nomePopularInput.addEventListener('input', function () {
            clearTimeout(debounceTimeout);
            loader.style.display = "none";

            // Função principal com debounce
            debounceTimeout = setTimeout(async () => {
                const nome = nomePopularInput.value.trim();

                if (nome.length >= 2 && datalist) {
                    // Mostra loader
                    loader.style.display = "";
                    try {
                        // --- AUTOCOMPLETE ---
                        const res = await fetch(`/api/autocomplete-nome/?term=${encodeURIComponent(nome)}`);
                        if (!res.ok) throw new Error('Erro ao buscar sugestões');
                        const sugestoes = await res.json();
                        datalist.innerHTML = '';
                        sugestoes.forEach(v => {
                            const opt = document.createElement('option');
                            opt.value = v;
                            datalist.appendChild(opt);
                        });
                        enableDatalistSelection();
                    } catch (err) {
                        datalist.innerHTML = '';
                        console.error('Erro ao buscar sugestões:', err);
                    } finally {
                        loader.style.display = "none";
                    }

                    // --- NOME CIENTÍFICO ---
                    if (nomeCientificoInput && !nomeCientificoEditado) {
                        try {
                            const res = await fetch(`/api/nome-cientifico/?nome_popular=${encodeURIComponent(nome)}`);
                            if (!res.ok) throw new Error('Erro ao buscar nome científico');
                            const data = await res.json();
                            nomeCientificoInput.value = data.nome_cientifico || '';
                        } catch (err) {
                            // não altera o valor em caso de erro
                            console.error('Erro ao buscar nome científico:', err);
                        }
                    }
                } else {
                    datalist.innerHTML = '';
                }
            }, DEBOUNCE_DELAY);
        });

        // Permite aceitar sugestão com tecla "seta para baixo" + enter (UX nativa)
        nomePopularInput.addEventListener('keydown', function (e) {
            if (e.key === "ArrowDown" && datalist.options.length > 0) {
                datalist.options[0].selected = true;
            }
        });
    }
});
