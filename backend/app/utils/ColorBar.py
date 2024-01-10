import base64
import logging
import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl

logger = logging.getLogger("__name__")


class ColorBar:
    def __init__(
        self,
        cmin: int | float,
        cmax: int | float,
        outpath: str,
        cmap: str = "Spectral",
        orientation: str = "vertical",
    ):
        self.logger = logger

        self.cmin = cmin
        self.cmax = cmax
        self.cmap = cmap
        self.orientation = orientation
        self.outdir = Path(outpath)

        if type(self.cmin) is not int and type(self.cmin) is not float:
            raise TypeError("cmin must be integer or float")

        if type(self.cmax) is not int and type(self.cmax) is not float:
            raise TypeError("cmax must be integer or float")

        if self.cmin > self.cmax:
            raise ValueError("cmin value cannot be greater than cmax value")

        if self.orientation != "horizontal" and self.orientation != "vertical":
            raise ValueError("orientation must be 'horizontal' or 'vertical'")

        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        self.outfilename = create_outfilename(self.cmin, self.cmax, self.cmap)

    def generate_colorbar(self) -> Path | None:
        out_fullpath = self.outdir / self.outfilename
        if os.path.exists(out_fullpath):
            return out_fullpath

        if self.orientation == "vertical":
            figsize = (1, 4)
        else:
            figsize = (4, 1)

        fig, ax = plt.subplots(figsize=figsize, layout="constrained")

        norm = mpl.colors.Normalize(vmin=self.cmin, vmax=self.cmax)

        fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=get_cmap(self.cmap)),
            cax=ax,
            orientation=self.orientation,
        )
        plt.savefig(out_fullpath, format="png", transparent=True)

        return out_fullpath


def create_outfilename(cmin, cmax, cmap) -> str:
    filename = base64.b64encode(f"{cmap}_{cmin}_{cmax}".encode("utf-8")).decode("utf-8")
    return filename + ".png"


def get_cmap(cmap: str) -> mpl.colors.LinearSegmentedColormap:
    mpl_colormaps_lower = [mpl_cm.lower() for mpl_cm in list(mpl.colormaps)]
    try:
        mpl_colormap_name = list(mpl.colormaps)[mpl_colormaps_lower.index(cmap.lower())]
        mpl_colormap = mpl.colormaps[mpl_colormap_name]
    except ValueError:
        logger.warning("unrecognized color map name provided")
        raise ValueError("unrecognized color map name provided")
    finally:
        return mpl_colormap
