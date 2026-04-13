# mapping/services/push_notifications.py
# Serviço para envio de notificações push via Firebase Cloud Messaging

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Flag para verificar se Firebase está disponível
FIREBASE_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    logger.warning("firebase-admin não está instalado. Notificações push desabilitadas.")


class PushNotificationService:
    """
    Serviço para envio de notificações push
    """

    def __init__(self):
        self.firebase_initialized = False
        if FIREBASE_AVAILABLE:
            self._initialize_firebase()

    def _initialize_firebase(self):
        """Inicializa o Firebase Admin SDK"""
        try:
            # Verifica se já foi inicializado
            if firebase_admin._apps:
                self.firebase_initialized = True
                return

            # Caminho para o arquivo de credenciais
            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')

            if not cred_path or not os.path.exists(cred_path):
                logger.warning(
                    "FIREBASE_CREDENTIALS_PATH não configurado ou arquivo não encontrado. "
                    "Notificações push desabilitadas."
                )
                return

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            self.firebase_initialized = True
            logger.info("Firebase Admin SDK inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase: {e}")
            self.firebase_initialized = False

    def enviar_notificacao(
        self,
        token: str,
        titulo: str,
        corpo: str,
        dados: Dict[str, Any] = None
    ) -> bool:
        """
        Envia notificação push para um único dispositivo

        Args:
            token: Token FCM do dispositivo
            titulo: Título da notificação
            corpo: Corpo da mensagem
            dados: Dados adicionais (opcional)

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.firebase_initialized:
            logger.warning("Firebase não inicializado. Notificação não enviada.")
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=corpo,
                ),
                data=dados or {},
                token=token,
            )

            response = messaging.send(message)
            logger.info(f"Notificação enviada com sucesso: {response}")
            return True

        except messaging.UnregisteredError:
            logger.warning(f"Token inválido ou não registrado: {token}")
            return False

        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
            return False

    def enviar_multiplas_notificacoes(
        self,
        tokens: List[str],
        titulo: str,
        corpo: str,
        dados: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Envia notificações push para múltiplos dispositivos

        Args:
            tokens: Lista de tokens FCM
            titulo: Título da notificação
            corpo: Corpo da mensagem
            dados: Dados adicionais (opcional)

        Returns:
            dict: Estatísticas de envio
        """
        if not self.firebase_initialized:
            logger.warning("Firebase não inicializado. Notificações não enviadas.")
            return {'success': 0, 'failure': len(tokens)}

        if not tokens:
            return {'success': 0, 'failure': 0}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=titulo,
                    body=corpo,
                ),
                data=dados or {},
                tokens=tokens,
            )

            response = messaging.send_multicast(message)

            logger.info(
                f"Notificações enviadas: {response.success_count} sucesso, "
                f"{response.failure_count} falhas"
            )

            return {
                'success': response.success_count,
                'failure': response.failure_count,
                'responses': response.responses
            }

        except Exception as e:
            logger.error(f"Erro ao enviar notificações múltiplas: {e}")
            return {'success': 0, 'failure': len(tokens)}

    def enviar_por_topico(
        self,
        topico: str,
        titulo: str,
        corpo: str,
        dados: Dict[str, Any] = None
    ) -> bool:
        """
        Envia notificação para um tópico (todos os inscritos)

        Args:
            topico: Nome do tópico
            titulo: Título da notificação
            corpo: Corpo da mensagem
            dados: Dados adicionais (opcional)

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.firebase_initialized:
            logger.warning("Firebase não inicializado. Notificação não enviada.")
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=corpo,
                ),
                data=dados or {},
                topic=topico,
            )

            response = messaging.send(message)
            logger.info(f"Notificação enviada para tópico '{topico}': {response}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificação para tópico: {e}")
            return False

    def inscrever_no_topico(self, tokens: List[str], topico: str) -> bool:
        """
        Inscreve dispositivos em um tópico

        Args:
            tokens: Lista de tokens FCM
            topico: Nome do tópico

        Returns:
            bool: True se inscrito com sucesso
        """
        if not self.firebase_initialized:
            return False

        try:
            response = messaging.subscribe_to_topic(tokens, topico)
            logger.info(f"Dispositivos inscritos no tópico '{topico}': {response.success_count}")
            return response.success_count > 0

        except Exception as e:
            logger.error(f"Erro ao inscrever no tópico: {e}")
            return False

    def desinscrever_do_topico(self, tokens: List[str], topico: str) -> bool:
        """
        Desinscreve dispositivos de um tópico

        Args:
            tokens: Lista de tokens FCM
            topico: Nome do tópico

        Returns:
            bool: True se desinscrito com sucesso
        """
        if not self.firebase_initialized:
            return False

        try:
            response = messaging.unsubscribe_from_topic(tokens, topico)
            logger.info(f"Dispositivos desinscritos do tópico '{topico}': {response.success_count}")
            return response.success_count > 0

        except Exception as e:
            logger.error(f"Erro ao desinscrever do tópico: {e}")
            return False


# Instância global do serviço
push_service = PushNotificationService()


# ===================================
# FUNÇÕES AUXILIARES
# ===================================
def enviar_notificacao_usuario(usuario, tipo, titulo, mensagem, link=None, dados_extra=None):
    """
    Cria notificação in-app e envia push notification para um usuário

    Args:
        usuario: Objeto User
        tipo: Tipo da notificação
        titulo: Título
        mensagem: Mensagem
        link: Link opcional
        dados_extra: Dados extras opcionais
    """
    from mapping.models import Notificacao, DispositivoPush, PreferenciasUsuario

    # Cria notificação in-app
    notificacao = Notificacao.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        link=link or '',
        dados_extra=dados_extra
    )

    # Verifica preferências do usuário
    try:
        preferencias = PreferenciasUsuario.objects.get(usuario=usuario)
        if not preferencias.notif_push:
            return notificacao
    except PreferenciasUsuario.DoesNotExist:
        pass

    # Envia push notification para dispositivos ativos
    dispositivos = DispositivoPush.objects.filter(
        usuario=usuario,
        ativo=True
    )

    if dispositivos.exists():
        tokens = list(dispositivos.values_list('token', flat=True))
        push_service.enviar_multiplas_notificacoes(
            tokens=tokens,
            titulo=titulo,
            corpo=mensagem,
            dados={
                'tipo': tipo,
                'link': link or '',
                'notificacao_id': str(notificacao.id)
            }
        )
        notificacao.enviada_push = True
        notificacao.save()

    return notificacao


def enviar_notificacao_multiplos_usuarios(usuarios, tipo, titulo, mensagem, link=None):
    """
    Envia notificações para múltiplos usuários

    Args:
        usuarios: QuerySet ou lista de usuários
        tipo: Tipo da notificação
        titulo: Título
        mensagem: Mensagem
        link: Link opcional
    """
    for usuario in usuarios:
        enviar_notificacao_usuario(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            link=link
        )
