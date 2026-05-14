# Jury Selection Tool

A free, open-source desktop application for organizing juror notes and tracking seat assignments during jury selection.

---

## Features

- **Drag-and-drop seating** — click to assign jurors to seats on a configurable grid
- **Multi-panel support** — manage multiple independent jury panels (e.g., Panel 1, Panel 2, Panel 3)
- **Juror notes** — rich-text notes per juror with strike/pro/defense tracking
- **Final jury tracker** — mark seated jurors as final jury members
- **PDF export** — generate a formatted report of all panels and juror details
- **Autosave** — automatically saves your work at a configurable interval
- **Light and dark themes**
- **Keyboard shortcuts** — `Ctrl+S` save, `Ctrl+O` open, `Ctrl+,` preferences

---

## Installation (Windows)

1. Go to the [**Releases**](https://github.com/hubcap12/Jury-Selection-Tool/releases) page
2. Download **`JuryTool_Setup.exe`** from the latest release
3. Run the installer and follow the prompts
4. Launch **Jury Selection Tool** from the Start Menu or desktop shortcut

No Python installation required — the app is fully self-contained.

---

## Running from Source

If you prefer to run directly from source (requires Python 3.10+):

```bash
git clone https://github.com/hubcap12/Jury-Selection-Tool.git
cd Jury-Selection-Tool
pip install reportlab pillow
python jury.py
```

---

## Saving and Loading

- **Save / Open**: `Ctrl+S` / `Ctrl+O` — saves as a `.json` file you can reopen later
- **Autosave**: Automatically saves to `autosave.json` in your working directory (configurable in Preferences → Misc)
- **Export PDF**: File menu → Export PDF

---

## Transparency / Security

This application is fully open source. The complete source code (`jury.py`) is available in this repository so anyone can inspect exactly what the program does before installing it. No data is ever sent over the internet — everything is stored locally on your machine.

---

## License

MIT License — free to use, modify, and distribute.
