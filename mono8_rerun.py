#!/usr/bin/env python

import argparse

import time
import rerun as rr  # pip install rerun-sdk
import rerun.blueprint as rrb
import numpy as np
import pycameleon
import os
from numba import jit, njit, prange
import re
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Convert any string into a safe filename."""
    # Replace invalid filename characters with underscores
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    # Optional: trim spaces and limit length
    safe = safe.strip().replace(" ", "_")[:255]
    return safe or "untitled"


def read_xml_to_string(name: str, directory: str = ".") -> str:
    """Sanitize filename and write content safely."""
    safe_name = sanitize_filename(name)
    path = Path(directory) / f"{safe_name}.xml"
    if not path.exists():
        print("Run `dumpgenapi.py` first to extract Gen Api Context as XML!")
        raise FileNotFoundError(f"XML file not found: {path}")
    xml = path.read_text(encoding="utf-8")
    return xml


def run_viewer() -> None:
    # Create a new video capture

    frame_nr = 0
    cam = pycameleon.enumerate_cameras()[0]
    try:
        cam.close()
        cam.open()
        cam.load_context_from_xml(read_xml_to_string(str(cam)))
        cam.execute("DeviceReset")
        cam.close()
        time.sleep(5)

        cam = pycameleon.enumerate_cameras()[0]
        cam.open()
        cam.load_context_from_xml(read_xml_to_string(str(cam)))
        payload = cam.start_streaming(1)

        while True:
            # Read the frame
            img = cam.receive(payload)

            frame_time_ms = 0
            if frame_time_ms != 0:
                rr.set_time("frame_time", duration=1e-3 * frame_time_ms)

            rr.set_time("frame_nr", sequence=frame_nr)
            frame_nr += 1

            # Log the original image
            # rr.log("image/rgb", rr.Image(img, color_model="BGR"))
            rr.log("image/mono8", rr.Image(img))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cam.close()
        print("Camera closed")
        exit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Streams a U3V camera as Mono8 image")

    rr.script_add_args(parser)
    args = parser.parse_args()

    rr.script_setup(
        args,
        "rerun_mono8",
        default_blueprint=rrb.Vertical(
            rrb.Spatial2DView(origin="/image/mono8", name="Video"),
        ),
    )

    # rr.spawn(memory_limit="1GB", server_memory_limit="1GB")
    run_viewer()

    rr.script_teardown(args)


if __name__ == "__main__":
    main()
