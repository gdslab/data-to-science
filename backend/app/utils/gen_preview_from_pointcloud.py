import io
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import laspy as lp
import numpy as np


def create_preview_image(input_las_path: Path, preview_out_path: Path) -> None:
    """Generates preview image for point cloud data products.

    Args:
        input_las_path (Path): Path to input las/laz dataset.
        preview_out_path (str): Path for final preview image.
    """
    input_las = lp.read(input_las_path)
    # input_las = lp.read('/home/minyj/Downloads/231028_PUSH_L1_40m_5ms_lin_70.las')

    # reduce the number of points

    idx_preview = (np.arange(len(input_las.x)) % 10) == 0
    # '''may need to reduce number of point in consideration of computing resources capacity'''

    point_x = input_las.x[idx_preview]
    point_y = input_las.y[idx_preview]
    point_z = input_las.z[idx_preview]

    x1 = np.min(point_x)
    x2 = np.max(point_x)
    y1 = np.min(point_y)
    y2 = np.max(point_y)
    z1 = np.min(point_z)
    z2 = np.max(point_z)

    # check color information
    try:
        exist_color = len(np.unique(input_las.red)) > 1
    except:
        exist_color = False

    # fig, ax = plt.subplots(fig_size=(20,20), subplot_kw = dict(projection='3d'),
    #                        gridspec_kw = dict(top=0.5, bottom = 0, left = 0, right = 1))
    # fig, ax = plt.subplots(subplot_kw = dict(projection='3d'), layout='compressed')
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    if exist_color:

        table_color = np.stack(
            (
                input_las.red[idx_preview],
                input_las.green[idx_preview],
                input_las.blue[idx_preview],
            ),
            axis=1,
        )
        ax.scatter(point_x, point_y, point_z, c=table_color / (2**16), s=0.01)
        ax.margins(x=0, tight=True)
        ax.set_xlim([x1, x2])
        ax.set_ylim([y1, y2])
        ax.set_zlim([z1, z2])
        # ax.set_yticks([])
        # ax.set_xticks([])
        # ax.set_zticks([])
        ax.set_aspect("equal")
        plt.axis("off")
        # ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # plt.show()

    else:
        table_color = point_z

        ax.scatter(point_x, point_y, point_z, c=table_color, cmap="coolwarm", s=0.01)
        ax.margins(x=0, tight=True)
        ax.set_xlim([x1, x2])
        ax.set_ylim([y1, y2])
        ax.set_zlim([z1, z2])
        # ax.set_yticks([])
        # ax.set_xticks([])
        # ax.set_zticks([])
        ax.set_aspect("equal")
        plt.axis("off")
        # ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # plt.show()

    in_memory_buff = io.BytesIO()
    plt.savefig(
        in_memory_buff, transparent=True, bbox_inches="tight", dpi=200
    )  # generate image with margins
    in_memory_buff.seek(0)
    plt.close("all")

    # region - Reduce the margins

    img = mpimg.imread(in_memory_buff)
    tmp_x, tmp_y = np.where(img[:, :, -1] != 0)
    x1 = np.min(tmp_x) - 10
    x2 = np.max(tmp_x) + 10
    if x1 < 0:
        x1 = 0
    if x2 > img.shape[1]:
        x2 = img.shape[1]
    y1 = np.min(tmp_y) - 10
    y2 = np.max(tmp_y) + 10
    if y1 < 0:
        y1 = 0
    if y2 > img.shape[0]:
        y2 = img.shape[0]
    plt.imshow(img[x1:x2, y1:y2, :])
    plt.axis("off")
    plt.savefig(preview_out_path, transparent=True, bbox_inches="tight", dpi=200)
    plt.close("all")

    # endregion
