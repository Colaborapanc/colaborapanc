from mapping.services.integrations.healthcheck import IntegrationHealthcheckService


class IntegrationHealthService(IntegrationHealthcheckService):
    def check_all(self):
        return self.run()
