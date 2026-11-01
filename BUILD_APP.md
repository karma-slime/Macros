# Portable Windows app — source and online build

This download contains application source, NOT a precompiled EXE. The current workspace is Linux, so the Windows app has not been compiled or tested here.

## Build online without installing Python on your PC
1. Create an empty repository on GitHub (a free account is sufficient; build availability/quotas depend on account settings).
2. Extract this ZIP. Upload `gpo_macro` and `.github/workflows/build-windows.yml` into the repository root. Make sure the hidden `.github` directory is included. You can create the workflow file through the website if your upload tool hides dot folders.
3. Open the repository's **Actions** tab. Enable workflows if asked. Select **Build portable Windows app**, then **Run workflow**. A push to `main` or `master` also triggers it.
4. When the run finishes successfully, open it and download the **Spooksville-Windows-Portable** artifact. Extract the downloaded artifact, then extract `Spooksville-Windows-Portable.zip` inside it.
5. Keep the entire `Spooksville` folder together in a writable location such as Documents. Launch `Spooksville.exe`. No Python or pip installation is needed on the PC that runs the resulting app. Windows x64 only; not a phone/browser app.

The EXE has a GUI and a diagnostic console window. Do not close the console while movement is active; stop with F8 first. The GUI has settings, a door-editor launcher, prompt capture and worker logs. It does not remove the underlying macro's calibration requirements. Read the included README before enabling movement. Opening Markdown/image/HTML files uses Windows' default applications.

A self-built unsigned executable may trigger reputation warnings or antivirus false positives. Inspect the source and build logs; do not disable security software or run unknown binaries. This app does not need a Roblox password. No bypass of Roblox input or anti-cheat restrictions is included.

## Optional local developer build
On Windows with Python 3.11 installed, run the commands in the workflow's Package application step after installing requirements and PyInstaller. Python is only needed on the build machine, not the destination PC.

## Current validation
Python syntax and routing checks passed in Linux. Windows packaging, GUI interaction, global hotkeys and Roblox behavior remain untested. A failed online build will show its error in the Actions log; share that error for troubleshooting.
