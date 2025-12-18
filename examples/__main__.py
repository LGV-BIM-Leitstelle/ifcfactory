import importlib
import pkgutil
import re

for pkg in [pkg for pkg in pkgutil.walk_packages(path=(".",)) if re.match(r"examples\.\d\d", pkg.name)]:
    getattr(importlib.import_module(pkg.name), "main", lambda x: x)()
