import asyncio
import omni.kit.ui
import omni.ui as ui
from omni.kit.widget.settings import create_setting_widget, SettingType
from .forma_settings import FormaSettings
from .file_picker_dialog import FilePickerDialogWrapper


WINDOW_NAME = "Forma Live Link"
MENU_PATH = "Window/Forma Link"
SPEED_INV = 300


class FormaSettingsWindow:
    def __init__(self, plugin_ver="0.0.0") -> None:
        self._busy = False

        # controls for UI spacing
        self.plugin_ver = plugin_ver
        self.default_col_width = 200
        self.default_h_spacing = 20
        self.section_v_spacing = 1

        self._settings = FormaSettings()
        self._window = ui.Window(WINDOW_NAME)
        self._window.width = 900
        self._window.height = 300

        self._menu = omni.kit.ui.get_editor_menu().add_item(
            MENU_PATH, self._menu_on_click, toggle=True, value=True
        )

        self._busy_state_track = None
        self._busy_state_label = None

        self._ping_pong_rectangle = None
        self._spacer_left = None
        self._spacer_right = None

        with self._window.frame:
            with ui.CollapsableFrame("Forma Settings - v" + plugin_ver):
                with ui.VStack(spacing=self.section_v_spacing):
                    self._build_settings()

        self._window.set_visibility_changed_fn(self._on_visibility_changed)

        self._window.visible = False
        self._window.deferred_dock_in("Content", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)
        self.busy = False

    def destroy(self):
        self._window.visible = False
        self._window.destroy()
        self._window = None
        # omni.kit.ui.get_editor_menu().remove_item(MENU_PATH)
        self._menu = None

    @property
    def busy(self):
        return self._busy

    @busy.setter
    def busy(self, value):
        if self._busy == value:
            return
        self._busy = value
        self._set_state_busy() if self._busy else self._set_state_idle()

    def _set_state_idle(self):
        self._ping_pong_rectangle.visible = False
        self._busy_state_track.visible = True
        self._busy_state_label.text = "Idle..."
        self._busy_state_track.set_style(
            {
                "border_width": 1.0,
                "background_color": ui.color("#2C2C2C"),
                "border_color": ui.color("#454545"),
            }
        )

    def _set_state_busy(self):
        asyncio.ensure_future(self._ping_pong())
        self._ping_pong_rectangle.visible = True
        self._busy_state_track.visible = True
        self._busy_state_label.text = "Working..."
        self._busy_state_label.set_style({"color": ui.color("#CCCCCC")})
        self._busy_state_track.set_style(
            {
                "border_width": 1.0,
                "background_color": ui.color("#1F2124"),
                "border_color": ui.color("#76b900"),
            }
        )

    def _menu_on_click(self, *args):
        self._window.visible = not self._window.visible
        if self._window.visible:
            self._window.deferred_dock_in(
                "Content", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE
            )

    def _on_visibility_changed(self, visible):
        omni.kit.ui.get_editor_menu().set_value(MENU_PATH, visible)

    def _add_read_only_setting2(
        self,
        name,
        value,
    ):
        with ui.HStack(height=self.default_h_spacing):
            ui.Label(
                name, width=self.default_col_width, alignment=ui.Alignment.LEFT_CENTER
            )
            ui.Label(
                str(value),
                width=self.default_col_width,
                alignment=ui.Alignment.LEFT_CENTER,
            )

    def _add_setting(
        self,
        setting_type: SettingType,
        name,
        path,
        range_from=0,
        range_to=0,
        speed=1,
        has_file_picker=False,
        window_title="",
        tooltip="",
    ):
        with ui.HStack(
            height=self.default_h_spacing,
        ):
            ui.Label(
                name, width=self.default_col_width, alignment=ui.Alignment.LEFT_CENTER
            )
            setting_widget, model = create_setting_widget(
                setting_path=path,
                setting_type=setting_type,
                range_from=range_from,
                range_to=range_to,
                speed=speed,
                tooltip=tooltip,
            )

            if has_file_picker:
                btn_default = ui.Button(
                    style={"image_url": "resources/icons/folder.png"},
                    width=30,
                    tooltip="Select Folder",
                )

                def set_file_path():
                    self._set_file_path(path, window_title)

                btn_default.set_clicked_fn(set_file_path)

                # Button to jump to the file in Content Window
                def locate_file(model):
                    url = model.get_value_as_string()
                    if len(url) == 0:
                        return

                    window = ui.Workspace.get_window("Content")
                    if not window:
                        return
                    if not window.visible:
                        ui.Workspace.show_window(title="Content", show=True)

                    window.focus()
                    asyncio.ensure_future(deferred_navigation(url))

                ui.Button(
                    style={"image_url": "resources/icons/find.png"},
                    width=30,
                    tooltip="Locate Folder",
                    clicked_fn=lambda model=model: locate_file(model),
                )

    def _build_settings(self):
        self._add_read_only_setting2(
            "Link Port", self._settings.get_kit_services_transport_port()
        )
        ui.Line(name="Default", height=20, style={"color": ui.color("#454545")})

        with ui.ZStack(
            height=24,
            tooltip="Shows extension state to let you know when data is being updated and uploaded to Nucleus",
        ):
            self._busy_state_track = ui.Rectangle(
                name="default",
                height=24,
                style={
                    "border_width": 2.0,
                    "background_color": ui.color("#2C2C2C"),
                    "border_color": ui.color("#454545"),
                },
            )
            self._busy_state_label = ui.Label(
                "Idle...",
                style={"color": ui.color("#CCCCCC")},
                alignment=ui.Alignment.CENTER,
            )
            with ui.HStack(height=24):
                self._spacer_left = ui.Spacer(width=ui.Fraction(0))
                self._ping_pong_rectangle = ui.Rectangle(
                    width=36,
                    mouse_pressed_fn=self.mouse_pressed,
                    style={
                        "background_color": ui.color("#76b900"),
                        "border_radius": 0.5,
                    },
                )
                self._spacer_right = ui.Spacer(width=ui.Fraction(1))
            self._ping_pong_rectangle.visible = False

        ui.Spacer()

    def __del__(self):
        pass

    def mouse_pressed(self, *args):
        # Bind this class to the rectangle, so when Rectangle is deleted, the
        # class is deleted as well
        pass

    def _set_file_path(self, path, window_title):
        initial_url = self._settings.get(path)

        def ok_handler(file_url):
            self._settings.set(path, file_url)

        dialog_wrapper = FilePickerDialogWrapper(
            window_title=window_title,
            item_filter_options=[],
            show_file_extensions=[],
            apply_button_label="Select",
            ok_handler=ok_handler,
        )

        dialog_wrapper.show_dialog(initial_url)

    async def _ping_pong(self):
        counter = 0
        while self._busy:
            await omni.kit.app.get_app().next_update_async()

            if not self._busy:
                break

            width = float(counter % SPEED_INV) / SPEED_INV

            width = width * 2
            if width > 1.0:
                width = 2.0 - width

            self._spacer_left.width = ui.Fraction(width)
            self._spacer_right.width = ui.Fraction(1.0 - width)
            counter += 1


async def deferred_navigation(url):
    """
    Makes sure the content browser tree (if availible) is browsed properly when initially hidden.
    This import does not have to be a requirement since this action will be ignored
    """
    try:
        import omni.kit.app

        await omni.kit.app.get_app().next_update_async()
        import omni.kit.window.content_browser

        instance = omni.kit.window.content_browser.get_instance()
        if not instance:
            return
        instance.navigate_to(url)
    except ImportError:
        pass
