import argparse
import logging
import os
from pathlib import Path

from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from tqdm import tqdm

from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.tasks.post_upload_tasks import generate_point_cloud_preview

logger = logging.getLogger("__name__")


def run(db: Session, check_only: bool) -> None:
    # query statement for all active point clouds
    point_cloud_query = select(DataProduct).where(
        and_(DataProduct.data_type == "point_cloud", DataProduct.is_active)
    )
    # perform query
    with db as session:
        point_clouds = session.scalars(point_cloud_query).all()
        # track missing preview images
        missing_previews = 0
        # for each point cloud data product
        for idx in tqdm(range(0, len(point_clouds))):
            # check if a preview image exists
            preview_img_path = point_clouds[idx].filepath.replace(".copc.laz", ".png")
            if (
                os.path.exists(point_clouds[idx].filepath)
                and not os.path.exists(preview_img_path)
                and not os.path.exists(
                    Path(point_clouds[idx].filepath).parent / "preview_failed"
                )
            ):
                # create preview image
                if not check_only:
                    generate_point_cloud_preview(point_clouds[idx].filepath)
                else:
                    missing_previews += 1

    if check_only:
        print(
            f"Missing preview images for {missing_previews} of {len(point_clouds)} point clouds."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Checks for point cloud preview image and generates one if missing."
    )
    parser.add_argument(
        "--check-only",
        type=bool,
        help="Only returns count of missing preview images. Does not generate preview images.",
        default=0,
        required=False,
    )

    args = parser.parse_args()

    try:
        # get database session
        db = SessionLocal()
        run(db, check_only=args.check_only)
    except Exception as e:
        print(str(e))
    finally:
        db.close()
