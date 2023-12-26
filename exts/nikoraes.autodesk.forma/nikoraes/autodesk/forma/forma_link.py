import os
import uuid
import asyncio
import pathlib
import shutil
import numpy as np
from collections import deque, Counter
from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import omni.client
import omni.ext
import omni.kit.ui
import omni.kit.commands
import omni.kit.notification_manager as notification_manager
import omni.kit.stage_templates
import omni.ui as ui
import omni.ext
import carb
from omni.services.core import main, routers
from pxr import Gf, Usd, UsdGeom
from . import (
    file_picker_dialog,
    forma_core,
    forma_constants,
    forma_data,
)
from .forma_settings import FormaSettings
from .forma_settings_window import FormaSettingsWindow
from .forma_request_bodies import (
    FileBrowserRequestBody,
    FileBrowserResponseBody,
    FormaRequestBody,
    FormaResponseBody,
)
from .utils import nucleus_file_exists

g_app = omni.kit.app.get_app()
g_forma_link = None
g_request_manager = None


def get_request_manager():
    """Get the instance of the request manager"""

    return g_request_manager


def _get_forma_link_instance():
    """Get the instance of the painter link to manage the busy state widget

    Returns:
        PainterLinkExtension: The extension that contains the settings window
    """
    global g_forma_link
    return g_forma_link


def set_idle():
    """Sets the busy widget to idle"""
    _get_forma_link_instance()._set_idle()


def set_busy():
    """Sets the busy widget to busy"""
    _get_forma_link_instance()._set_busy()


def is_busy():
    """Check if busy widget is busy"""
    return _get_forma_link_instance().busy


def validate_extension_version(
    requested_version: str, current_version: str
) -> forma_data.Validation:
    """ """
    if not bool(
        float(requested_version)
    ):  # an older version of the Connector is being used that does not send the required extension version
        return forma_data.Validation(
            f"Please update the Autodesk Forma Omniverse Connector to version {current_version}",
            False,
        )

    if requested_version != current_version:
        return forma_data.Validation(
            f"Version {requested_version} of the Omniverse Autodesk Forma Link extension is required for this connector, but version {current_version} is installed.",
            False,
        )

    return forma_data.Validation("Extension version is correct.", True)


# Import mesh Endpoint
import_mesh_router = routers.ServiceAPIRouter(tags=["connector"])


