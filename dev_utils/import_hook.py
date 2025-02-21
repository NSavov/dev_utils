from __future__ import annotations

import builtins
import importlib
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import ModuleType


class SubmoduleImporter:
    """Custom import hook for loading modules from an external repo."""

    def __init__(self, submodule_name: str, submodule_path: str) -> None:
        self.submodule_name = submodule_name
        self.submodule_path = submodule_path
        self.suffix = f"_{self.submodule_name}_{hash(self.submodule_name)}"

    def find_spec(
        self,
        fullname: str,
        path: str | None,  # noqa: ARG002
        target: str | None = None,  # noqa: ARG002
    ) -> importlib.machinery.ModuleSpec | None:
        """Redirects imports that start with `external_repo.`"""
        relative_module = fullname
        relative_module = relative_module.removesuffix(self.suffix)

        if relative_module.startswith(self.submodule_name + "."):
            relative_module = relative_module[len(self.submodule_name) + 1 :]

        relative_module = relative_module.removesuffix(".")

        module_path = os.path.join(
            self.submodule_path,
            relative_module.replace(".", "/") + ".py",
        )

        package_dir = os.path.join(
            self.submodule_path,
            relative_module.replace(".", "/"),
        )
        if os.path.exists(module_path):
            return importlib.util.spec_from_file_location(fullname, module_path)

        # Next, check if it's a package directory.
        if os.path.isdir(package_dir):
            # If an __init__.py exists, load it as a regular package.
            init_path = os.path.join(package_dir, "__init__.py")
            if os.path.exists(init_path):
                return importlib.util.spec_from_file_location(fullname, init_path)
            # No __init__.py: treat as an implicit namespace package.
            spec = importlib.machinery.ModuleSpec(
                fullname,
                loader=None,
                origin=package_dir,
            )
            spec.submodule_search_locations = [package_dir]
            return spec

        # Module not found.
        return None


class ImportHook:
    def __init__(self, submodule_name: str, submodule_path: str) -> None:
        self.importer = SubmoduleImporter(submodule_name, submodule_path)

        self.abs_submodule_path = os.path.abspath(submodule_path)
        self.original_import = builtins.__import__

        def custom_import(
            name: str,
            globals_: Mapping[str, object] | None = None,
            locals_: Mapping[str, object] | None = None,
            fromlist: Sequence[str] = (),
            level: int = 0,
        ) -> ModuleType:
            caller_file = globals_.get("__file__") if globals_ and "__file__" in globals_ else None

            if caller_file is not None and caller_file.startswith(
                self.abs_submodule_path,
            ):
                spec = self.importer.find_spec(name, None)

                if spec is not None and spec.name != "":
                    # If level > 0, resolve the relative import name to an absolute one.
                    if level > 0:
                        # globals should contain '__package__' for relative imports to work.
                        msg = "Relative imports with level > 0 not supported"
                        raise NotImplementedError(
                            msg,
                        )
                        # package = globals.get("__package__") if globals else None
                        # if package is None:
                        #     raise ImportError("Relative import in non-package")
                        # name = importlib.util.resolve_name(name, package)

                    # print(name, caller_file, self.abs_submodule_path)
                    name = spec.name
                    name_parts = name.split(".")
                    name_parts = [
                        part + self.importer.suffix if part else part for part in name_parts
                    ]
                    name = ".".join(name_parts)
                    # spec.name = name
                    if sys.modules.get(name):
                        return sys.modules[name]
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    return module

            return self.original_import(name, globals_, locals_, fromlist, level)

        self.custom_import = custom_import

    # Function to enable the import hook
    def enable_import_hook(self) -> None:
        if self.importer not in sys.meta_path:
            sys.meta_path.insert(0, self.importer)

        builtins.__import__ = self.custom_import

    # Function to disable the import hook
    def disable_import_hook(self) -> None:
        if self.importer in sys.meta_path:
            sys.meta_path.remove(self.importer)

        builtins.__import__ = self.original_import
