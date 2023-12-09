import os
import uuid
import asyncio
import pathlib
import shutil
import numpy as np
from collections import deque, Counter
from fastapi import FastAPI, File, UploadFile, Form
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
    # FormaRequestBody,
    FormaRequestBody,
    FormaResponseBody,
)

g_app = omni.kit.app.get_app()
g_forma_link = None
g_request_manager = None


def get_request_manager():
    """Get the instance of the request manager

    Returns:
        RequestManager: Handles incoming requests from Autodesk Forma
    """
    global g_request_manager
    if g_request_manager is None:
        g_request_manager = RequestManager()

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


class RequestManager:
    """Handles incoming request from Autodesk Forma. Breaks up requests into multiple tasks and adds them
    to a collections.deque that is managed by a callback function.
    """

    def __init__(self) -> None:
        """USD Composer request and task queue"""
        self._request_queue = deque()
        self._task_queue = deque()

    async def add_request(self, request: FormaRequestBody, response: FormaResponseBody):
        """Add task to queue and dishes out the job

        Args:
            request (FormaRequestBody): contains Forma side data command to run etc
            response (FormaResponseBody): response body to send back to Forma

        Returns:
            FormaResponseBody: Modifies (if applicable) and returns response
        """
        request_id = uuid.uuid4().hex
        self._request_queue.append(request_id)
        if not is_busy():
            set_busy()

        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        if not stage:
            return

        if request.execute_command == forma_constants.Commands.IMPORT_MESH:
            # painter_validation.validate_usd(request.usd_geometry_path, log=True)
            # painter_validation.validate_usd(request.usd_materials_path, log=True)

            s = Usd.Stage.Open(request.usd_path)

        return response

    """ if request.usd_geometry_path != usd_paths.root_layer_geometry_path:
                try:
                    painter_core.log(
                        f"Copying {request.usd_geometry_path} to {usd_paths.root_layer_geometry_path}.",
                        severity=painter_data.SEVERITY.INFO,
                    )
                    s = Usd.Stage.Open(request.usd_geometry_path)
                    s.Export(usd_paths.root_layer_geometry_path)
                except OSError:
                    painter_core.log(
                        "Cannot create Stage because USD geometry file failed to copy.",
                        severity=painter_data.SEVERITY.ERROR,
                        notify=True,
                        hide_after_timeout=False,
                    )
                    return """
    """
            # import the mesh
            mesh_task_id = uuid.uuid4().hex
            mesh_queue_id = f"{request_id}_{mesh_task_id}"
            self._task_queue.append(mesh_queue_id)
            await self._request_import_mesh(usd_paths, mesh_queue_id)

            # import the environment map
            if request.use_env_map is True:
                environment_task_id = uuid.uuid4().hex
                environment_queue_id = f'{request_id}_{environment_task_id}'
                self._task_queue.append(environment_queue_id)

                await self._request_import_environment(request, environment_queue_id)

            # usd_material_info = painter_data.UsdMaterials(request)
            # Sets up and kicks off all texture copy actions
            # source_target_textures: dict = painter_utils.get_source_target_textures(request)
            # nucleus_task_data = self._set_up_copy_texture_data(request, usd_material_info.source_target_textures, request_id)

            # material_session_queue_id = self._get_material_queue_id(request_id)
            # material_queue_id = self._get_material_queue_id(request_id)

            # await self._request_update_materials_root_layer(request, usd_material_info, True, material_queue_id)
            await g_app.next_update_async()
            # await self._request_update_materials_session_layer(request, usd_material_info, True, material_session_queue_id)

            # forma_core.save_stage()

            # await self._process_nucleus_task_data(nucleus_task_data)
    """

    async def _request_import_mesh(
        self, usd_paths: forma_data.UsdPaths, mesh_queue_id: str
    ):
        """Mesh from Forma to USD Composer

        Args:
            request (TextureSetUpdatedRequestBody): contains painter side data command to run etc
            mesh_queue_id (str): Composition - {request_id}_{task_id} each id generated with uuid.uuid4().hex
        """
        notification_manager.post_notification(
            f"Opening: {usd_paths.stage_path}\n\nAdding sublayer: {usd_paths.root_layer_geometry_path}",
            hide_after_timeout=False,
        )
        """ def _hide_unused_materials():
            parents = []
            for p in stage.Traverse():
                # usually, the materials are placed in a 'Scope' prim called 'material'
                if p.GetTypeName() == "Material":
                    p.SetActive(False)
                    parent = p.GetParent()
                    if parent.GetName() == painter_constants.PrimPaths.MATERIALS_PRIM_REL_PATH and parent.GetTypeName() == "Scope":
                        if parent not in parents:
                            parents.append(parent)

            for p in parents:
                if p.IsValid():
                    p.SetActive(False) """

        """ def _insert_geometry_sublayer(layer, sublayer_path: str):
            with Usd.EditContext(stage, layer):
                painter_core.insert_sublayer(layer, sublayer_path)
                # omni.kit.commands.execute("MovePrimsCommand", paths_to_move={usd_material_info.root_prim_path : f"{stage.GetDefaultPrim().GetPath().pathString}/Geometry"})
                _hide_unused_materials() """

        """ usd_context = omni.usd.get_context()
        current_stage_url = usd_context.get_stage_url()
        opened = True if current_stage_url == usd_paths.stage_path else False
        if opened:
            carb.log_info(f"Close stage")

        usd_context.close_stage()
        omni.kit.stage_templates.new_stage(template="sunlight")
        await usd_context.save_as_stage_async(usd_paths.stage_path)
        stage = usd_context.get_stage()

        _insert_geometry_sublayer(
            stage.GetRootLayer(), usd_paths.root_layer_geometry_path
        )
        painter_core.frame_prims_by_type(["Mesh"])

        await usd_context.save_as_stage_async(usd_paths.stage_path)
        self.task_callback(mesh_queue_id) """

    def task_callback(self, queue_id: str, result=omni.client.Result.OK):
        """Callback will manage the request queue

        Args:
            queue_id (str): Composition - {request_id}_{task_id} each id generated with uuid.uuid4().hex
            result (str, optional): The result of the task action. Primarily used/gets set by the omnni.client.copy_with_callback function. Defaults to omni.client.Result.OK.
        """
        queue_id_parts = queue_id.split("_")

        try:
            self._task_queue.remove(queue_id)
        except ValueError:
            carb.log_warn(
                f"Error - tried removing from queue, but queue id does not exist - {queue_id}"
            )
            carb.log_warn("The following values are present:")
            for item in self._task_queue:
                carb.log_warn(item)

        request_id = queue_id_parts[0]
        if not self._is_request_id_in_queue(request_id):
            try:
                self._request_queue.remove(request_id)
            except ValueError:
                carb.log_warn(
                    f"Error - tried removing from queue, but request id does not exist - {request_id}"
                )
                carb.log_warn("The following values are present:")
                for item in self._request_queue:
                    carb.log_warn(item)

        if len(self._request_queue) == 0:
            carb.log_info("Request queue is now empty")
            if is_busy():
                set_idle()
        if len(self._task_queue) == 0:
            carb.log_info("Task queue is now empty")
            if is_busy():
                set_idle()

    def _is_request_id_in_queue(self, request_id) -> bool:
        """Check if the given request id is part of the queue (items are {request_id}_{task_id})

        Args:
            request_id (str): Unique request id generated with uuid.uuid4().hex

        Returns:
            bool: True, False weather the request_id exists within the task queue
        """
        for request_task in self._task_queue:
            request_part = request_task.split("_")[0]
            if request_part == request_id:
                return True

        return False

    @property
    def number_of_tasks(self):
        return len(self._task_queue)


