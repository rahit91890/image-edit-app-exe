# image-edit-app-exe

A beginner-friendly Windows desktop Image Editor built with Python (PyQt5 + Pillow). It includes a modern GUI with live preview and common editing tools, plus packaging instructions to create a standalone .exe using PyInstaller.

## Features
- Open/Save images (PNG, JPG/JPEG, BMP)
- Crop by dragging on the preview
- Resize (custom width/height)
- Rotate (-90°, +90°)
- Adjust Brightness and Contrast (sliders + Apply)
- Filters: Grayscale, Blur, Sharpen
- Undo/Redo history
- Responsive preview with aspect-fit scaling

## Screenshots
Add your screenshots in the screenshots/ folder and reference them here:
- ![Home UI](screenshots/home.png)
- ![Crop tool](screenshots/crop.png)
- ![Filters](screenshots/filters.png)

## Requirements
- Python 3.9+ (recommended 3.10/3.11 on Windows)
- pip

Install dependencies:
```
pip install -r requirements.txt
```

requirements.txt contains:
```
PyQt5==5.15.11
Pillow==10.4.0
```

## Run from source
```
python main.py
```

## Build Windows .exe with PyInstaller
There are two options below. Option A is the simplest.

### Option A: One-file EXE (recommended)
```
pip install pyinstaller
pyinstaller --noconsole --onefile --name ImageEditApp main.py
```
Artifacts will appear in the dist/ folder as `ImageEditApp.exe`.

### Option B: Using a .spec file
1. Create the spec file automatically:
```
pyi-makespec --noconsole --onefile --name ImageEditApp main.py
```
2. Edit ImageEditApp.spec if needed (add data folders like screenshots or icons)
3. Build with the spec:
```
pyinstaller ImageEditApp.spec
```

Notes:
- If you want a custom icon: add `--icon path/to/icon.ico` to the PyInstaller command
- If you include sample images, add them as data in the spec (e.g., `datas=[('sample_images', 'sample_images')]`)
- If SmartScreen or AV flags the exe, sign the binary or distribute as zip with hash notes

## Project Structure (suggested)
```
image-edit-app-exe/
├─ main.py
├─ requirements.txt
├─ README.md
├─ screenshots/            # add PNG screenshots for the README
└─ sample_images/          # optional demo images to test editing
```

## How it works
- GUI built with PyQt5 (QMainWindow + QLabel preview + control panel)
- Editing powered by Pillow (PIL)
- HistoryStack keeps an in-memory undo/redo stack (up to 20 steps by default)
- Crop is done by dragging on the preview; points are mapped from label space to image space

## Tips & Troubleshooting
- If the preview doesn’t refresh on resize, try toggling a tool; the app automatically re-renders on window resize
- Large images may use more memory; consider downscaling first via Resize
- For JPEG save, alpha is dropped automatically (converted to RGB)

## License
MIT License (see LICENSE)

## Author
- Rahit Biswas (rahit91890) — Codaphics

## Credits
- PyQt5
- Pillow (PIL)
- PyInstaller
