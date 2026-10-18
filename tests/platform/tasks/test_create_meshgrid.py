import geopandas as gpd  # type: ignore[import-untyped]
import pytest
from shapely.geometry import box

from ecoscope.platform.tasks.analysis import create_meshgrid
from ecoscope.platform.tasks.analysis._time_density import (
    AutoScaleGridCellSize,
    CustomGridCellSize,
)

from ..utils.random_geometry import random_3857_rectangle


def test_create_meshgrid():
    bounds = random_3857_rectangle(500, 500, 500, 500, utm_safe=True)
    aoi = gpd.GeoDataFrame(geometry=[bounds], crs="EPSG:3857")

    meshgrid_custom_cell_size = create_meshgrid(
        aoi,
        auto_scale_or_custom_cell_size=CustomGridCellSize(grid_cell_size=250.0),
    )

    meshgrid_auto_scale = create_meshgrid(
        aoi,
        auto_scale_or_custom_cell_size=AutoScaleGridCellSize(),
    )

    # In this case the custom cell size of 250 is actually too big for a 500x500 square
    # So we expect the auto-scaled value to be smaller
    assert 0 < len(meshgrid_custom_cell_size) < len(meshgrid_auto_scale)
    for point in aoi["geometry"]:
        assert meshgrid_custom_cell_size.intersects(point).any()
        assert meshgrid_auto_scale.intersects(point).any()


def test_create_meshgrid_tiny_cell_size_errors():
    # 60km x 60km: with cell_size=1.0 this exceeds the extent-based cell
    # budget (~3e9 cells), so the extent guard fires instead of the param
    # bound, which the 1.0 cell size already passes.
    aoi = gpd.GeoDataFrame(geometry=[box(0, 0, 60000, 60000)], crs="EPSG:3857")

    with pytest.raises(
        ValueError,
        match="Custom grid cell size is too small for the extent of the area of interest",
    ):
        create_meshgrid(
            aoi,
            auto_scale_or_custom_cell_size=CustomGridCellSize(grid_cell_size=1.0),
        )
