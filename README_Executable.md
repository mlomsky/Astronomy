# Creating Executable for Viewing Tonight Astronomy Program

## Quick Start (Recommended Method)

1. **Install PyInstaller** (already done):
   ```
   pip install pyinstaller
   ```

2. **Run the build script**:
   ```
   python build_executable.py
   ```
   
   OR run the batch file:
   ```
   build_executable.bat
   ```

## Manual Method

If you prefer to build manually, use this command in your astronomy folder:

```bash
pyinstaller --onefile --windowed --name "ViewingTonight" --add-data "Messier.py;." --hidden-import=astropy --hidden-import=matplotlib --hidden-import=numpy --hidden-import=pandas --hidden-import=geopy --hidden-import=requests --hidden-import=astral --hidden-import=tkinter --hidden-import=multiprocessing Viewing_Tonight.py
```

## What the Build Options Mean

- `--onefile`: Creates a single executable file (no separate folders needed)
- `--windowed`: Hides the console window (since it's a GUI app)
- `--name "ViewingTonight"`: Sets the executable name
- `--add-data "Messier.py;."`: Includes the Messier.py module in the executable
- `--hidden-import`: Tells PyInstaller to include specific modules that might not be auto-detected

## Required Files Before Building

Make sure these files are in your astronomy folder:
- `Viewing_Tonight.py` (main program)
- `Messier.py` (astronomy data module)
- `viewing_targets.json` (optional, but recommended)

## Expected Output

After successful build:
- Executable will be in: `dist/ViewingTonight.exe`
- Size: Approximately 50-100 MB
- Can run on any Windows computer (no Python installation required)

## Alternative Methods

### Method 2: cx_Freeze
```bash
pip install cx_freeze
python setup_cx_freeze.py build
```

### Method 3: Auto-py-to-exe (GUI)
```bash
pip install auto-py-to-exe
auto-py-to-exe
```

## Troubleshooting

### Common Issues:

1. **"Module not found" errors**: Add missing modules with `--hidden-import=module_name`

2. **Large file size**: This is normal for astronomy programs with many dependencies

3. **Antivirus warnings**: Some antivirus software flags PyInstaller executables as suspicious

4. **Missing data files**: Use `--add-data` for any JSON or data files your program needs

### If WeasyPrint/PDF issues persist:
The executable will automatically fall back to browser-based PDF generation or provide clear instructions for manual PDF creation.

## Distribution

The final executable (`ViewingTonight.exe`) can be:
- Copied to any Windows computer
- Run without Python installation
- Shared with other astronomy enthusiasts
- Used on computers without internet (except for coordinate lookups)

## Performance Notes

- First startup may be slower (15-30 seconds) as the executable unpacks
- Subsequent runs will be faster
- All astronomy calculations run at full speed
- Parallel processing for Messier objects will work normally
