import glob
import os
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.deps import get_db
from app.core.celery_app import celery_app
from app.utils.ImageProcessor import ImageProcessor
from app.utils.toolbox.ndvi import run as ndvi_run

logger = get_task_logger(__name__)


AVAILABLE_TOOLS = {"exg": ndvi_run, "ndvi": ndvi_run}


class Toolbox:
    def __init__(self, in_raster: str, out_raster: str) -> None:
        """Toolbox for running processing scripts on raster data products.

        Args:
            in_raster (str): Path to input raster
            out_raster (str): Path for output rasater

        Raises:
            ValueError: Raise if input raster does not exist
            ValueError: Raise if output raster already exists
        """
        self.in_raster = in_raster
        self.out_raster = out_raster

        self.ip = None

        if not os.path.exists(in_raster):
            raise ValueError("Input raster does not exist")

        if os.path.exists(out_raster):
            raise ValueError("Output raster already exists")

    def run(self, name: str, params) -> tuple[str, ImageProcessor]:
        """Run processing tool.

        Args:
            name (str): Name of processing tool
            params (_type_): Input parameters for processing tool

        Raises:
            ValueError: Raise if tool name not matched with tool function
            e: Raise if unexpected error occurs while running processing tool

        Returns:
            tuple[str, ImageProcessor]: Output file path and image processing object
        """
        # find tool function
        if name not in AVAILABLE_TOOLS:
            raise ValueError("Invalid tool name")
        tool_fn = AVAILABLE_TOOLS.get(name)

        # create temp directory and run tool
        in_raster = Path(self.in_raster)
        out_raster = Path(self.out_raster)
        with tempfile.TemporaryDirectory(dir=str(in_raster.parent)) as tmpdir:
            tmp_out_raster = os.path.join(tmpdir, out_raster.name)
            try:
                tool_fn(self.in_raster, tmp_out_raster, params)
                if not os.path.exists(tmp_out_raster):
                    raise
            except Exception as e:
                logger.exception(f"{name.upper()} processing tool failed")
                raise e
            # convert output raster from tool to COG
            self.convert_result_to_cog(
                tmp_out_raster, output_dir=str(out_raster.parent)
            )

        return self.out_raster, self.ip

    def convert_result_to_cog(self, tmp_out_raster: str, output_dir: str) -> None:
        """Convert output from processing tool to COG layout.

        Args:
            tmp_out_raster (str): Output from processing tool
            output_dir (str): Location for COG output

        Raises:
            e: Raise exception if image processor fails
        """
        try:
            self.ip = ImageProcessor(tmp_out_raster, output_dir=output_dir)
            self.ip.run()
        except Exception as e:
            logger.exception("Failed to process output raster")
            raise e
