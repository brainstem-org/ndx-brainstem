from importlib.resources import files

import ndx_anatomical_localization  # noqa: F401  (namespace included by ndx-brainstem)
from pynwb import load_namespaces, get_class

# Get path to the namespace.yaml file with the expected location when installed not in editable mode
__location_of_this_file = files(__name__)
__spec_path = __location_of_this_file / "spec" / "ndx-brainstem.namespace.yaml"

# If that path does not exist, we are likely running in editable mode. Use the local path instead
if not __spec_path.exists():
    __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-brainstem.namespace.yaml"

# Load the namespace
load_namespaces(str(__spec_path))

BrainstemTable = get_class("BrainstemTable", "ndx-brainstem")
BrainstemSchemaTable = get_class("BrainstemSchemaTable", "ndx-brainstem")
BrainstemMetadata = get_class("BrainstemMetadata", "ndx-brainstem")

__all__ = [
    "BrainstemMetadata",
    "BrainstemSchemaTable",
    "BrainstemTable",
]

# Remove these functions/modules from the package
del load_namespaces, get_class, files, __location_of_this_file, __spec_path
