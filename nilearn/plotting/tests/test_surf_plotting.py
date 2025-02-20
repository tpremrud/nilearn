# Tests for functions in surf_plotting.py
import re
import tempfile
import unittest.mock as mock

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure
from numpy.testing import assert_array_equal

from nilearn._utils.helpers import is_kaleido_installed, is_plotly_installed
from nilearn.conftest import _rng
from nilearn.datasets import fetch_surf_fsaverage
from nilearn.plotting.displays import PlotlySurfaceFigure
from nilearn.plotting.surf_plotting import (
    VALID_HEMISPHERES,
    VALID_VIEWS,
    _compute_facecolors_matplotlib,
    _get_ticks_matplotlib,
    _get_view_plot_surf_matplotlib,
    _get_view_plot_surf_plotly,
    plot_img_on_surf,
    plot_surf,
    plot_surf_contours,
    plot_surf_roi,
    plot_surf_stat_map,
)
from nilearn.surface import load_surf_data, load_surf_mesh
from nilearn.surface.tests._testing import generate_surf

try:
    import IPython.display  # noqa:F401
except ImportError:
    IPYTHON_INSTALLED = False
else:
    IPYTHON_INSTALLED = True


EXPECTED_CAMERAS_PLOTLY = [
    (
        "left",
        "lateral",
        (0, 180),
        {
            "eye": {"x": -1.5, "y": 0, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    (
        "left",
        "medial",
        (0, 0),
        {
            "eye": {"x": 1.5, "y": 0, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Dorsal left
    (
        "left",
        "dorsal",
        (90, 0),
        {
            "eye": {"x": 0, "y": 0, "z": 1.5},
            "up": {"x": -1, "y": 0, "z": 0},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Ventral left
    (
        "left",
        "ventral",
        (270, 0),
        {
            "eye": {"x": 0, "y": 0, "z": -1.5},
            "up": {"x": 1, "y": 0, "z": 0},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Anterior left
    (
        "left",
        "anterior",
        (0, 90),
        {
            "eye": {"x": 0, "y": 1.5, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Posterior left
    (
        "left",
        "posterior",
        (0, 270),
        {
            "eye": {"x": 0, "y": -1.5, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Lateral right
    (
        "right",
        "lateral",
        (0, 0),
        {
            "eye": {"x": 1.5, "y": 0, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Medial right
    (
        "right",
        "medial",
        (0, 180),
        {
            "eye": {"x": -1.5, "y": 0, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Dorsal right
    (
        "right",
        "dorsal",
        (90, 0),
        {
            "eye": {"x": 0, "y": 0, "z": 1.5},
            "up": {"x": -1, "y": 0, "z": 0},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Ventral right
    (
        "right",
        "ventral",
        (270, 0),
        {
            "eye": {"x": 0, "y": 0, "z": -1.5},
            "up": {"x": 1, "y": 0, "z": 0},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Anterior right
    (
        "right",
        "anterior",
        (0, 90),
        {
            "eye": {"x": 0, "y": 1.5, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
    # Posterior right
    (
        "right",
        "posterior",
        (0, 270),
        {
            "eye": {"x": 0, "y": -1.5, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
            "center": {"x": 0, "y": 0, "z": 0},
        },
    ),
]


EXPECTED_VIEW_MATPLOTLIB = {"left": {"anterior": (0, 90),
                                     "posterior": (0, 270),
                                     "medial": (0, 0),
                                     "lateral": (0, 180),
                                     "dorsal": (90, 0),
                                     "ventral": (270, 0)},
                            "right": {"anterior": (0, 90),
                                      "posterior": (0, 270),
                                      "medial": (0, 180),
                                      "lateral": (0, 0),
                                      "dorsal": (90, 0),
                                      "ventral": (270, 0)}}


@pytest.mark.parametrize("full_view", EXPECTED_CAMERAS_PLOTLY)
def test_get_view_plot_surf_plotly(full_view):
    from nilearn.plotting.surf_plotting import (
        _get_camera_view_from_elevation_and_azimut,
        _get_camera_view_from_string_view,
        _get_view_plot_surf_plotly,
    )
    hemi, view_name, (elev, azim), expected_camera_view = full_view
    camera_view = _get_view_plot_surf_plotly(hemi, view_name)
    camera_view_string = _get_camera_view_from_string_view(hemi, view_name)
    camera_view_elev_azim = _get_camera_view_from_elevation_and_azimut(
        (elev, azim)
    )
    # Check each camera view parameter
    for k in ["center", "eye", "up"]:
        # Check default camera view
        assert np.allclose(
            list(camera_view[k].values()),
            list(expected_camera_view[k].values())
        )
        # Check camera view obtained from string view
        assert np.allclose(
            list(camera_view_string[k].values()),
            list(expected_camera_view[k].values())
        )
        # Check camera view obtained from elevation & azimut
        assert np.allclose(
            list(camera_view_elev_azim[k].values()),
            list(expected_camera_view[k].values())
        )


@pytest.fixture
def expected_view_matplotlib(hemi, view):
    return EXPECTED_VIEW_MATPLOTLIB[hemi][view]


@pytest.mark.parametrize("hemi", VALID_HEMISPHERES)
@pytest.mark.parametrize("view", VALID_VIEWS)
def test_get_view_plot_surf_matplotlib(hemi, view, expected_view_matplotlib):
    from nilearn.plotting.surf_plotting import _get_view_plot_surf_matplotlib
    assert (_get_view_plot_surf_matplotlib(hemi, view)
            == expected_view_matplotlib)


def test_surface_figure():
    from nilearn.plotting.displays import SurfaceFigure
    s = SurfaceFigure()
    assert s.output_file is None
    assert s.figure is None
    with pytest.raises(NotImplementedError):
        s.show()
    with pytest.raises(ValueError, match="You must provide an output file"):
        s._check_output_file()
    s._check_output_file("foo.png")
    assert s.output_file == "foo.png"
    s = SurfaceFigure(output_file="bar.png")
    assert s.output_file == "bar.png"


@pytest.mark.skipif(is_plotly_installed(),
                    reason='Plotly is installed.')
def test_plotly_surface_figure_import_error():
    """Test that an ImportError is raised when instantiating \
       a PlotlySurfaceFigure without having Plotly installed."""
    with pytest.raises(ImportError, match="Plotly is required"):
        PlotlySurfaceFigure()


@pytest.mark.skipif(not is_plotly_installed() or is_kaleido_installed(),
                    reason=("This test only runs if Plotly is "
                            "installed, but not kaleido."))
def test_plotly_surface_figure_savefig_error():
    """Test that an ImportError is raised when saving \
       a PlotlySurfaceFigure without having kaleido installed."""
    with pytest.raises(ImportError, match="`kaleido` is required"):
        PlotlySurfaceFigure().savefig()


@pytest.mark.skipif(not is_plotly_installed() or not is_kaleido_installed(),
                    reason=("Plotly and/or kaleido not installed; "
                            "required for this test."))
def test_plotly_surface_figure():
    ps = PlotlySurfaceFigure()
    assert ps.output_file is None
    assert ps.figure is None
    ps.show()
    with pytest.raises(ValueError, match="You must provide an output file"):
        ps.savefig()
    ps.savefig('foo.png')


@pytest.mark.skipif(not is_plotly_installed() or not IPYTHON_INSTALLED,
                    reason=("Plotly and/or Ipython is not installed; "
                            "required for this test."))
@pytest.mark.parametrize("renderer", ['png', 'jpeg', 'svg'])
def test_plotly_show(renderer):
    import plotly.graph_objects as go
    ps = PlotlySurfaceFigure(go.Figure())
    assert ps.output_file is None
    assert ps.figure is not None
    with mock.patch("IPython.display.display") as mock_display:
        ps.show(renderer=renderer)
    assert len(mock_display.call_args.args) == 1
    key = 'svg+xml' if renderer == 'svg' else renderer
    assert f'image/{key}' in mock_display.call_args.args[0]


@pytest.mark.skipif(not is_plotly_installed() or not is_kaleido_installed(),
                    reason=("Plotly and/or kaleido not installed; "
                            "required for this test."))
def test_plotly_savefig(tmp_path):
    import plotly.graph_objects as go
    ps = PlotlySurfaceFigure(go.Figure(), output_file=tmp_path / "foo.png")
    assert ps.output_file == tmp_path / "foo.png"
    assert ps.figure is not None
    ps.savefig()
    assert (tmp_path / "foo.png").exists()


@pytest.mark.skipif(not is_plotly_installed(),
                    reason='Plotly is not installed; required for this test.')
@pytest.mark.parametrize("input_obj", ["foo", Figure(), ["foo", "bar"]])
def test_instantiation_error_plotly_surface_figure(input_obj):
    with pytest.raises(TypeError,
                       match=("`PlotlySurfaceFigure` accepts only "
                              "plotly figure objects.")):
        PlotlySurfaceFigure(input_obj)


@pytest.mark.parametrize(
    "view,is_valid",
    [
        ("lateral", True),
        ("medial", True),
        ("latreal", False),
        ((100, 100), True),
        ([100.0, 100.0], True),
        ((100, 100, 1), False),
        (("lateral", "medial"), False),
        ([100, "bar"], False),
    ]
)
def test_check_view_is_valid(view, is_valid):
    from nilearn.plotting.surf_plotting import _check_view_is_valid
    assert _check_view_is_valid(view) is is_valid


@pytest.mark.parametrize(
    "hemi,is_valid",
    [
        ("left", True),
        ("right", True),
        ("lft", False),
    ]
)
def test_check_hemisphere_is_valid(hemi, is_valid):
    from nilearn.plotting.surf_plotting import _check_hemisphere_is_valid
    assert _check_hemisphere_is_valid(hemi) is is_valid


@pytest.mark.parametrize("hemi,view", [("foo", "medial"), ("bar", "anterior")])
def test_get_view_plot_surf_hemisphere_errors(hemi, view):
    from nilearn.plotting.surf_plotting import (
        _get_view_plot_surf_matplotlib,
        _get_view_plot_surf_plotly,
    )
    with pytest.raises(ValueError,
                       match="Invalid hemispheres definition"):
        _get_view_plot_surf_matplotlib(hemi, view)
    with pytest.raises(ValueError,
                       match="Invalid hemispheres definition"):
        _get_view_plot_surf_plotly(hemi, view)


@pytest.mark.parametrize(
    "hemi,view,f",
    [
        ("left", "foo", _get_view_plot_surf_matplotlib),
        ("right", "bar", _get_view_plot_surf_plotly),
    ]
)
def test_get_view_plot_surf_view_errors(hemi, view, f):
    with pytest.raises(ValueError,
                       match="Invalid view definition"):
        f(hemi, view)


def test_configure_title_plotly():
    from nilearn.plotting.surf_plotting import _configure_title_plotly
    assert _configure_title_plotly(None, None) == dict()
    assert _configure_title_plotly(None, 22) == dict()
    config = _configure_title_plotly("Test Title", 22, color="green")
    assert config["text"] == "Test Title"
    assert config["x"] == 0.5
    assert config["y"] == 0.96
    assert config["xanchor"] == "center"
    assert config["yanchor"] == "top"
    assert config["font"]["size"] == 22
    assert config["font"]["color"] == "green"


@pytest.mark.parametrize("data,expected",
                         [(np.linspace(0, 1, 100), (0, 1)),
                          (np.linspace(-.7, -.01, 40), (-.7, -.01))])
def test_get_bounds(data, expected):
    from nilearn.plotting.surf_plotting import _get_bounds
    assert _get_bounds(data) == expected
    assert _get_bounds(data, vmin=.2) == (.2, expected[1])
    assert _get_bounds(data, vmax=.8) == (expected[0], .8)
    assert _get_bounds(data, vmin=.1, vmax=.8) == (.1, .8)


def test_plot_surf_engine_error():
    mesh = generate_surf()
    with pytest.raises(ValueError,
                       match="Unknown plotting engine"):
        plot_surf(mesh, engine="foo")


@pytest.mark.parametrize("engine", ["matplotlib", "plotly"])
def test_plot_surf(engine, tmp_path, rng):
    if not is_plotly_installed() and engine == "plotly":
        pytest.skip('Plotly is not installed; required for this test.')
    mesh = generate_surf()
    bg = rng.standard_normal(size=mesh[0].shape[0])

    # Plot mesh only
    plot_surf(mesh, engine=engine)

    # Plot mesh with background
    plot_surf(mesh, bg_map=bg, engine=engine)
    plot_surf(mesh, bg_map=bg, darkness=0.5, engine=engine)
    plot_surf(mesh, bg_map=bg, alpha=0.5,
              output_file=tmp_path / 'tmp.png', engine=engine)

    # Plot different views
    plot_surf(mesh, bg_map=bg, hemi='right', engine=engine)
    plot_surf(mesh, bg_map=bg, view='medial', engine=engine)
    plot_surf(mesh, bg_map=bg, hemi='right', view='medial', engine=engine)

    # Plot with colorbar
    plot_surf(mesh, bg_map=bg, colorbar=True, engine=engine)
    plot_surf(mesh, bg_map=bg, colorbar=True, cbar_vmin=0,
              cbar_vmax=150, cbar_tick_format="%i", engine=engine)
    # Save execution time and memory
    plt.close()

    # Plot with title
    display = plot_surf(mesh, bg_map=bg, title='Test title',
                        engine=engine)
    if engine == 'matplotlib':
        assert len(display.axes) == 1
        assert display.axes[0].title._text == 'Test title'


def test_plot_surf_avg_method(rng):
    mesh = generate_surf()
    # Plot with avg_method
    # Test all built-in methods and check
    mapp = rng.standard_normal(size=mesh[0].shape[0])
    mesh_ = load_surf_mesh(mesh)
    _, faces = mesh_[0], mesh_[1]

    for method in ['mean', 'median', 'min', 'max']:
        display = plot_surf(mesh, surf_map=mapp,
                            avg_method=method,
                            engine='matplotlib')
        if method == 'mean':
            agg_faces = np.mean(mapp[faces], axis=1)
        elif method == 'median':
            agg_faces = np.median(mapp[faces], axis=1)
        elif method == 'min':
            agg_faces = np.min(mapp[faces], axis=1)
        elif method == 'max':
            agg_faces = np.max(mapp[faces], axis=1)
        vmin = np.min(agg_faces)
        vmax = np.max(agg_faces)
        agg_faces -= vmin
        agg_faces /= (vmax - vmin)
        cmap = plt.get_cmap(plt.rcParamsDefault['image.cmap'])
        assert_array_equal(
            cmap(agg_faces),
            display._axstack.as_list()[0].collections[0]._facecolors
        )

    #  Try custom avg_method
    def custom_avg_function(vertices):
        return vertices[0] * vertices[1] * vertices[2]
    plot_surf(
        mesh,
        surf_map=rng.standard_normal(size=mesh[0].shape[0]),
        avg_method=custom_avg_function,
        engine='matplotlib',
    )
    # Save execution time and memory
    plt.close()


@pytest.mark.parametrize("engine", ["matplotlib", "plotly"])
def test_plot_surf_error(engine, rng):
    if not is_plotly_installed() and engine == "plotly":
        pytest.skip('Plotly is not installed; required for this test.')
    mesh = generate_surf()

    # Wrong inputs for view or hemi
    with pytest.raises(ValueError, match='Invalid view definition'):
        plot_surf(mesh, view='middle', engine=engine)
    with pytest.raises(ValueError, match='Invalid hemispheres definition'):
        plot_surf(mesh, hemi='lft', engine=engine)

    # Wrong size of background image
    with pytest.raises(
            ValueError,
            match='bg_map does not have the same number of vertices'):
        plot_surf(mesh,
                  bg_map=rng.standard_normal(size=mesh[0].shape[0] - 1),
                  engine=engine
                  )

    # Wrong size of surface data
    with pytest.raises(
        ValueError, match="surf_map does not have the same number of vertices"
    ):
        plot_surf(
            mesh,
            surf_map=rng.standard_normal(size=mesh[0].shape[0] + 1),
            engine=engine
        )

    with pytest.raises(
        ValueError, match="'surf_map' can only have one dimension"
    ):
        plot_surf(
            mesh,
            surf_map=rng.standard_normal(size=(mesh[0].shape[0], 2)),
            engine=engine
        )


def test_plot_surf_avg_method_errors(rng):
    mesh = generate_surf()
    with pytest.raises(
        ValueError,
        match=(
            "Array computed with the custom "
            "function from avg_method does "
            "not have the correct shape"
        )
    ):
        def custom_avg_function(vertices):
            return [vertices[0] * vertices[1], vertices[2]]

        plot_surf(mesh,
                  surf_map=rng.standard_normal(
                      size=mesh[0].shape[0]),
                  avg_method=custom_avg_function,
                  engine='matplotlib'
                  )

    with pytest.raises(
        ValueError,
        match=re.escape(
            "avg_method should be either "
            "['mean', 'median', 'max', 'min'] "
            "or a custom function"
        )
    ):
        custom_avg_function = dict()

        plot_surf(mesh,
                  surf_map=rng.standard_normal(
                      size=mesh[0].shape[0]),
                  avg_method=custom_avg_function,
                  engine='matplotlib'
                  )

        plot_surf(mesh,
                  surf_map=rng.standard_normal(
                      size=mesh[0].shape[0]),
                  avg_method="foo",
                  engine='matplotlib'
                  )

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Array computed with the custom function "
            "from avg_method should be an array of "
            "numbers (int or float)"
        )
    ):
        def custom_avg_function(vertices):
            return "string"

        plot_surf(mesh,
                  surf_map=rng.standard_normal(
                      size=mesh[0].shape[0]),
                  avg_method=custom_avg_function,
                  engine='matplotlib'
                  )


@pytest.mark.parametrize("engine", ["matplotlib", "plotly"])
def test_plot_surf_stat_map(engine, rng):
    if not is_plotly_installed() and engine == "plotly":
        pytest.skip('Plotly is not installed; required for this test.')
    mesh = generate_surf()
    bg = rng.standard_normal(size=mesh[0].shape[0])
    data = 10 * rng.standard_normal(size=mesh[0].shape[0])

    # Plot mesh with stat map
    plot_surf_stat_map(mesh, stat_map=data, engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, colorbar=True, engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, alpha=1, engine=engine)

    # Plot mesh with background and stat map
    plot_surf_stat_map(mesh, stat_map=data, bg_map=bg, engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, bg_map=bg,
                       bg_on_data=True, darkness=0.5,
                       engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, bg_map=bg, colorbar=True,
                       bg_on_data=True, darkness=0.5, engine=engine)

    # Plot with title
    display = plot_surf_stat_map(mesh, stat_map=data, bg_map=bg,
                                 title="Stat map title")
    assert display.axes[0].title._text == "Stat map title"

    # Apply threshold
    plot_surf_stat_map(mesh, stat_map=data, bg_map=bg,
                       bg_on_data=True, darkness=0.5,
                       threshold=0.3, engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, bg_map=bg, colorbar=True,
                       bg_on_data=True, darkness=0.5,
                       threshold=0.3, engine=engine)

    # Change colorbar tick format
    plot_surf_stat_map(mesh, stat_map=data, bg_map=bg, colorbar=True,
                       bg_on_data=True, darkness=0.5, cbar_tick_format="%.2g",
                       engine=engine)

    # Change vmax
    plot_surf_stat_map(mesh, stat_map=data, vmax=5, engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, vmax=5,
                       colorbar=True, engine=engine)

    # Change colormap
    plot_surf_stat_map(mesh, stat_map=data, cmap='cubehelix', engine=engine)
    plot_surf_stat_map(mesh, stat_map=data, cmap='cubehelix',
                       colorbar=True, engine=engine)

    plt.close()


def test_plot_surf_stat_map_matplotlib_specific(rng):
    mesh = generate_surf()
    data = 10 * rng.standard_normal(size=mesh[0].shape[0])
    # Plot to axes
    axes = plt.subplots(ncols=2, subplot_kw={'projection': '3d'})[1]
    for ax in axes.flatten():
        plot_surf_stat_map(mesh, stat_map=data, axes=ax)
    axes = plt.subplots(ncols=2, subplot_kw={'projection': '3d'})[1]
    for ax in axes.flatten():
        plot_surf_stat_map(mesh, stat_map=data, axes=ax, colorbar=True)

    fig = plot_surf_stat_map(mesh, stat_map=data, colorbar=False)
    assert len(fig.axes) == 1

    # symmetric_cbar
    fig = plot_surf_stat_map(
        mesh, stat_map=data, colorbar=True, symmetric_cbar=True)
    fig.canvas.draw()
    assert len(fig.axes) == 2
    yticklabels = fig.axes[1].get_yticklabels()
    first, last = yticklabels[0].get_text(), yticklabels[-1].get_text()
    assert float(first) == - float(last)

    # no symmetric_cbar
    fig = plot_surf_stat_map(
        mesh, stat_map=data, colorbar=True, symmetric_cbar=False)
    fig.canvas.draw()
    assert len(fig.axes) == 2
    yticklabels = fig.axes[1].get_yticklabels()
    first, last = yticklabels[0].get_text(), yticklabels[-1].get_text()
    assert float(first) != - float(last)

    # Test handling of nan values in texture data
    # Add nan values in the texture
    data[2] = np.nan
    # Plot the surface stat map
    fig = plot_surf_stat_map(mesh, stat_map=data)
    # Check that the resulting plot facecolors contain no transparent faces
    # (last column equals zero) even though the texture contains nan values
    tmp = fig._axstack.as_list()[0].collections[0]
    assert (mesh[1].shape[0] ==
            ((tmp._facecolors[:, 3]) != 0).sum())

    # Save execution time and memory
    plt.close()


def test_plot_surf_stat_map_error(rng):
    mesh = generate_surf()
    data = 10 * rng.standard_normal(size=mesh[0].shape[0])

    # Wrong size of stat map data
    with pytest.raises(
            ValueError,
            match='surf_map does not have the same number of vertices'):
        plot_surf_stat_map(mesh, stat_map=np.hstack((data, data)))

    with pytest.raises(
            ValueError,
            match="'surf_map' can only have one dimension"):
        plot_surf_stat_map(mesh, stat_map=np.vstack((data, data)).T)


def _generate_data_test_surf_roi():
    mesh = generate_surf()
    roi_idx = _rng().integers(0, mesh[0].shape[0], size=10)
    roi_map = np.zeros(mesh[0].shape[0])
    roi_map[roi_idx] = 1
    parcellation = _rng().integers(100, size=mesh[0].shape[0]).astype(float)
    return mesh, roi_map, parcellation


@pytest.mark.parametrize("engine", ["matplotlib", "plotly"])
def test_plot_surf_roi(engine):
    if not is_plotly_installed() and engine == "plotly":
        pytest.skip('Plotly is not installed; required for this test.')
    mesh, roi_map, parcellation = _generate_data_test_surf_roi()
    # plot roi
    plot_surf_roi(mesh, roi_map=roi_map, engine=engine)
    plot_surf_roi(mesh, roi_map=roi_map,
                  colorbar=True, engine=engine)
    # plot parcellation
    plot_surf_roi(mesh, roi_map=parcellation, engine=engine)
    plot_surf_roi(mesh, roi_map=parcellation, colorbar=True,
                  engine=engine)
    plot_surf_roi(mesh, roi_map=parcellation, colorbar=True,
                  cbar_tick_format="%f", engine=engine)
    plt.close()


def test_plot_surf_roi_matplotlib_specific():
    mesh, roi_map, parcellation = _generate_data_test_surf_roi()

    # change vmin, vmax
    img = plot_surf_roi(mesh, roi_map=roi_map, vmin=1.2,
                        vmax=8.9, colorbar=True,
                        engine='matplotlib')
    img.canvas.draw()
    cbar = img.axes[-1]
    cbar_vmin = float(cbar.get_yticklabels()[0].get_text())
    cbar_vmax = float(cbar.get_yticklabels()[-1].get_text())
    assert cbar_vmin == 1.0
    assert cbar_vmax == 8.0

    img2 = plot_surf_roi(mesh, roi_map=roi_map, vmin=1.2,
                         vmax=8.9, colorbar=True,
                         cbar_tick_format="%.2g",
                         engine='matplotlib')
    img2.canvas.draw()
    cbar = img2.axes[-1]
    cbar_vmin = float(cbar.get_yticklabels()[0].get_text())
    cbar_vmax = float(cbar.get_yticklabels()[-1].get_text())
    assert cbar_vmin == 1.2
    assert cbar_vmax == 8.9

    # Test nans handling
    parcellation[::2] = np.nan
    img = plot_surf_roi(mesh, roi_map=parcellation,
                        engine='matplotlib')
    # Check that the resulting plot facecolors contain no transparent faces
    # (last column equals zero) even though the texture contains nan values
    tmp = img._axstack.as_list()[0].collections[0]
    assert (
        mesh[1].shape[0] ==
        ((tmp._facecolors[:, 3]) != 0).sum()
    )
    # Save execution time and memory
    plt.close()


def test_plot_surf_roi_matplotlib_specific_plot_to_axes():
    """Test plotting directly on some axes."""
    mesh, roi_map, _ = _generate_data_test_surf_roi()

    plot_surf_roi(mesh, roi_map=roi_map, axes=None,
                  figure=plt.gcf(), engine='matplotlib')

    _, ax = plt.subplots(subplot_kw={'projection': '3d'})

    with tempfile.NamedTemporaryFile() as tmp_file:
        plot_surf_roi(mesh, roi_map=roi_map, axes=ax,
                      figure=None, output_file=tmp_file.name,
                      engine='matplotlib')

    with tempfile.NamedTemporaryFile() as tmp_file:
        plot_surf_roi(mesh, roi_map=roi_map, axes=ax,
                      figure=None, output_file=tmp_file.name,
                      colorbar=True, engine='matplotlib')

    # Save execution time and memory
    plt.close()


@pytest.mark.parametrize("engine", ["matplotlib", "plotly"])
def test_plot_surf_roi_error(engine, rng):
    if not is_plotly_installed() and engine == "plotly":
        pytest.skip('Plotly is not installed; required for this test.')
    mesh, roi_map, _ = _generate_data_test_surf_roi()

    # too many axes
    with pytest.raises(
        ValueError,
            match="roi_map can only have one dimension but has"):
        plot_surf_roi(
            mesh, roi_map=np.array([roi_map, roi_map]), engine=engine)

    # wrong number of vertices
    roi_idx = rng.integers(0, mesh[0].shape[0], size=5)
    with pytest.raises(
            ValueError,
            match='roi_map does not have the same number of vertices'):
        plot_surf_roi(mesh, roi_map=roi_idx, engine=engine)

    # negative value in roi map
    roi_map[0] = -1
    with pytest.warns(
        DeprecationWarning,
        match="Negative values in roi_map will no longer be allowed",
    ):
        plot_surf_roi(mesh, roi_map=roi_map, engine=engine)

    # float value in roi map
    roi_map[0] = 1.2
    with pytest.warns(
        DeprecationWarning,
        match="Non-integer values in roi_map will no longer be allowed",
    ):
        plot_surf_roi(mesh, roi_map=roi_map, engine=engine)


@pytest.mark.skipif(not is_plotly_installed(),
                    reason=("This test only runs if Plotly is installed."))
@pytest.mark.parametrize(
    "kwargs", [{"vmin": 2}, {"vmin": 2, "threshold": 5}, {"threshold": 5}]
)
def test_plot_surf_roi_colorbar_vmin_equal_across_engines(kwargs):
    """See issue https://github.com/nilearn/nilearn/issues/3944."""
    mesh = generate_surf()
    roi_map = np.arange(0, len(mesh[0]))

    mpl_plot = plot_surf_roi(
        mesh, roi_map=roi_map, colorbar=True, engine="matplotlib", **kwargs
    )
    plotly_plot = plot_surf_roi(
        mesh, roi_map=roi_map, colorbar=True, engine="plotly", **kwargs
    )
    assert (
        mpl_plot.axes[-1].get_ylim()[0] == plotly_plot.figure.data[1]["cmin"]
    )


def test_plot_img_on_surf_hemispheres_and_orientations(img_3d_mni):
    nii = img_3d_mni
    # Check that all combinations of 1D or 2D hemis and orientations work.
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'])
    plot_img_on_surf(nii, hemispheres=['left', 'right'], views=['lateral'])
    plot_img_on_surf(nii,
                     hemispheres=['right'],
                     views=['medial', 'lateral'])
    plot_img_on_surf(nii,
                     hemispheres=['left', 'right'],
                     views=['dorsal', 'medial'])
    # Check that manually set view angles work.
    plot_img_on_surf(nii,
                     hemispheres=['left', 'right'],
                     views=[(210.0, 90.0), (15.0, -45.0)])


def test_plot_img_on_surf_colorbar(img_3d_mni):
    nii = img_3d_mni
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'],
                     colorbar=True, vmin=-5, vmax=5, threshold=3)
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'],
                     colorbar=True, vmin=-1, vmax=5, symmetric_cbar=False,
                     threshold=3)
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'],
                     colorbar=False)
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'],
                     colorbar=False, cmap='roy_big_bl')
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'],
                     colorbar=True, cmap='roy_big_bl', vmax=2)


def test_plot_img_on_surf_inflate(img_3d_mni):
    nii = img_3d_mni
    plot_img_on_surf(nii, hemispheres=['right'], views=['lateral'],
                     inflate=True)


def test_plot_img_on_surf_surf_mesh(img_3d_mni):
    nii = img_3d_mni
    plot_img_on_surf(nii, hemispheres=['right', 'left'], views=['lateral'])
    plot_img_on_surf(nii, hemispheres=['right', 'left'], views=['lateral'],
                     surf_mesh='fsaverage5')
    surf_mesh = fetch_surf_fsaverage()
    plot_img_on_surf(nii, hemispheres=['right', 'left'], views=['lateral'],
                     surf_mesh=surf_mesh)


def test_plot_img_on_surf_with_invalid_orientation(img_3d_mni):
    kwargs = {"hemisphere": ["right"], "inflate": True}
    nii = img_3d_mni
    with pytest.raises(ValueError):
        plot_img_on_surf(nii, views=['latral'], **kwargs)
    with pytest.raises(ValueError):
        plot_img_on_surf(nii, views=['dorsal', 'post'], **kwargs)
    with pytest.raises(TypeError):
        plot_img_on_surf(nii, views=0, **kwargs)
    with pytest.raises(ValueError):
        plot_img_on_surf(nii, views=['medial', {'a': 'a'}], **kwargs)


def test_plot_img_on_surf_with_invalid_hemisphere(img_3d_mni):
    nii = img_3d_mni
    with pytest.raises(ValueError):
        plot_img_on_surf(
            nii, views=['lateral'], inflate=True, hemispheres=["lft]"]
        )
    with pytest.raises(ValueError):
        plot_img_on_surf(
            nii, views=['medial'], inflate=True, hemispheres=['lef']
        )
    with pytest.raises(ValueError):
        plot_img_on_surf(
            nii,
            views=['anterior', 'posterior'],
            inflate=True,
            hemispheres=['left', 'right', 'middle']
        )


def test_plot_img_on_surf_with_figure_kwarg(img_3d_mni):
    nii = img_3d_mni
    with pytest.raises(ValueError):
        plot_img_on_surf(
            nii,
            views=["anterior"],
            hemispheres=["right"],
            figure=True,
        )


def test_plot_img_on_surf_with_axes_kwarg(img_3d_mni):
    nii = img_3d_mni
    with pytest.raises(ValueError):
        plot_img_on_surf(
            nii,
            views=["anterior"],
            hemispheres=["right"],
            inflat=True,
            axes="something",
        )


def test_plot_img_on_surf_with_engine_kwarg(img_3d_mni):
    with pytest.raises(ValueError):
        plot_img_on_surf(
            img_3d_mni,
            views=["anterior"],
            hemispheres=["right"],
            inflat=True,
            engine="something",
        )


def test_plot_img_on_surf_title(img_3d_mni):
    title = "Title"
    fig, _ = plot_img_on_surf(
        img_3d_mni, hemispheres=['right'], views=['lateral']
    )
    assert fig._suptitle is None, "Created title without title kwarg."
    fig, _ = plot_img_on_surf(
        img_3d_mni, hemispheres=['right'], views=['lateral'], title=title
    )
    assert fig._suptitle is not None, "Title not created."
    assert fig._suptitle.get_text() == title, "Title text not assigned."


def test_plot_img_on_surf_output_file(tmp_path, img_3d_mni):
    nii = img_3d_mni
    fname = tmp_path / 'tmp.png'
    return_value = plot_img_on_surf(nii,
                                    hemispheres=['right'],
                                    views=['lateral'],
                                    output_file=str(fname))
    assert return_value is None, "Returned figure and axes on file output."
    assert fname.is_file(), "Saved image file could not be found."


def test_plot_surf_contours():
    mesh = generate_surf()
    # we need a valid parcellation for testing
    parcellation = np.zeros((mesh[0].shape[0],))
    parcellation[mesh[1][3]] = 1
    parcellation[mesh[1][5]] = 2
    plot_surf_contours(mesh, parcellation)
    plot_surf_contours(mesh, parcellation, levels=[1, 2])
    plot_surf_contours(mesh, parcellation, levels=[1, 2], cmap='gist_ncar')
    plot_surf_contours(mesh, parcellation, levels=[1, 2],
                       colors=['r', 'g'])
    plot_surf_contours(mesh, parcellation, levels=[1, 2], colors=['r', 'g'],
                       labels=['1', '2'])
    fig = plot_surf_contours(mesh, parcellation, levels=[1, 2],
                             colors=['r', 'g'],
                             labels=['1', '2'], legend=True)
    assert fig.legends is not None
    plot_surf_contours(mesh, parcellation, levels=[1, 2],
                       colors=[[0, 0, 0, 1], [1, 1, 1, 1]])
    fig, axes = plt.subplots(1, 1, subplot_kw={'projection': '3d'})
    plot_surf_contours(mesh, parcellation, axes=axes)
    plot_surf_contours(mesh, parcellation, figure=fig)
    fig = plot_surf(mesh)
    plot_surf_contours(mesh, parcellation, figure=fig)
    display = plot_surf_contours(mesh, parcellation, levels=[1, 2],
                                 labels=['1', '2'], colors=['r', 'g'],
                                 legend=True, title='title',
                                 figure=fig)
    # Non-regression assertion: we switched from _suptitle to axis title
    assert display._suptitle is None
    assert display.axes[0].get_title() == "title"
    fig = plot_surf(mesh, title='title 2')
    display = plot_surf_contours(mesh, parcellation, levels=[1, 2],
                                 labels=['1', '2'], colors=['r', 'g'],
                                 legend=True, figure=fig)
    # Non-regression assertion: we switched from _suptitle to axis title
    assert display._suptitle is None
    assert display.axes[0].get_title() == "title 2"
    with tempfile.NamedTemporaryFile() as tmp_file:
        plot_surf_contours(mesh, parcellation, output_file=tmp_file.name)
    plt.close()


def test_plot_surf_contours_error(rng):
    mesh = generate_surf()
    # we need an invalid parcellation for testing
    invalid_parcellation = rng.uniform(size=(mesh[0].shape[0]))
    parcellation = np.zeros((mesh[0].shape[0],))
    parcellation[mesh[1][3]] = 1
    parcellation[mesh[1][5]] = 2
    with pytest.raises(
            ValueError,
            match='Vertices in parcellation do not form region.'):
        plot_surf_contours(mesh, invalid_parcellation)
    fig, axes = plt.subplots(1, 1)
    with pytest.raises(
            ValueError,
            match='Axes must be 3D.'):
        plot_surf_contours(mesh, parcellation, axes=axes)
    msg = 'All elements of colors .* matplotlib .* RGBA'
    with pytest.raises(
            ValueError,
            match=msg):
        plot_surf_contours(
            mesh,
            parcellation,
            levels=[1, 2],
            colors=[[1, 2], 3])
    msg = 'Levels, labels, and colors argument .* same length or None.'
    with pytest.raises(
            ValueError,
            match=msg):
        plot_surf_contours(
            mesh,
            parcellation,
            levels=[1, 2],
            colors=['r'],
            labels=['1', '2'])


@pytest.mark.parametrize("vmin,vmax,cbar_tick_format,expected", [
    (0, 0, "%i", [0]),
    (0, 3, "%i", [0, 1, 2, 3]),
    (0, 4, "%i", [0, 1, 2, 3, 4]),
    (1, 5, "%i", [1, 2, 3, 4, 5]),
    (0, 5, "%i", [0, 1.25, 2.5, 3.75, 5]),
    (0, 10, "%i", [0, 2.5, 5, 7.5, 10]),
    (0, 0, "%.1f", [0]),
    (0, 1, "%.1f", [0, 0.25, 0.5, 0.75, 1]),
    (1, 2, "%.1f", [1, 1.25, 1.5, 1.75, 2]),
    (1.1, 1.2, "%.1f", [1.1, 1.125, 1.15, 1.175, 1.2]),
    (0, np.nextafter(0, 1), "%.1f", [0.e+000, 5.e-324]),
])
def test_get_ticks_matplotlib(vmin, vmax, cbar_tick_format, expected):
    ticks = _get_ticks_matplotlib(vmin, vmax, cbar_tick_format, threshold=None)
    assert 1 <= len(ticks) <= 5
    assert ticks[0] == vmin and ticks[-1] == vmax
    assert (
        len(np.unique(ticks)) == len(expected)
        and (np.unique(ticks) == expected).all()
    )


def test_compute_facecolors_matplotlib():
    fsaverage = fetch_surf_fsaverage()
    mesh = load_surf_mesh(fsaverage['pial_left'])
    alpha = "auto"
    # Surface map whose value in each vertex is
    # 1 if this vertex's curv > 0
    # 0 if this vertex's curv is 0
    # -1 if this vertex's curv < 0
    bg_map = np.sign(load_surf_data(fsaverage['curv_left']))
    bg_min, bg_max = np.min(bg_map), np.max(bg_map)
    assert (bg_min < 0 or bg_max > 1)
    facecolors_auto_normalized = _compute_facecolors_matplotlib(
        bg_map,
        mesh[1],
        len(mesh[0]),
        None,
        alpha,
    )
    assert len(facecolors_auto_normalized) == len(mesh[1])

    # Manually set values of background map between 0 and 1
    bg_map_normalized = (bg_map - bg_min) / (bg_max - bg_min)
    assert np.min(bg_map_normalized) == 0 and np.max(bg_map_normalized) == 1
    facecolors_manually_normalized = _compute_facecolors_matplotlib(
        bg_map_normalized,
        mesh[1],
        len(mesh[0]),
        None,
        alpha,
    )
    assert len(facecolors_manually_normalized) == len(mesh[1])
    assert np.allclose(
        facecolors_manually_normalized, facecolors_auto_normalized
    )

    # Scale background map between 0.25 and 0.75
    bg_map_scaled = bg_map_normalized / 2 + 0.25
    assert np.min(bg_map_scaled) == 0.25 and np.max(bg_map_scaled) == 0.75
    facecolors_manually_rescaled = _compute_facecolors_matplotlib(
        bg_map_scaled,
        mesh[1],
        len(mesh[0]),
        None,
        alpha,
    )
    assert len(facecolors_manually_rescaled) == len(mesh[1])
    assert not np.allclose(
        facecolors_manually_rescaled, facecolors_auto_normalized
    )

    with pytest.warns(
        DeprecationWarning,
        match=(
            "The `darkness` parameter will be deprecated in release 0.13. "
            "We recommend setting `darkness` to None"
        ),
    ):
        facecolors_manually_rescaled = _compute_facecolors_matplotlib(
            bg_map_scaled,
            mesh[1],
            len(mesh[0]),
            0.5,
            alpha,
        )


@pytest.mark.skipif(not is_plotly_installed(),
                    reason=("This test only runs if Plotly is installed."))
@pytest.mark.parametrize("avg_method", ["mean", "median"])
@pytest.mark.parametrize("symmetric_cmap", [True, False, None])
@pytest.mark.parametrize("engine", ["matplotlib", "plotly"])
def test_plot_surf_roi_default_arguments(engine, symmetric_cmap, avg_method):
    """Regression test for https://github.com/nilearn/nilearn/issues/3941."""
    mesh, roi_map, _ = _generate_data_test_surf_roi()
    plot_surf_roi(mesh, roi_map=roi_map,
                  engine=engine,
                  symmetric_cmap=symmetric_cmap,
                  darkness=None,  # to avoid deprecation warning
                  cmap="RdYlBu_r",
                  avg_method=avg_method)
