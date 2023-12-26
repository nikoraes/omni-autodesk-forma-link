import os
import pathlib
import shutil
from collections import namedtuple
from typing import List, Dict, Callable

import omni.client
import omni.kit.commands
import omni.kit.notification_manager as notification_manager
from pxr import Usd, UsdShade, Sdf

import carb


def nucleus_file_exists(file_path: str) -> bool:
    p = pathlib.Path(file_path)
    filename = p.name

    for entry in omni.client.list(os.path.dirname(file_path))[1]:
        if entry.relative_path == filename:
            return True

    return False
