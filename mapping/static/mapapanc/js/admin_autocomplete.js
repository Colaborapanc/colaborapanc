document.addEventListener('DOMContentLoaded', function () {
    const nomePopularInput = document.getElementById('id_nome_popular');
    const nomeCientificoInput = document.getElementById('id_nome_cientifico');

    if (nomePopularInput && nomeCientificoInput) {
        nomePopularInput.addEventListener('input', function () {
            const nome = this.value;

            fetch(`/api/nome-cientifico/?nome_popular=${encodeURIComponent(nome)}`)
                .then(response => response.json())
                .then(data => {
                    nomeCientificoInput.value = data.nome_cientifico || '';
                });
        });
    }
});
