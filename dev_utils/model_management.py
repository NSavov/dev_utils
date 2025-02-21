from __future__ import annotations

import contextlib
import os
import shutil
from pathlib import Path
from typing import Callable

from natsort import natsorted


def get_checkpoint_dpath(  # noqa: PLR0912
    run_name: str,
    ckpt_dpath: Path,
    ckpt_central_dpath: Path | None = None,
    load_ckpt: tuple | None = None,
    is_main_process: bool | None = True,
    wait_callback: Callable | None = None,
    name_id_map: dict | None = None,
) -> tuple:
    """
    Returns the checkpoint directory path and the path to the checkpoint to load.

    If load_ckpt is None, then the checkpoint directory is created and the load_checkpoint_fpath
    is None.
    If load_ckpt is not None, then the checkpoint directory is created and the load_checkpoint_fpath
    is set to the path of the checkpoint to load.

    run_name: str
        The name of the run
    ckpt_central_dpath: Path
        The central checkpoint directory path that holds all the model ids
    load_ckpt: tuple
        A tuple that holds the checkpoint id and the model id to load. If None, then no checkpoint
        is loaded.
    is_main_process: bool
        If True, then the process is the main process
    wait_callback: callable
        A callback function that is called in order to synchronize multiple processes.
    """
    load_checkpoint_fpath = None
    run_id = None
    if ckpt_central_dpath is not None:
        os.makedirs(ckpt_central_dpath, exist_ok=True)
        cdm = CheckpointDirManager(ckpt_central_dpath)

        if is_main_process:
            if name_id_map is not None and run_name in name_id_map:
                run_id = name_id_map[run_name]
                checkpoint_dpath = cdm.build_dpath_by_id(
                    run_id,
                    description=run_name,
                    exist_ok=True,
                )
            else:
                checkpoint_dpath = cdm.build_dpath_next(run_name)
            cdm.update()
            run_id = cdm.get_last_id()

    cdm = CheckpointDirManager(ckpt_dpath)
    if run_id is None:
        run_id = cdm.get_next_id()

    if is_main_process:
        if name_id_map is not None and run_name in name_id_map:
            run_id = name_id_map[run_name]
            checkpoint_dpath = cdm.build_dpath_by_id(run_id, description=run_name, exist_ok=True)
        else:
            checkpoint_dpath = cdm.build_dpath_by_id(run_id, description=run_name)

    if wait_callback is not None:
        wait_callback()

    if not is_main_process:
        cdm.update()
        checkpoint_dpath = cdm.get_last_dpath()

    if load_ckpt is not None:
        if not hasattr(load_ckpt, "__iter__") or len(load_ckpt) != 2:
            msg = "load_ckpt must be an iterable with exactly two elements"
            raise ValueError(msg)

        if load_ckpt[0] == "last":
            load_checkpoint_dpath = cdm.get_last_dpath()
        else:
            load_checkpoint_dpath = cdm.get_dpath_by_id(load_ckpt[0])

        cm = CheckpointManager(load_checkpoint_dpath)
        if load_ckpt[1] == "last":
            load_checkpoint_fpath = cm.get_last_fpath()
        else:
            load_checkpoint_fpath = cm.get_fpath_by_id(load_ckpt[1])

    if wait_callback is not None:
        wait_callback()

    return checkpoint_dpath, load_checkpoint_fpath


