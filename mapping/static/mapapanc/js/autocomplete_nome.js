document.addEventListener("DOMContentLoaded", () => {
  const ip = document.getElementById("id_nome_popular");
  const ic = document.getElementById("id_nome_cientifico");
  const dl = document.getElementById("datalist-nome-popular");
  const origemInput = document.getElementById("id_nome_resolucao_origem");
  const statusEl = document.getElementById("nome-autocomplete-status");

  if (!ip || !ic) return;

  let timeoutId = null;
  let suggestionsByPopular = {};
  let autoFilled = false;

  const setStatus = (text = "", variant = "muted") => {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.classList.remove("text-muted", "text-danger", "text-success");
    statusEl.classList.add(
      variant === "error" ? "text-danger" : variant === "success" ? "text-success" : "text-muted"
    );
  };

  const fillScientificFromSelected = () => {
    const selected = suggestionsByPopular[(ip.value || "").trim().toLowerCase()];
    if (selected && selected.nome_cientifico) {
      ic.value = selected.nome_cientifico;
      autoFilled = true;
      if (origemInput) origemInput.value = selected.source || "autocomplete";
      setStatus(`Nome científico preenchido automaticamente (${selected.source || "autocomplete"}).`, "success");
      return true;
    }
    return false;
  };

  const handleNomePopularInput = () => {
    const v = ip.value.trim();
    if (origemInput) origemInput.value = "manual";
    if (fillScientificFromSelected()) return;

    if (timeoutId) clearTimeout(timeoutId);

    if (v.length >= 2) {
      timeoutId = setTimeout(() => {
        setStatus("Buscando sugestões…");
        fetch(`/api/autocomplete-nome/?term=${encodeURIComponent(v)}&detailed=1`)
          .then(r => r.json())
          .then(arr => {
            const normalized = Array.isArray(arr)
              ? arr.map(item => (typeof item === "string" ? { nome_popular: item, nome_cientifico: "", source: "base_local" } : item))
              : [];

            suggestionsByPopular = {};
            if (dl) dl.innerHTML = "";

            normalized.forEach(item => {
              const popular = (item.nome_popular || "").trim();
              if (!popular) return;
              suggestionsByPopular[popular.toLowerCase()] = item;
              if (dl) {
                const option = document.createElement("option");
                option.value = popular;
                if (item.nome_cientifico) option.label = `${popular} — ${item.nome_cientifico}`;
                dl.appendChild(option);
              }
            });

            if (normalized.length === 0) setStatus("Nenhuma sugestão encontrada. Você pode continuar manualmente.");
            else if (!fillScientificFromSelected()) setStatus("Escolha uma sugestão para preencher o nome científico.");
          })
          .catch(err => {
            console.error("Erro no autocomplete:", err);
            setStatus("Não foi possível buscar sugestões agora. Campo segue manual.", "error");
          });
      }, 350);
    } else {
      if (autoFilled) {
        ic.value = "";
        autoFilled = false;
      }
      setStatus("");
      if (dl) dl.innerHTML = "";
    }
  };

  ["input", "change"].forEach(evt => {
    ip.addEventListener(evt, handleNomePopularInput);
  });

  ic.addEventListener("input", () => {
    if ((ic.value || "").trim().length > 0) autoFilled = false;
    if (origemInput && origemInput.value === "manual") return;
    if (origemInput) origemInput.value = "manual";
  });
});
