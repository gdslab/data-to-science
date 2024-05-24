import argparse
import json
import logging
import os
import sys
from contextlib import redirect_stdout
from glob import glob
from pathlib import Path

import functions


logger = logging.getLogger(__name__)


def run(config_filepath: str) -> None:
    logger.info("running agtc")
    try:
        with open("devnull", "w") as fnull:
            with redirect_stdout(fnull):
                # create template with AgTC
                functions.create_new_template(
                    config_filepath,
                    "TEMPLATE_INPUT",
                    "COLUMNS_TEMPLATE",
                    "NEW_COLUMNS",
                    "SAMPLES_PER_PLOT",
                    "SAMPLE_IDENTIFIER",
                    "TEMPLATE_OUTPUT",
                )
        # construct path to output csv
        output_dir = str(Path(config_filepath).parent / "output")
        output_dir_contents = glob(f"{output_dir}/*.csv")
        output_filepath = str(Path(output_dir_contents[0]).resolve())
    except Exception as e:
        print(
            json.dumps(
                {"status": 0, "message": "AgTC task failed", "output_filepath": ""}
            )
        )
        return None
    print(
        json.dumps(
            {
                "status": 1,
                "message": "AgTC task finished",
                "output_filepath": output_filepath,
            }
        )
    )
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Runs AgTC with config.yml created on D2S."
    )
    parser.add_argument("in_config", type=str, help="Path to config.yml.")

    args = parser.parse_args()

    if not os.path.exists(args.in_config):
        raise FileNotFoundError("config.yml not found")

    run(args.in_config)