class CheckpointManager:
    def __init__(self, checkpoints_root_dpath: Path | str) -> None:
        if type(checkpoints_root_dpath) is str:
            self.checkpoints_root_dpath = Path(checkpoints_root_dpath)
        else:
            self.checkpoints_root_dpath = checkpoints_root_dpath
        self.checkpoints_root_dpath.mkdir(parents=True, exist_ok=True)
        self.update()

    def update(self) -> None:
        self.checkpoints_fnames = natsorted(os.listdir(self.checkpoints_root_dpath))
        self.checkpoints_fnames = list(
            filter(lambda fname: "model" in fname, self.checkpoints_fnames),
        )
        print(self.checkpoints_fnames)
        self.checkpoints_dict = {}
        for fname in self.checkpoints_fnames:
            model_id = int(fname.rsplit(".", 1)[0].split("-", 1)[1])
            if model_id not in self.checkpoints_dict:
                self.checkpoints_dict[model_id] = []
            self.checkpoints_dict[model_id].append(fname)

    def log_state(self) -> None:
        ids = self.checkpoints_dict.keys()
        if len(ids) == 0:
            print("No checkpoints found!")
            return

        # print min and max ids
        print(f"Min checkpoint id: {min(ids)}")
        print(f"Max checkpoint id: {max(ids)}")

        repeating_ids = [
            model_id for model_id, lst in self.checkpoints_dict.items() if len(lst) > 1
        ]
        if len(repeating_ids) > 0:
            print(f"Repeating checkpoints: {self.repeating_numbers}")

    def get_fpath_by_id(self, model_id: int) -> Path:
        if model_id not in self.checkpoints_dict:
            msg = f"Checkpoint file with id {model_id} not found!"
            raise FileNotFoundError(msg)

        if len(self.checkpoints_dict[model_id]) > 1:
            msg = f"Multiple checkpoint files found with id {model_id}: \
                {self.checkpoints_dict[model_id]}"
            raise FileExistsError(
                msg,
            )
        return self.checkpoints_root_dpath / self.checkpoints_dict[model_id][0]

    def get_last_fpath(self) -> Path:
        if len(self.checkpoints_dict) == 0:
            msg = f"No checkpoint files found at {self.checkpoints_root_dpath}"
            raise FileNotFoundError(msg)
        return self.get_fpath_by_id(max(self.checkpoints_dict.keys()))

    def get_last_id(self) -> int:
        return max(self.checkpoints_dict.keys())


