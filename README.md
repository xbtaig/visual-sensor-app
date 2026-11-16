# Visual Sensor App

A small Python desktop app for checking whether wiring, connectors, and clip mates
are present by comparing a live webcam image with a saved master sample. The UI
uses Tkinter; camera capture and image-comparison logic live in separate modules.

## Requirements

- Python 3.10 or later
- A webcam for live inspection (not needed to run tests)
- Windows, macOS, or Linux with Tkinter available

## Setup in Visual Studio Code

1. Open this folder in VS Code and select a Python 3.10+ interpreter.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On macOS/Linux, activate it with `source .venv/bin/activate`.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Start the app from the repository root:

   ```powershell
   python -m webcam_inspector
   ```

Choose a camera index and select **Start camera**. Arrange the complete assembly
in the camera view, with fixed focus, distance, lighting, and fixture position,
then select **Capture master**. The app saves the image as
`data/master_sample/master.jpg` and compares each live frame to it. Red pixels
indicate areas that differ beyond the pixel tolerance. The result is **NG** when
the changed area is larger than the configured allowed percentage.

Use **Pixel tolerance** to ignore small brightness/color changes and **Allowed
changed area (%)** to control how much of the image may differ before an NG.
Select **Save inspection** to store the current image, highlighted overlay, and
JSON result record in `data/inspections/`.

## Project layout

- `webcam_inspector/ui.py` — Tkinter interface and webcam lifecycle
- `webcam_inspector/inspection.py` — independent image comparison
- `webcam_inspector/storage.py` — master and inspection file storage
- `data/master_sample/` — saved master reference image
- `data/inspections/` — saved inspection images and JSON records
- `tests/` — hardware-independent unit tests

Captured master samples and inspection results stay local and are excluded from
Git; the placeholder files keep the dedicated data-folder structure in the repo.

Run tests without a camera:

```powershell
python -m unittest discover -s tests -v
```

## Limitations

This MVP uses direct pixel comparison, not object recognition. It expects the
part and camera view to be aligned consistently; changes in lighting, focus,
fixture position, or background can cause false NG results. Red highlights show
changed image pixels, not a diagnosis of a missing component. Tune the tolerance
and allowed changed area on representative good and faulty assemblies before
using it for production decisions. Selectable inspection regions and automatic
alignment are not implemented.
