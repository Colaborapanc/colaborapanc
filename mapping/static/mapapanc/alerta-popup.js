/**
 * alerta-popup.js
 * Exibe um alerta flutuante no canto da tela ao carregar a p�gina.
 * Usado para destacar rapidamente riscos clim�ticos ativos para o usu�rio.
 */

window.addEventListener("load", () => {
  // Verifica se o alerta j� foi exibido nesta sess�o para evitar repeti��es
  if (sessionStorage.getItem("alertaClimaticoMostrado") === "true") {
    return;
  }

  // Cria o elemento de alerta de forma segura
  const alerta = document.createElement("div");
  alerta.className = "alerta-popup";

  // Cria conte�do do alerta usando DOM manipulation segura
  const icon = document.createTextNode("⚠️ ");
  const strong = document.createElement("strong");
  strong.textContent = "Alerta:";
  const text = document.createTextNode(" Chuva intensa registrada na sua região!");
  const br = document.createElement("br");
  const small = document.createElement("small");
  small.textContent = "Consulte os detalhes no mapa.";

  alerta.appendChild(icon);
  alerta.appendChild(strong);
  alerta.appendChild(text);
  alerta.appendChild(br);
  alerta.appendChild(small);

  // Aplica o alerta ao corpo do documento
  document.body.appendChild(alerta);

  // Remove o alerta ap�s 10 segundos
  setTimeout(() => {
    alerta.remove();
  }, 10000);

  // Marca que o alerta j� foi mostrado nesta sess�o
  sessionStorage.setItem("alertaClimaticoMostrado", "true");
});
