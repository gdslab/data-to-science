import tarfile
import os
from typing import Any, Dict, List


class TarProcessor:
    """
    Used to extract contents of tar file and return tar file's directory structure
    in Dict format.
    """

    def __init__(self, tar_file_path: str) -> None:
        """Initialize TarProcessor with tar file path.

        Args:
            tar_file_path (str): Tar file path.
        """
        # confirm file exists
        if not os.path.exists(tar_file_path):
            raise FileNotFoundError(f"Unable to locate .tar at: {tar_file_path}")

        self.tar_file_path = tar_file_path

    def extract(self) -> None:
        """
        Extracts all contents of tar file to current directory.
        """
        with tarfile.open(self.tar_file_path, "r") as tar_file:
            parent_dir = os.path.dirname(self.tar_file_path)
            tar_file.extractall(path=parent_dir)

    def get_directory_structure(self) -> Dict[str, Any]:
        """Returns tar file's directory structure in Dict format.

        Returns:
            dict: Dict representation of tar file's directory structure.
        """
        return generate_tar_structure_json(self.tar_file_path)

    def remove(self) -> None:
        """
        Remove .tar file from file system.
        """
        if os.path.exists(self.tar_file_path):
            os.remove(self.tar_file_path)


def generate_tar_structure_json(tar_file_path: str) -> Dict[str, Any]:
    """Returns Dict representation of the tar file's directory structure.

    Args:
        tar_file_path (str): Path to tar file.

    Returns:
        dict: Dict representation of tar file's directory structure.
    """

    def build_tree(
        tar_info: tarfile.TarInfo, members: List[tarfile.TarInfo]
    ) -> Dict[str, Any]:
        """Recursively builds the directory tree structure.

        Args:
            tar_info (tarfile.TarInfo): Tar info for top-level directory.
            members (List[tarfile.TarInfo]): Tar info for all members of tar archive.

        Returns:
            Dict[str, Any]: Dictionary of tar file's directory structure.
        """
        node: Dict[str, Any] = {
            "name": os.path.basename(tar_info.name),
            "type": "directory" if tar_info.isdir() else "file",
        }
        if tar_info.isfile():
            node["size"] = tar_info.size

        children = [
            build_tree(member, members)
            for member in members
            if os.path.dirname(member.name) == tar_info.name
        ]
        if children:
            node["children"] = children
        return node

    try:
        with tarfile.open(tar_file_path, "r") as tar:
            members = tar.getmembers()

            # raise exception if no members inside tar
            if len(members) == 0:
                return {"error": "Tar archive does not contain any files"}

            # check for multiple top-level directories
            top_level_dirs = [
                member for member in members if os.path.dirname(member.name) == ""
            ]

            if len(top_level_dirs) > 1:
                return {"error": "Multiple top-level directories found in tar archive"}

            elif len(top_level_dirs) == 1:
                root_member = top_level_dirs[0]
                tree = build_tree(root_member, members)
                return tree
            else:
                return {"error": "Could not find top-level directory in tar archive"}
    except tarfile.TarError as e:
        return {"error": f"Error reading tar file: {e}"}
