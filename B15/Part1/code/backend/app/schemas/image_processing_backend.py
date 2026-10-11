from enum import Enum


class ImageProcessingBackend(str, Enum):
    """Enum for supported image processing backends."""

    METASHAPE = "metashape"
    ODM = "odm"
