import tempfile
from pathlib import Path
from typing import List, Optional

import laspy as lp
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np


def create_preview_image(
    input_las_path: Path, preview_out_path: Path, point_limit: int = 1_000_000
) -> None:
    """Generates preview image for point cloud data products using streaming to reduce memory usage.

    Args:
        input_las_path (Path): Path to input las/laz dataset.
        preview_out_path (str): Path for final preview image.
        point_limit (int): Maximum number of points to use in the preview.
    """
    # Open the file in streaming mode
    with lp.open(input_las_path) as input_las:
        # Get total number of points from header
        total_points = input_las.header.point_count

        # Adjust point limit if it's larger than total points
        if point_limit > total_points:
            point_limit = total_points - 1

        # Calculate sampling ratio
        if total_points > point_limit:
            ratio = np.round(total_points / point_limit)
            # Create a mask for the first chunk to determine if we need color
            first_chunk = input_las.read_points(min(1000, total_points))
            try:
                exist_color = len(np.unique(first_chunk.red)) > 1
            except:
                exist_color = False
        else:
            ratio = 1
            first_chunk = input_las.read_points(total_points)
            try:
                exist_color = len(np.unique(first_chunk.red)) > 1
            except:
                exist_color = False

        # Initialize arrays to store sampled points
        point_x: List[float] = []
        point_y: List[float] = []
        point_z: List[float] = []
        point_colors: Optional[List[np.ndarray]] = [] if exist_color else None

        # Read points in chunks
        chunk_size = 100000
        points_collected = 0

        for i in range(0, total_points, chunk_size):
            # Stop if we've collected enough points
            if points_collected >= point_limit:
                break

            # Calculate how many points we can still collect
            remaining_points = point_limit - points_collected
            current_chunk_size = min(chunk_size, total_points - i, remaining_points)

            chunk = input_las.read_points(current_chunk_size)

            # Always use sampling logic, with ratio=1 when no sampling needed
            mask = (np.arange(len(chunk)) % ratio) == 0
            point_x.extend(chunk.x[mask])
            point_y.extend(chunk.y[mask])
            point_z.extend(chunk.z[mask])
            if exist_color and point_colors is not None:
                point_colors.extend(
                    np.stack(
                        (chunk.red[mask], chunk.green[mask], chunk.blue[mask]),
                        axis=1,
                    )
                )
            points_collected += len(chunk.x[mask])

        # Convert to numpy arrays
        point_x_array = np.array(point_x)
        point_y_array = np.array(point_y)
        point_z_array = np.array(point_z)
        if exist_color:
            point_colors_array = np.array(point_colors)

        if len(point_x_array) == 0:
            raise ValueError("No points were collected from the point cloud file")

        # Calculate bounds
        x1 = float(np.min(point_x_array))
        x2 = float(np.max(point_x_array))
        y1 = float(np.min(point_y_array))
        y2 = float(np.max(point_y_array))
        z1 = float(np.min(point_z_array))
        z2 = float(np.max(point_z_array))

        # Create the plot
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        if exist_color:
            ax.scatter(
                point_x_array,
                point_y_array,
                point_z_array,
                c=point_colors_array / (2**16),
                s=0.01,  # type: ignore
            )
        else:
            ax.scatter(
                point_x_array,
                point_y_array,
                point_z_array,
                c=point_z_array,
                cmap="coolwarm",
                s=0.01,  # type: ignore
            )

        ax.margins(x=0, tight=True)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1, y2)
        ax.set_zlim(z1, z2)  # type: ignore
        ax.set_aspect("equal")
        plt.axis("off")

        # save initial figure to temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            plt.savefig(
                tmp_file.name, transparent=True, bbox_inches="tight", dpi=200
            )  # generate image with margins
            plt.close("all")

            # region - Reduce the margins
            img = mpimg.imread(tmp_file.name)
            tmp_x, tmp_y = np.where(img[:, :, -1] != 0)
            x1 = int(np.min(tmp_x) - 10)
            x2 = int(np.max(tmp_x) + 10)
            if x1 < 0:
                x1 = 0
            if x2 > img.shape[1]:
                x2 = img.shape[1]
            y1 = int(np.min(tmp_y) - 10)
            y2 = int(np.max(tmp_y) + 10)
            if y1 < 0:
                y1 = 0
            if y2 > img.shape[0]:
                y2 = img.shape[0]
            plt.imshow(img[x1:x2, y1:y2, :])  # type: ignore
            plt.axis("off")
            plt.savefig(
                preview_out_path, transparent=True, bbox_inches="tight", dpi=200
            )
            plt.close("all")

            # clean up the temporary file
            Path(tmp_file.name).unlink()