# This function is the service endpoint for the import mesh
@import_mesh_router.post(f"{forma_constants.ServiceEndpoints.IMPORT_MESH}")
async def handle_import_mesh(
    base: FormaRequestBody = Depends(), file: UploadFile = File(...)
):
    carb.log_info("Import mesh")

    forma_path = base.forma_path

    # Read the file as bytes
    file_bytes = await file.read()

    # Convert the bytes to a numpy array of type float32
    mesh = np.frombuffer(file_bytes, dtype=np.float32)

    usd_context = omni.usd.get_context()
    stage = usd_context.get_stage()
    current_stage_url = usd_context.get_stage_url()
    # if current stage url is the same, add a sublayer to the session layer and use that
    # else try to find the stage. If it doesn't exist create it
    if not nucleus_file_exists(base.usd_path):
        # Create a new stage
        stage = Usd.Stage.CreateNew(base.usd_path)
    else:
        # Open the existing stage
        stage = Usd.Stage.Open(base.usd_path)

    # TODO: Check if the selected USD path is the same as the current stage path
    # If so, just continue
    # If not, we need to add the new USD file to a sublayer of the current stage
    # As the up axis will be Z, we will need to set this on that layer/stage

    if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.z:
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    prim_path = f"/World/_{forma_path.split('/')[-1]}"

    # Define a Mesh primitive on the stage
    mesh_prim = UsdGeom.Mesh.Define(stage, prim_path)

    vertices = mesh.reshape((-1, 3))

    # Set the 'points' attribute using your vertex coordinates
    # You need to convert your numpy array to a list of Gf.Vec3f objects
    points = [
        Gf.Vec3f(vertices[i][0].item(), vertices[i][1].item(), vertices[i][2].item())
        for i in range(len(vertices))
    ]
    mesh_prim.CreatePointsAttr(points)

    # Set the 'faceVertexCounts' attribute
    # This is a list where each element is the number of vertices in a face
    # For a mesh of triangles, each face has 3 vertices
    faceVertexCounts = [3 for _ in range(len(points) // 3)]
    mesh_prim.CreateFaceVertexCountsAttr(faceVertexCounts)

    # Set the 'faceVertexIndices' attribute
    # This is a list where each group of three integers represents a triangle
    # The integers are indices into the 'points' list
    faceVertexIndices = [i for i in range(len(points))]
    mesh_prim.CreateFaceVertexIndicesAttr(faceVertexIndices)

    # Save the stage to a USD file
    stage.Save()

    return {"ok": True}


# Delete mesh Endpoint
delete_mesh_router = routers.ServiceAPIRouter(tags=["connector"])


# This function is the service endpoint for the import mesh
@delete_mesh_router.post(f"{forma_constants.ServiceEndpoints.DELETE_MESH}")
async def handle_delete_mesh(
    req: FormaRequestBody,
):
    carb.log_info("Delete mesh")

    usd_context = omni.usd.get_context()
    stage = usd_context.get_stage()

    forma_path = req.forma_path
    prim_path = f"/World/_{forma_path.split('/')[-1]}"
    stage.RemovePrim(prim_path)

    # Save the stage to a USD file
    stage.Save()

    return {"ok": True}


# File Browser Endpoint
file_browser_router = routers.ServiceAPIRouter(tags=["connector"])


# This function is the service endpoint for the file browser
@file_browser_router.post(forma_constants.ServiceEndpoints.FILE_BROWSER)
async def handle_filebrowser(
    req: FileBrowserRequestBody,
):
    carb.log_info("Start filebrowser")

    # validate extension version
    major_minor_version: str = ".".join(g_forma_link.version.split(".")[:-1])
    ext_version_validation = validate_extension_version(
        req.extension_version, major_minor_version
    )
    response = FileBrowserResponseBody.parse_obj(
        {
            "extension_version_is_valid": ext_version_validation.succeeded,
            "url": "",
            "options": "None Selected",
            "status": "OK",
            "succeeded": ext_version_validation.succeeded,
        }
    )
    if ext_version_validation.succeeded is False:
        forma_core.log(
            ext_version_validation.message,
            severity=forma_data.SEVERITY.ERROR,
            hide_after_timeout=False,
            notify=True,
        )
        response.status = ext_version_validation.message
        response.succeeded = ext_version_validation.succeeded
        return response

    dialog_wrapper = file_picker_dialog.FilePickerDialogWrapper(
        window_title=req.window_title,
        item_filter_options=req.item_filter_options,
        show_file_extensions=req.show_file_extensions,
        apply_button_label="Select",
    )

    dialog_wrapper.show_dialog(req.initial_url)
    await omni.kit.app.get_app().next_update_async()
    await omni.kit.app.get_app().next_update_async()
    while not dialog_wrapper.wait_event.is_set():
        await asyncio.sleep(1)

    dialog_wrapper.wait_event.clear()

    return FileBrowserResponseBody.parse_obj(
        {
            "extension_version_is_valid": ext_version_validation.succeeded,
            "url": dialog_wrapper.file_url,
            "options": "None Selected",
            "status": "OK",
            "succeeded": True,
        }
    )


class ConnectorServiceContext:
    def __init__(self) -> None:
        self.nothing = None


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class FormaLinkExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        ext, version = ext_id.split("-")
        print(f"[{ext}] FormaLinkExtension startup")

        global g_forma_link
        g_forma_link = self

        self.__version = version

        self._settings = FormaSettings()
        print(
            f"[{ext}] APIs are up at {self._settings.get_kit_services_transport_port()}"
        )

        self._settings_window = FormaSettingsWindow(str(self.__version))
        # Context for the service and dialog callbacks (currently unused)
        self.context = ConnectorServiceContext()

        main.get_app().add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:8081",
                "https://app.autodeskforma.com",
                "https://app.autodeskforma.eu",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        file_browser_router.register_facility("context", self.context)
        main.register_router(file_browser_router)
        import_mesh_router.register_facility("context", self.context)
        main.register_router(import_mesh_router)
        delete_mesh_router.register_facility("context", self.context)
        main.register_router(delete_mesh_router)

        print(
            f"[{ext}] APIs are up at {self._settings.get_kit_services_transport_port()}"
        )

    def on_shutdown(self):
        global g_forma_link
        g_forma_link = None

        # For now let's not clean anything out
        # global g_local_texture_root_folder
        # if g_local_texture_root_folder is not None:
        #    clean_texture_folders(g_local_texture_root_folder, remove_all=True)

        print("[nikoraes.autodesk.forma] FormaLinkExtension shutdown")
        """ if self._settings_window:
            self._settings_window.destroy()
            self._settings_window = None """

        main.deregister_endpoint("post", forma_constants.ServiceEndpoints.FILE_BROWSER)
        main.deregister_endpoint("post", forma_constants.ServiceEndpoints.IMPORT_MESH)
        main.deregister_endpoint("post", forma_constants.ServiceEndpoints.DELETE_MESH)

    def _set_busy(self):
        self._settings_window.busy = True

    def _set_idle(self):
        self._settings_window.busy = False

    @property
    def busy(self):
        return self._settings_window.busy

    @property
    def version(self) -> str:
        return self.__version