# Import mesh Endpoint
import_mesh_router = routers.ServiceAPIRouter(tags=["connector"])


# This function is the service endpoint for the import mesh
@import_mesh_router.post(f"{forma_constants.ServiceEndpoints.IMPORT_MESH}/{{id}}")
async def handle_import_mesh(id: str, file: UploadFile = File(...)):
    # Read the file as bytes
    file_bytes = await file.read()

    # Convert the bytes to a numpy array of type float32
    mesh = np.frombuffer(file_bytes, dtype=np.float32)

    usd_context = omni.usd.get_context()

    stage = usd_context.get_stage()

    prim_path = f"/World/_{id}"

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
    # Process the content as needed
    return {"ok": True}


# File Browser Endpoint
file_browser_router = routers.ServiceAPIRouter(tags=["connector"])


# This function is the service endpoint for the file browser
@file_browser_router.post(forma_constants.ServiceEndpoints.FILE_BROWSER)
async def handle_filebrowser(
    req: FileBrowserRequestBody,
):
    carb.log_info("Start filebrowser service endpoint")

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


# Forma Service Endpoint
forma_router = routers.ServiceAPIRouter(tags=["connector"])


# This function is the service endpoint for the main Forma interaction
@forma_router.post(forma_constants.ServiceEndpoints.FORMA_LINK)
async def handle_forma(
    request: FormaRequestBody,
    service_context=forma_router.get_facility("context"),
):
    carb.log_info("FormaRequestBody: ")
    carb.log_info(f"{request}")

    # validate extension version
    major_minor_version: str = ".".join(g_forma_link.version.split(".")[:-1])
    version_validation = validate_extension_version(
        request.extension_version, major_minor_version
    )
    response = FormaResponseBody.parse_obj(
        {
            "extension_version_is_valid": version_validation.succeeded,
            "status": "Everything is great",
        }
    )

    if version_validation.succeeded is False:
        forma_core.log(
            version_validation.message,
            severity=forma_data.SEVERITY.ERROR,
            hide_after_timeout=False,
            notify=True,
        )
        response.status = version_validation.message
        return response

    request_manager = get_request_manager()
    await request_manager.add_request(request, response)

    return response


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
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        file_browser_router.register_facility("context", self.context)
        main.register_router(file_browser_router)
        forma_router.register_facility("context", self.context)
        main.register_router(forma_router)
        import_mesh_router.register_facility("context", self.context)
        main.register_router(import_mesh_router)

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
        main.deregister_endpoint("post", forma_constants.ServiceEndpoints.FORMA_LINK)
        main.deregister_endpoint("post", forma_constants.ServiceEndpoints.IMPORT_MESH)

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
