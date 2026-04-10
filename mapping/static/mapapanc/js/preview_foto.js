// Função global para preview de foto
window.previewFoto = function(file) {
  if (!file) return;

  const reader = new FileReader();
  reader.onload = ev => {
    const preview = document.getElementById("photo-preview");
    if (preview) {
      preview.textContent = ""; // Limpa conteúdo anterior
      const img = document.createElement("img");
      img.src = ev.target.result;
      img.alt = "Prévia da foto";
      img.style.maxWidth = "200px";
      img.style.maxHeight = "200px";
      img.style.borderRadius = "10px";
      img.style.marginTop = "10px";
      preview.appendChild(img);
    }
  };
  reader.readAsDataURL(file);
};

document.addEventListener("DOMContentLoaded", () => {
  const fotoInput = document.getElementById("id_foto");
  if (fotoInput) {
    fotoInput.addEventListener("change", e => {
      const f = e.target.files?.[0];
      if (f) {
        window.previewFoto(f);
      }
    });
  }
});
