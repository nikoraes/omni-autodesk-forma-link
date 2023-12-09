from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem
import omni.ui as ui
import threading


class FilePickerDialogWrapper:
    def __init__(
        self,
        window_title: str,
        item_filter_options: list,
        show_file_extensions: list,
        apply_button_label: str,
    ) -> None:
        self.window_title = window_title
        self.item_filter_options = item_filter_options
        self.show_file_extensions = show_file_extensions
        self.apply_button_label = apply_button_label
        self.wait_event = threading.Event()
        self.wait_event.clear()
        self.file_url = ""

        self.dialog = FilePickerDialog(
            self.window_title,
            apply_button_label=self.apply_button_label,
            click_apply_handler=lambda filename, dirname: self._on_click_open(
                self.dialog, filename, dirname
            ),
            click_cancel_handler=lambda filename, dirname: self._on_click_cancel(
                self.dialog, filename, dirname
            ),
            item_filter_options=self.item_filter_options,
            item_filter_fn=lambda item: self._on_filter_item(self.dialog, item),
            options_pane_build_fn=self._options_pane_build_fn,
        )
        self.dialog.hide()

    def _options_pane_build_fn(self, selected_items):
        with ui.CollapsableFrame("Reference Options"):
            with ui.HStack(height=0, spacing=2):
                ui.Label("Prim Path", width=0)
        return True

    def _on_filter_item(self, dialog: FilePickerDialog, item: FileBrowserItem) -> bool:
        if not item or item.is_folder:
            return True

        return False

    def _on_click_cancel(self, dialog: FilePickerDialog, filename: str, dirname: str):
        dialog.hide()
        self.file_url = ""
        self.wait_event.set()

    def _on_click_open(self, dialog: FilePickerDialog, filename: str, dirname: str):
        # Normally, you'd want to hide the dialog
        dialog.hide()
        self.file_url = dirname + filename
        self.wait_event.set()

    def show_dialog(self, url: str):
        # Display dialog at pre-determined path
        self.dialog.show(path=url)
