from acrul_toolkit.custom_resources import CustomResourceEventHandler
import requests


class EventHandler(CustomResourceEventHandler):
    def on_create(self, event):
        self.check_api_endpoint(event)

    def on_update(self, event):
        self.check_api_endpoint(event)

    def on_delete(self, event):
        pass

    @staticmethod
    def check_api_endpoint(event):
        url = event["ResourceProperties"]["health_check_url"]
        tries = 0
        error = None
        while tries < 3:
            response = requests.get(url)
            if response.status_code == 200:
                error = None
                break
            error = f"{response.status_code}: {response.text}"
            tries += 1

        if error is not None:
            raise RuntimeError(f"Check Failed: {error}")


main = EventHandler()
