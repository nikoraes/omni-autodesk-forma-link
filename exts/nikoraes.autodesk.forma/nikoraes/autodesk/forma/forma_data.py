import os
from .forma_constants import STAGE_SUFFIX


class SEVERITY(object):
    INFO = 0
    WARNING = 1
    ERROR = 2


class UsdPaths(object):
    def __init__(self, request) -> None:
        stage_name = f"{request.mesh_name}{STAGE_SUFFIX}.{request.mesh_file_format}"
        stage_local_path = f"{request.local_export_folder}/{stage_name}".replace(
            "\\", "/"
        )

        self._usd_geometry_path = f"{os.path.dirname(stage_local_path)}/{os.path.basename(request.usd_geometry_path).replace('.geo.usd', '.geometry.usd')}"

        if request.nucleus_folder:
            self._stage_path = f"{request.nucleus_folder}/{stage_name}"
            self._root_layer_geometry_path = (
                f"{request.nucleus_folder}/{os.path.basename(self._usd_geometry_path)}"
            )

        else:
            self._stage_path = stage_local_path
            self._root_layer_geometry_path = self._usd_geometry_path

    @property
    def stage_path(self) -> str:
        return self._stage_path

    @property
    def root_layer_geometry_path(self) -> str:
        return self._root_layer_geometry_path

    @property
    def usd_geometry_path(self) -> str:
        return self._usd_geometry_path


class Validation(object):
    def __init__(self, message: str = "", succeeded: bool = True):
        self.message = message
        self.succeeded = succeeded
