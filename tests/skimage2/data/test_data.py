import hashlib
from pathlib import Path

import numpy as np
import _skimage2.data as data
import _skimage2.data._fetchers as _fetchers
from _skimage2.data._fetchers import (
    _image_fetcher,
    _default_data_url,
    _stdlib_download,
)
from _skimage2.data._registry import registry_urls
from _skimage2 import io
from _skimage2._shared.testing import (
    assert_equal,
    fetch,
)
from _skimage2._shared._dependency_checks import is_wasm
import os
import pytest


@pytest.mark.thread_unsafe(reason="worker threads would share a download directory")
def test_download_all_with_pooch():
    # jni first wrote this test with the intention of
    # fully deleting the files in the data_dir,
    # then ensure that the data gets downloaded accordingly.
    # hmaarrfk raised the concern that this test wouldn't
    # play well with parallel testing since we
    # may be breaking the global state that certain other
    # tests require, especially in parallel testing

    # The second concern is that this test essentially uses
    # a lot of bandwidth, which is not fun for developers on
    # lower speed connections.
    # https://github.com/scikit-image/scikit-image/pull/4666/files/26d5138b25b958da6e97ebf979e9bc36f32c3568#r422604863
    data_dir = data.data_dir
    if _image_fetcher is not None:
        data.download_all()
        assert 'astronaut.png' in os.listdir(data_dir)
        assert len(os.listdir(data_dir)) > 50
    else:
        with pytest.raises(ModuleNotFoundError):
            data.download_all()


def test_astronaut():
    """Test that "astronaut" image can be loaded."""
    astronaut = data.astronaut()
    assert_equal(astronaut.shape, (512, 512, 3))


def test_camera():
    """Test that "camera" image can be loaded."""
    cameraman = data.camera()
    assert_equal(cameraman.ndim, 2)


def test_checkerboard():
    """Test that "checkerboard" image can be loaded."""
    data.checkerboard()


def test_chelsea():
    """Test that "chelsea" image can be loaded."""
    data.chelsea()


def test_clock():
    """Test that "clock" image can be loaded."""
    data.clock()


def test_coffee():
    """Test that "coffee" image can be loaded."""
    data.coffee()


def test_eagle():
    """Test that "eagle" image can be loaded."""
    # Fetching the data through the testing module will
    # cause the test to skip if pooch isn't installed.
    fetch('data/eagle.png')
    eagle = data.eagle()
    assert_equal(eagle.ndim, 2)
    assert_equal(eagle.dtype, np.dtype('uint8'))


def test_horse():
    """Test that "horse" image can be loaded."""
    horse = data.horse()
    assert_equal(horse.ndim, 2)
    assert_equal(horse.dtype, np.dtype('bool'))


def test_hubble():
    """Test that "Hubble" image can be loaded."""
    data.hubble_deep_field()


def test_immunohistochemistry():
    """Test that "immunohistochemistry" image can be loaded."""
    data.immunohistochemistry()


def test_logo():
    """Test that "logo" image can be loaded."""
    logo = data.logo()
    assert_equal(logo.ndim, 3)
    assert_equal(logo.shape[2], 4)


def test_moon():
    """Test that "moon" image can be loaded."""
    data.moon()


def test_page():
    """Test that "page" image can be loaded."""
    data.page()


def test_rocket():
    """Test that "rocket" image can be loaded."""
    data.rocket()


def test_text():
    """Test that "text" image can be loaded."""
    data.text()


def test_stereo_motorcycle():
    """Test that "stereo_motorcycle" image can be loaded."""
    data.stereo_motorcycle()


def test_lfw_subset():
    """Test that "lfw_subset" can be loaded."""
    data.lfw_subset()


def test_skin():
    """Test that "skin" image can be loaded.

    Needs internet connection.
    """
    skin = data.skin()
    assert skin.ndim == 3


def test_cell():
    """Test that "cell" image can be loaded."""
    data.cell()


def test_cells3d():
    """Needs internet connection."""
    path = fetch('data/cells3d.tif')
    image = io.imread(path)
    assert image.shape == (60, 2, 256, 256)


def test_brain_3d():
    """Needs internet connection."""
    path = fetch('data/brain.tiff')
    image = io.imread(path)
    assert image.shape == (10, 256, 256)


def test_kidney_3d_multichannel():
    """Test that 3D multichannel image of kidney tissue can be loaded.

    Needs internet connection.
    """
    fetch('data/kidney.tif')
    kidney = data.kidney()
    assert kidney.shape == (16, 512, 512, 3)


def test_lily_multichannel():
    """Test that microscopy image of lily of the valley can be loaded.

    Needs internet connection.
    """
    fetch('data/lily.tif')
    lily = data.lily()
    assert lily.shape == (922, 922, 4)


def test_vortex():
    fetch('data/pivchallenge-B-B001_1.tif')
    fetch('data/pivchallenge-B-B001_2.tif')
    image0, image1 = data.vortex()
    for image in [image0, image1]:
        assert image.shape == (512, 512)


