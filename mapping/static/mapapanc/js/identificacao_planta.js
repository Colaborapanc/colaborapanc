document.addEventListener("DOMContentLoaded", () => {
  const btnIdentificar = document.getElementById("btn-identificar");
  const fi = document.getElementById("id_identificacao_foto");
  if (!btnIdentificar) return;

  if (fi) {
    fi.addEventListener("change", () => {
      if (fi.files?.length) {
        const dv = document.getElementById("identificacao-resultado");
        if (dv) {
          dv.innerHTML = '<i class="bi bi-info-circle-fill"></i> Foto selecionada. Clique em <strong>Identificar com IA</strong> para sugerir nomes automaticamente.';
          dv.className = "alert alert-info d-block";
          dv.removeAttribute("hidden");
        }
        setTimeout(() => btnIdentificar.click(), 250);
      }
    });
  }

  btnIdentificar.addEventListener("click", () => {
    const dv = document.getElementById("identificacao-resultado");

    if (!fi.files?.length) {
      dv.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i> <strong>Atenção:</strong> Selecione uma foto para identificar.';
      dv.className = "alert alert-warning d-block";
      dv.removeAttribute("hidden");
      return;
    }

    // Validação de tamanho de arquivo (máx 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (fi.files[0].size > maxSize) {
      dv.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> <strong>Erro:</strong> A foto é muito grande. O tamanho máximo é 10MB.';
      dv.className = "alert alert-danger d-block";
      dv.removeAttribute("hidden");
      return;
    }

    // Desabilita o botão durante o processamento
    btnIdentificar.disabled = true;
    btnIdentificar.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Processando...';

    dv.innerHTML = '<i class="bi bi-hourglass-split"></i> <strong>Processando imagem...</strong><br><small>Isso pode levar alguns segundos. Estamos consultando nossa IA para identificar a planta.</small>';
    dv.className = "alert alert-info d-block";
    dv.removeAttribute("hidden");

    const fd = new FormData();
    fd.append("foto", fi.files[0]);

    fetch("/api/identificar/", { method: "POST", body: fd })
      .then(r => {
        if (!r.ok) {
          if (r.status === 401) {
            throw new Error("Você precisa estar logado para usar esta funcionalidade.");
          } else if (r.status === 500) {
            throw new Error("Erro no servidor. As APIs de identificação podem estar indisponíveis.");
          }
          throw new Error(`Erro HTTP ${r.status}`);
        }
        return r.json();
      })
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          // Limpa o conteúdo anterior
          dv.innerHTML = "";

          // Adiciona título de sucesso
          const successHeader = document.createElement("div");
          successHeader.innerHTML = '<i class="bi bi-check-circle-fill"></i> <strong>Identificação concluída!</strong>';
          successHeader.style.marginBottom = "1rem";
          dv.appendChild(successHeader);

          // Cria elementos DOM de forma segura para cada sugestão
          data.forEach((it, i) => {
            const sugContainer = document.createElement("div");
            sugContainer.style.marginBottom = "1rem";

            const sugTitle = document.createElement("div");
            sugTitle.innerHTML = `<strong class="text-success">🌿 Sugestão ${i + 1}</strong> <small class="text-muted">(Fonte: ${it.fonte || "desconhecida"})</small>`;
            sugContainer.appendChild(sugTitle);

            const detailsDiv = document.createElement("div");
            detailsDiv.style.marginLeft = "1.5rem";
            detailsDiv.style.marginTop = "0.5rem";

            if (it.nome_popular) {
              const popDiv = document.createElement("div");
              popDiv.innerHTML = `<strong>Nome Popular:</strong> ${it.nome_popular}`;
              detailsDiv.appendChild(popDiv);
            }

            if (it.nome_cientifico) {
              const sciDiv = document.createElement("div");
              sciDiv.innerHTML = `<strong>Nome Científico:</strong> <em>${it.nome_cientifico}</em>`;
              detailsDiv.appendChild(sciDiv);
            }

            if (it.score) {
              const confDiv = document.createElement("div");
              const percentage = (it.score * 100).toFixed(1);
              const confClass = percentage >= 70 ? 'text-success' : percentage >= 50 ? 'text-warning' : 'text-danger';
              confDiv.innerHTML = `<strong>Confiança:</strong> <span class="${confClass}">${percentage}%</span>`;
              detailsDiv.appendChild(confDiv);
            }

            sugContainer.appendChild(detailsDiv);

            if (i < data.length - 1) {
              const hr = document.createElement("hr");
              hr.style.margin = "1rem 0";
              sugContainer.appendChild(hr);
            }

            dv.appendChild(sugContainer);
          });

          // Preenche os campos do formulário com animação
          const nomePopularInput = document.getElementById("id_nome_popular");
          const nomeCientificoInput = document.getElementById("id_nome_cientifico");

          if (nomePopularInput && data[0].nome_popular) {
            nomePopularInput.value = data[0].nome_popular;
            nomePopularInput.style.backgroundColor = '#e8f5e9';
            setTimeout(() => {
              nomePopularInput.style.transition = 'background-color 0.8s';
              nomePopularInput.style.backgroundColor = '';
            }, 100);
          }

          if (nomeCientificoInput && data[0].nome_cientifico) {
            nomeCientificoInput.value = data[0].nome_cientifico;
            nomeCientificoInput.style.backgroundColor = '#e8f5e9';
            setTimeout(() => {
              nomeCientificoInput.style.transition = 'background-color 0.8s';
              nomeCientificoInput.style.backgroundColor = '';
            }, 100);
          }

          // Transfere a foto para o campo de foto do ponto
          const fotoInput = document.getElementById("id_foto");
          if (fotoInput && fi.files[0]) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(fi.files[0]);
            fotoInput.files = dataTransfer.files;

            // Atualiza preview se existir
            if (window.previewFoto) {
              window.previewFoto(fi.files[0]);
            }
          }

          dv.className = "alert alert-success d-block";
        } else {
          dv.innerHTML = '<i class="bi bi-x-circle-fill"></i> <strong>Não foi possível identificar a planta.</strong><br><small>Tente com uma foto mais clara ou de outro ângulo. Você também pode preencher os campos manualmente.</small>';
          dv.className = "alert alert-warning d-block";
        }
      })
      .catch((err) => {
        console.error("Erro ao identificar:", err);
        dv.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> <strong>Erro ao identificar:</strong> ${err.message}<br><small>Verifique sua conexão ou tente novamente mais tarde. Você pode preencher os campos manualmente.</small>`;
        dv.className = "alert alert-danger d-block";
      })
      .finally(() => {
        // Reabilita o botão
        btnIdentificar.disabled = false;
        btnIdentificar.innerHTML = '<i class="bi bi-stars"></i> Identificar com IA';
      });
  });
});
