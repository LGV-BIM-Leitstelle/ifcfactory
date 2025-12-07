import importlib
import os
import pkgutil
import re
import sys

import numpy as np
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in map(os.path.abspath, sys.path):
    sys.path.insert(0, project_root)

def discover_example_modules():
    for pkg in pkgutil.walk_packages(path=(os.path.join(os.path.dirname(__file__), '../examples'),), prefix="examples."):
        if re.match(r'examples\.\d\d', pkg.name):
            yield pkg.name


@pytest.mark.parametrize("module_name", list(discover_example_modules()))
def test_example_main(module_name):
    module = importlib.import_module(module_name)
    main = getattr(module, "main", None)

    if callable(main):
        result = main()
    else:
        pytest.skip(f"{module_name} has no main() function")

    if module_name == 'examples.01_basic_object_creation':
        walls = {w.Name: w for w in result.by_type('IfcWall')}
        assert walls.keys() == {'Box Wall', 'Cube Wall', 'Cylinder Wall'}

        # Box(width=5.0, depth=0.3, height=3.0)
        assert walls['Box Wall'].Representation.Representations[0].Items[0].is_a('IfcExtrudedAreaSolid')
        xys = np.array(walls['Box Wall'].Representation.Representations[0].Items[0].SweptArea.OuterCurve.Points.CoordList)
        assert xys.min(axis=0).tolist() == [0., 0.]
        assert xys.max(axis=0).tolist() == [5., 0.3]
        assert walls['Box Wall'].Representation.Representations[0].Items[0].Depth == 3.
        
        # Cube(size=4.0)
        assert walls['Cube Wall'].Representation.Representations[0].Items[0].is_a('IfcExtrudedAreaSolid')
        xys = np.array(walls['Cube Wall'].Representation.Representations[0].Items[0].SweptArea.OuterCurve.Points.CoordList)
        assert xys.min(axis=0).tolist() == [0., 0.]
        assert xys.max(axis=0).tolist() == [4., 4.]
        assert walls['Cube Wall'].Representation.Representations[0].Items[0].Depth == 4.

        # Cylinder(radius=1.5, height=4.0)
        assert walls['Cylinder Wall'].Representation.Representations[0].Items[0].SweptArea.is_a('IfcCircleProfileDef')
