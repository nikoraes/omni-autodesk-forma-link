from typing import List, Dict
import pathlib
import pydantic
import os


g_file_browser_protocol_version = "1.0"
g_forma_protocol_version = "1.0"


class FormaRequestBody(pydantic.BaseModel):
    """Data model for the callbacks to adhere to"""

    protocol_version: str = pydantic.Field(
        g_forma_protocol_version, title="Protocol version"
    )
    extension_version: str = pydantic.Field("0.0", title="Extension version")
    execute_command: str = pydantic.Field("", title="Execute Command")
    forma_path: str = pydantic.Field("", title="Forma Path")
    usd_path: str = pydantic.Field(
        "", title="Nucleus folder where resulting USD will be saved"
    )  # default value received from connector should be omniverse://localhost/Projects/Forma
    autosave_stage: bool = pydantic.Field(True, title="Autosave Stage")

    def __str__(self) -> str:
        return (
            f"protocol_version: {self.protocol_version}\n"
            f"execute_command: {self.execute_command}\n"
            f"usd_path: {self.usd_path}\n"
            f"autosave_stage: {self.autosave_stage}\n"
        )


class FormaResponseBody(pydantic.BaseModel):
    """Data model for the callbacks to adhere to"""

    extension_version_is_valid: bool = pydantic.Field(
        ..., title="Indicates if the extension version is valid"
    )
    status: str = pydantic.Field(..., title="Everything is OK")
    succeeded: bool = pydantic.Field(
        True, title="Indicates if the operation succeeded or failed"
    )
    usd_path: str = pydantic.Field("", title="The path of the exported USD file")
    selected_prims: List[str] = pydantic.Field([], title="The currently selected prims")


class FileBrowserRequestBody(pydantic.BaseModel):
    """Data model for the callbacks to adhere to"""

    extension_version: str = pydantic.Field("0.0", title="Extension version")
    protocol_version: str = pydantic.Field(
        g_file_browser_protocol_version, title="Protocol version"
    )
    window_title: str = pydantic.Field(
        "Input Filename or Choose File to Override", title="File browser window title"
    )
    item_filter_options: list = pydantic.Field(
        ["USD Files (*.usd, *.usda, *.usdc, *.usdz)", "All Files (*)"],
        title="Item filter options",
    )
    show_file_extensions: list = pydantic.Field(
        [".usd", ".usda", ".usdc", ".usdz"], title="Extensions to show"
    )
    apply_button_label: str = pydantic.Field("Save", title="Apply button label")
    initial_url: str = pydantic.Field(
        "omniverse://", title="The initial URL to open in the file browser"
    )


class FileBrowserResponseBody(pydantic.BaseModel):
    """Data model for the callbacks to adhere to"""

    extension_version_is_valid: bool = pydantic.Field(
        ..., title="Indicates if the extension version is valid"
    )
    url: str = pydantic.Field(..., title="The export URL")
    options: str = pydantic.Field(..., title="Export options")
    status: str = pydantic.Field(..., title="Everything is OK")
    succeeded: bool = pydantic.Field(
        True, title="Indicates if the operation succeeded or failed"
    )
