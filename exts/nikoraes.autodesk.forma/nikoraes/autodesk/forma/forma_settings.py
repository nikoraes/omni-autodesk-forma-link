import carb.settings


'''
This class is intended to put all carb.setting responsibilities and specific strings
in one place.
'''
class FormaSettings:
    def __init__(self) -> None:
        self._settings = carb.settings.get_settings()
        self._settingsPath = "/persistent/exts/nikoraes.autodesk.importer/"

    def get_kit_services_transport_port(self) -> int:
        return self._settings.get_as_int("exts/omni.services.transport.server.http/port")

    def get(self, path):
        return self._settings.get(path)

    def set(self, path, value):
        return self._settings.set(path, value)