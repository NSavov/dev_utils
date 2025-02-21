import os
import subprocess


def dataset_download(*args: str) -> None:
    """Python wrapper to call the dataset_download shell script with an argument."""
    script_path = os.path.join(os.path.dirname(__file__), "../shell_utils/dataset_download.sh")
    subprocess.run(["bash", script_path, *args], check=False)


def dataset_upload(*args: str) -> None:
    """Python wrapper to call the second_script shell script with an argument."""
    script_path = os.path.join(os.path.dirname(__file__), "../shell_utils/dataset_upload.sh")
    subprocess.run(["bash", script_path, *args], check=False)