@pytest.mark.parametrize(
    'function_name',
    [
        'file_hash',
    ],
)
def test_fetchers_are_public(function_name):
    # Check that the following functions that are only used indirectly in the
    # above tests are public.
    assert hasattr(data, function_name)


# --- stdlib urllib fallback (used when pooch is not installed) ---


def test_default_data_url_uses_registry_urls():
    """A file with a registry_urls entry should resolve to that exact URL."""
    key = next(iter(registry_urls))
    assert _default_data_url(key) == registry_urls[key]


def test_default_data_url_falls_back_to_github_raw():
    """A file with no registry_urls entry falls back to its GitHub raw URL
    under tests/skimage2/, where these test-only fixtures are committed."""
    key = 'color/ciede2000_test_data.txt'
    assert key not in registry_urls
    url = _default_data_url(key)
    assert url.startswith('https://github.com/scikit-image/scikit-image/raw/')
    assert url.endswith(f'/tests/skimage2/{key}')


@pytest.mark.skipif(is_wasm, reason="no access to pytest-localserver")
def test_stdlib_download_success(httpserver, tmp_path):
    content = b'stdlib fallback test content'
    expected_hash = hashlib.sha256(content).hexdigest()
    httpserver.serve_content(content)

    dest_path = tmp_path / 'downloaded.bin'
    result = _stdlib_download(httpserver.url, str(dest_path), expected_hash)

    assert result == str(dest_path)
    assert dest_path.read_bytes() == content
    assert not Path(f'{dest_path}.part').exists()


@pytest.mark.skipif(is_wasm, reason="no access to pytest-localserver")
def test_stdlib_download_hash_mismatch(httpserver, tmp_path):
    httpserver.serve_content(b'unexpected content')
    dest_path = tmp_path / 'downloaded.bin'

    with pytest.raises(ValueError, match='Hash mismatch'):
        _stdlib_download(httpserver.url, str(dest_path), '0' * 64)

    assert not dest_path.exists()
    assert not Path(f'{dest_path}.part').exists()


def test_stdlib_download_connection_error(tmp_path):
    dest_path = tmp_path / 'downloaded.bin'

    with pytest.raises(ConnectionError):
        _stdlib_download('http://127.0.0.1:1/unreachable', str(dest_path), '0' * 64)

    assert not dest_path.exists()
    assert not Path(f'{dest_path}.part').exists()


@pytest.mark.thread_unsafe(reason="mutates process-wide environment variables")
def test_skip_pytest_case_requiring_pooch_fires_during_collection(monkeypatch):
    """``PYTEST_VERSION`` is set for the whole session (including collection),
    unlike ``PYTEST_CURRENT_TEST`` (only set while a test's call/setup/teardown
    phase runs). Module- and class-level data fetches (e.g. ``IMG =
    data.astronaut()``) execute during collection, so the guard must also
    fire on ``PYTEST_VERSION`` alone."""
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    monkeypatch.setenv('PYTEST_VERSION', '9.0.0')
    with pytest.raises(pytest.skip.Exception):
        _fetchers._skip_pytest_case_requiring_pooch('data/does_not_matter.png')


@pytest.mark.thread_unsafe(reason="mutates process-wide environment variables")
def test_skip_pytest_case_requiring_pooch_noop_outside_pytest(monkeypatch):
    """Without any pytest marker env var, the guard must not skip -- it
    should only intervene when actually running under pytest."""
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    monkeypatch.delenv('PYTEST_VERSION', raising=False)
    # Should return normally; raises if it unexpectedly tries to skip.
    _fetchers._skip_pytest_case_requiring_pooch('data/does_not_matter.png')


@pytest.mark.thread_unsafe(reason="monkeypatches shared fetcher module state")
@pytest.mark.skipif(is_wasm, reason="no access to pytest-localserver")
def test_fetch_without_pooch_uses_stdlib_download(httpserver, tmp_path, monkeypatch):
    """End-to-end: `_fetch` downloads via urllib when pooch is unavailable."""
    content = b'stdlib fallback integration test content'
    expected_hash = hashlib.sha256(content).hexdigest()
    httpserver.serve_content(content)

    test_key = 'data/_test_stdlib_fallback.bin'
    monkeypatch.setattr(_fetchers, '_image_fetcher', None)
    monkeypatch.setattr(
        _fetchers, '_skip_pytest_case_requiring_pooch', lambda *a, **kw: None
    )
    monkeypatch.setitem(_fetchers.registry, test_key, expected_hash)
    monkeypatch.setitem(_fetchers.registry_urls, test_key, httpserver.url)
    monkeypatch.setenv('SKIMAGE_DATADIR', str(tmp_path))

    result_path = _fetchers._fetch(test_key)

    assert Path(result_path).read_bytes() == content