class CheckpointDirManager:
    def __init__(self, checkpoints_root_dpath: Path | str) -> None:
        if type(checkpoints_root_dpath) is str:
            self.checkpoints_root_dpath = Path(checkpoints_root_dpath)
        else:
            self.checkpoints_root_dpath = checkpoints_root_dpath
        self.checkpoints_root_dpath.mkdir(parents=True, exist_ok=True)
        self.update()

    def update(self) -> None:
        self.checkpoints_dnames = natsorted(os.listdir(self.checkpoints_root_dpath))
        self.checkpoints_dnames = list(
            filter(lambda fname: fname.split("_", 1)[0].isdigit(), self.checkpoints_dnames),
        )
        self.checkpoints_dict = {}
        for fname in self.checkpoints_dnames:
            model_id = int(fname.split("_", 1)[0])
            if model_id not in self.checkpoints_dict:
                self.checkpoints_dict[model_id] = []
            self.checkpoints_dict[model_id].append(fname)

    def log_state(self) -> None:
        ids = self.checkpoints_dict.keys()
        if len(ids) == 0:
            print("No checkpoints found!")
            return

        # print min and max ids
        print(f"Min checkpoint id: {min(ids)}")
        print(f"Max checkpoint id: {max(ids)}")

        missing_ids = [i for i in range(min(ids), max(ids) + 1) if i not in ids]
        if len(missing_ids) > 0:
            print(f"Missing checkpoints: {missing_ids}")

        repeating_ids = [
            model_dir_id for model_dir_id, lst in self.checkpoints_dict.items() if len(lst) > 1
        ]
        if len(repeating_ids) > 0:
            print(f"Repeating checkpoints: {self.repeating_numbers}")

    def get_dpath_by_id(self, model_dir_id: int) -> Path:
        if model_dir_id not in self.checkpoints_dict:
            msg = f"Checkpoint with id {model_dir_id} not found!"
            raise FileNotFoundError(msg)

        if len(self.checkpoints_dict[model_dir_id]) > 1:
            msg = f"Multiple checkpoints found with id {model_dir_id}: \
                {self.checkpoints_dict[model_dir_id]}"
            raise FileExistsError(msg)
        return (self.checkpoints_root_dpath / self.checkpoints_dict[model_dir_id][0]).resolve()

    def get_dpath_by_description(self, description: str) -> list[Path]:
        dpaths = [
            self.checkpoints_root_dpath / dname
            for dname in self.checkpoints_dnames
            if description in dname
        ]

        if not dpaths:
            msg = f"No checkpoints found with description {description}!"
            raise FileNotFoundError(msg)

        if len(dpaths) > 1:
            msg = f"Multiple checkpoints found with description {description}: {dpaths}"
            raise FileExistsError(msg)

        return dpaths[0].resolve()

    def get_dpath_by_id_or_description(self, id_or_description: str) -> list[Path]:
        if id_or_description.isdigit():
            return self.get_dpath_by_id(int(id_or_description))
        return self.get_dpath_by_description(id_or_description)

    def get_last_dpath(self) -> Path:
        return self.get_dpath_by_id(max(self.checkpoints_dict.keys()))

    def get_last_id(self) -> int:
        if len(self.checkpoints_dict) == 0:
            msg = "No checkpoints found!"
            raise FileNotFoundError(msg)
        return max(self.checkpoints_dict.keys())

    def build_dpath_by_id(
        self,
        model_dir_id: int,
        description: str = "",
        base_id: int | None = None,
        base_iter: int | None = None,
        exist_ok: bool = False,
    ) -> Path:
        # self.delete_empty_by_id(id)
        if model_dir_id in self.checkpoints_dict:
            if not exist_ok:
                msg = f"Checkpoint with id {model_dir_id} already exists!"
                raise FileExistsError(msg)
            return self.get_dpath_by_id(model_dir_id)

        dname = f"{model_dir_id:03}"
        if description:
            dname = dname + "_" + description

        if base_id is not None:
            dname = dname + "_base_" + f"{base_id:03}"

        if base_iter is not None:
            dname = dname + "_iter_" + f"{base_iter}"

        out_dpath = self.checkpoints_root_dpath / dname

        if base_id is not None:
            out_dpath.mkdir(parents=True, exist_ok=False)
            base_dpath = self.get_dpath_by_id(base_id)
            if base_iter is not None:
                base_fpath = CheckpointManager(base_dpath).get_fpath_by_id(base_iter)
            else:
                base_fpath = CheckpointManager(base_dpath).get_last_fpath()
            shutil.copy(base_fpath, out_dpath)

        out_dpath.mkdir(parents=True, exist_ok=True)
        self.update()
        return out_dpath.resolve()

    def get_next_id(self) -> int:
        return max(self.checkpoints_dict.keys()) + 1 if len(self.checkpoints_dict) > 0 else 1

    def build_dpath_next(
        self,
        description: str = "",
        base_id: int | None = None,
        base_iter: int | None = None,
    ) -> Path:
        # self.delete_empty()
        next_id = self.get_next_id()
        return self.build_dpath_by_id(next_id, description, base_id, base_iter)

    def check_id_existence(self, model_dir_id: int) -> bool:
        return model_dir_id in self.checkpoints_dict

    def check_description_existence(self, description: str) -> bool:
        return any(description in dname for dname in self.checkpoints_dnames)

    def delete_by_id(self, model_dir_id: int, not_exist_ok: bool = True) -> None:
        if not self.check_id_existence(model_dir_id):
            if not not_exist_ok:
                msg = f"Checkpoint with id {model_dir_id} does not exist!"
                raise FileNotFoundError(msg)
            return

        dpath = self.get_dpath_by_id(model_dir_id)
        shutil.rmtree(dpath)
        self.update()

    def delete_until_id(self, model_dir_id: int) -> None:
        for dir_id in range(model_dir_id):
            with contextlib.suppress(Exception):
                self.delete_by_id(dir_id)

        self.update()

    def is_empty(self, dpath: Path) -> bool:
        return not [
            fname
            for fname in os.listdir(dpath)
            if not fname.endswith(".yaml") and fname not in ["log", "wandb"]
        ]

    def delete_empty_by_id(self, model_dir_id: int, not_exist_ok: bool = True) -> None:
        if not self.check_id_existence(model_dir_id):
            if not not_exist_ok:
                msg = f"Checkpoint with id {model_dir_id} does not exist!"
                raise FileNotFoundError(msg)
            return

        with contextlib.suppress(Exception):
            dpath = self.get_dpath_by_id(model_dir_id)

        if self.is_empty(dpath):
            shutil.rmtree(dpath)
            self.update()

    def delete_empty(self, test_mode: bool = False) -> None:
        """
        Deletes empty directories from the checkpoints directory. Keeps the last directory.

        Args:
            test_mode (bool, optional): If True, the deletion will be simulated without actually
            removing any directories.
                Defaults to False.
        """
        last_dpath = self.get_last_dpath()
        for dname in self.checkpoints_dnames:
            dpath = self.checkpoints_root_dpath / dname
            if dpath != last_dpath and self.is_empty(dpath):
                if not test_mode:
                    shutil.rmtree(dpath)
                else:
                    print(f"Empty directory: {dpath}")
                self.update()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dpath", type=str, required=True)
    args = parser.parse_args()

    cdm = CheckpointDirManager(args.dpath)
    cdm.log_state()
    cdm.delete_empty(test_mode=False)
    # cdm.delete_empty()
    # cdm.delete_by_id(1)
    # cdm.delete_until_id(2)
    # cdm.delete_empty_by_id(2)
    # cdm.build_dpath_by_id(1)
