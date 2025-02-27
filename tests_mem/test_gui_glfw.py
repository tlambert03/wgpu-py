"""
Test creation of GLFW canvas windows.
"""

import gc
import weakref
import asyncio

import wgpu
import pytest
from testutils import create_and_release, can_use_glfw, can_use_wgpu_lib
from test_gui import make_draw_func_for_canvas
import testutils  # noqa: F401 - sometimes used in debugging


if not can_use_wgpu_lib:
    pytest.skip("Skipping tests that need wgpu lib", allow_module_level=True)
if not can_use_glfw:
    pytest.skip("Need glfw for this test", allow_module_level=True)

loop = asyncio.get_event_loop_policy().get_event_loop()
if loop.is_running():
    pytest.skip("Asyncio loop is running", allow_module_level=True)


DEVICE = wgpu.utils.get_default_device()


async def stub_event_loop():
    pass


@create_and_release
def test_release_canvas_context(n):
    # Test with GLFW canvases.

    # Note: in a draw, the textureview is obtained (thus creating a
    # Texture and a TextureView), but these are released in present(),
    # so we don't see them in the counts.

    from wgpu.gui.glfw import WgpuCanvas, poll_glfw_briefly

    yield {
        "ignore": {"CommandBuffer"},
    }

    canvases = weakref.WeakSet()

    for i in range(n):
        c = WgpuCanvas()
        canvases.add(c)
        c.request_draw(make_draw_func_for_canvas(c))
        loop.run_until_complete(stub_event_loop())
        yield c.get_context("wgpu")

    # Need some shakes to get all canvas refs gone.
    del c
    loop.run_until_complete(stub_event_loop())
    gc.collect()
    loop.run_until_complete(stub_event_loop())
    gc.collect()

    poll_glfw_briefly()  # removes all windows from screen

    # Check that the canvas objects are really deleted
    assert not canvases, f"Still {len(canvases)} canvases"


if __name__ == "__main__":
    # testutils.TEST_ITERS = 40  # Uncomment for a mem-usage test run

    test_release_canvas_context()
