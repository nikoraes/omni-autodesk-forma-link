import carb.tokens

UDIM_TAG = ".<UDIM>."
STAGE_SUFFIX = "_stage"


class Commands(object):
    IMPORT_MESH = "importmesh"
    EXPORT_MESH = "exportmesh"


class Layers(object):
    SESSION = "Session"
    ROOT = "Root"


class ServiceEndpoints(object):
    FILE_BROWSER = "/kit/formaconnector/filebrowser"
    IMPORT_MESH = "/kit/formaconnector/importmesh"
    DELETE_MESH = "/kit/formaconnector/deletemesh"
