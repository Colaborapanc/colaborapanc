// mobile/src/services/compartilhamentoService.js
// Serviço para compartilhamento em redes sociais

import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';
import { Platform } from 'react-native';

class CompartilhamentoService {
  /**
   * Compartilha texto simples
   */
  async compartilharTexto(titulo, mensagem, url = null) {
    try {
      const conteudo = url ? `${mensagem}\n\n${url}` : mensagem;

      const disponivel = await Sharing.isAvailableAsync();

      if (disponivel) {
        await Sharing.shareAsync(conteudo, {
          dialogTitle: titulo,
        });
        return true;
      } else {
        console.log('Compartilhamento não disponível');
        return false;
      }
    } catch (error) {
      console.error('Erro ao compartilhar:', error);
      return false;
    }
  }

  /**
   * Compartilha ponto PANC
   */
  async compartilharPonto(ponto) {
    const titulo = `Confira esta PANC no ColaboraPANC!`;
    const mensagem = `🌿 ${ponto.nome_popular}\n\nLocalização: ${ponto.cidade}, ${ponto.estado}\n\nDescubra mais PANCs no ColaboraPANC!`;
    const url = `https://foodlens.com.br/ponto/${ponto.id}`;

    return await this.compartilharTexto(titulo, mensagem, url);
  }

  /**
   * Compartilha conquista/badge
   */
  async compartilharConquista(badge) {
    const titulo = `Nova conquista no ColaboraPANC! 🏆`;
    const mensagem = `Acabei de conquistar a badge "${badge.nome}" no ColaboraPANC! 🎉\n\nJunte-se a mim na descoberta de PANCs!`;
    const url = `https://foodlens.com.br`;

    return await this.compartilharTexto(titulo, mensagem, url);
  }

  /**
   * Compartilha rota
   */
  async compartilharRota(rota) {
    const titulo = `Rota de PANCs no ColaboraPANC`;
    const mensagem = `📍 Rota: ${rota.nome}\n${rota.descricao}\n\n${rota.pontos.length} pontos de PANCs para visitar!\n\nDistância: ${rota.distancia_total} km`;
    const url = `https://foodlens.com.br/rotas/${rota.id}`;

    return await this.compartilharTexto(titulo, mensagem, url);
  }

  /**
   * Compartilha imagem
   */
  async compartilharImagem(imageUri, mensagem = '') {
    try {
      const disponivel = await Sharing.isAvailableAsync();

      if (!disponivel) {
        console.log('Compartilhamento não disponível');
        return false;
      }

      // Se a imagem for remota, baixa primeiro
      let localUri = imageUri;

      if (imageUri.startsWith('http')) {
        const filename = imageUri.split('/').pop();
        const localPath = `${FileSystem.cacheDirectory}${filename}`;

        const download = await FileSystem.downloadAsync(imageUri, localPath);
        localUri = download.uri;
      }

      await Sharing.shareAsync(localUri, {
        mimeType: 'image/jpeg',
        dialogTitle: mensagem || 'Compartilhar imagem',
      });

      return true;
    } catch (error) {
      console.error('Erro ao compartilhar imagem:', error);
      return false;
    }
  }

  /**
   * Compartilha no WhatsApp (se disponível)
   */
  async compartilharWhatsApp(mensagem) {
    try {
      const { Linking } = require('react-native');

      const url = `whatsapp://send?text=${encodeURIComponent(mensagem)}`;

      const suportado = await Linking.canOpenURL(url);

      if (suportado) {
        await Linking.openURL(url);
        return true;
      } else {
        // Fallback para compartilhamento genérico
        return await this.compartilharTexto('Compartilhar', mensagem);
      }
    } catch (error) {
      console.error('Erro ao compartilhar no WhatsApp:', error);
      return false;
    }
  }

  /**
   * Gera link de compartilhamento com UTM
   */
  gerarLinkComUTM(path, source = 'mobile', medium = 'share') {
    const baseUrl = 'https://foodlens.com.br';
    return `${baseUrl}${path}?utm_source=${source}&utm_medium=${medium}&utm_campaign=compartilhamento`;
  }

  /**
   * Compartilha convite para o app
   */
  async compartilharConvite() {
    const titulo = 'Junte-se ao ColaboraPANC!';
    const mensagem = `🌿 Descubra Plantas Alimentícias Não Convencionais perto de você!\n\n📱 Baixe o ColaboraPANC e explore um mundo de biodiversidade comestível!`;
    const url = this.gerarLinkComUTM('/', 'mobile', 'convite');

    return await this.compartilharTexto(titulo, mensagem, url);
  }
}

export default new CompartilhamentoService();
