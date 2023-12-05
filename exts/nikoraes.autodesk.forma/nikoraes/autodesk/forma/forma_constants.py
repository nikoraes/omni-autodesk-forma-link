import carb.tokens

UDIM_TAG = ".<UDIM>."
DOCUMENTS_DIR = f"{carb.tokens.get_tokens_interface().resolve('${omni_documents}')}/Omniverse/Autodesk/Forma"
STAGE_SUFFIX = "_stage"


class Commands(object):
    IMPORT_MESH = "importmesh"
    EXPORT_MESH = "exportmesh"


class Layers(object):
    SESSION = "Session"
    ROOT = "Root"
    ANON_SESSION_SUBLAYER = "FormaLinkLocalFileReferences"


class ServiceEndpoints(object):
    FILE_BROWSER = "/kit/formaconnector/filebrowser"
    FORMA_LINK = "/kit/formaconnector/link"
