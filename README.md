# Spooksville screen-input macro — calibration-required prototype

Windows PC / Python 3.10+. This is not a Roblox executor script. It reads screen pixels and sends W/A/S/D/E. Check the game's automation rules before using it; account penalties may apply.

## Important limitation
A static map image does NOT reveal your live position. This prototype requires an on-screen **north-up, nonrotating, entire-map view** matching the supplied image, with exactly one distinguishable green player marker. `map_roi` must tightly bound that map's content (no border). A scrolling/zooming minimap is NOT supported. The map must remain visible while movement and the E prompt work. If GPO does not provide that view, this prototype cannot navigate reliably as written; a screenshot of the actual gameplay HUD is needed to design another localization method. Do not simply turn calibration on without meeting these requirements.

There is no mouse/camera correction. Lock the camera heading yourself and do not rotate it while running. Camera-relative movement axes must be measured. Detected obstacles/doors are estimates from a stylized image, not a collision map. Navigation and prompt recognition have not been tested in Roblox.

## Included
- `macro.py`: marker tracking, grid A*, nearest reachable door by route length, keyboard movement, template-based E detection, pause/exit and stuck detection.
- `data/doors.json`: 34 auto-detected candidates; review them, including false positives and missed/occluded doors.
- `data/nav_full.png`: estimated walkability; white is walkable.
- `tools/door_editor.html`: offline editor with embedded map. Show candidates, accept them, drag/add/delete, then download JSON. Replace `data/doors.json` with the download. Sidebar coordinates are scaled editor-image pixels; export converts to original-map pixels. Keep markers near the doorway at a reachable approach location.
- `route_preview.jpg`: illustrative route from the central area to one door, plus candidate labels. Not evidence of in-game navigation success.

## Install and calibrate
1. Unzip the entire folder. Open a terminal there:
   ```powershell
   py -m pip install -r requirements.txt
   ```
2. Review the doors in `tools/door_editor.html` using a normal browser. Click **show auto-detected**, **Accept all auto-detected**, correct markers, and download/replace the JSON. Save it before closing; edits are not persisted automatically.
3. Keep Roblox window placement/resolution and OS display scaling fixed. Set `map_roi` and `prompt_roi` in `config.json`, both `[left, top, width, height]` in screenshot pixels. Map ROI must cover exactly the full map image area.
4. Tune the player-marker HSV range and component area bounds to isolate exactly one green dot. OpenCV hue is 0–179. Zero or multiple candidates pause the macro. Another green map icon can cause ambiguity or misidentification; verify carefully.
5. Measure the marker's map-space displacement while briefly holding W, then D at the locked camera heading. Normalize these directions and enter `w_map_vector` and `d_map_vector`. For a truly north-facing camera, defaults may work; they are not assumed correct for your setup. They must not be parallel.
6. Stand at a door with the E prompt visible. Set a tight prompt ROI and run:
   ```powershell
   py macro.py --capture-prompt
   ```
   There is a 5-second delay to focus the game. Crop `data/e_prompt.png` to the stable E/key icon with an image editor. Keep the configured search ROI larger than the cropped template. Avoid a large changing background or solid-color template. Tune `prompt_threshold` to avoid false positives, especially other E interactions.
7. Only after these checks, set `calibrated` to `true`. Run:
   ```powershell
   py macro.py
   ```
   Focus Roblox. **F7** starts/resumes, **F6** pauses/releases movement, **F8** exits. Remain present for initial tests and keep F8 accessible. Keyboard hooks can behave differently by system permissions. Do not use other apps while active.

## Loop and safeguards
The bot chooses the shortest reachable A* route to an available door. While a door is on cooldown, a configurable disk around its marker is excluded from routing, in addition to estimated building obstacles. This is a conservative approximation, not a verified house footprint; narrow routes can be blocked. If no route is available it waits and retries.

It only presses E when near the selected door and the captured prompt matches twice. It waits 15 seconds afterward and stores a 130-second cooldown from the keypress in `cooldowns.json`, surviving restarts. **A keypress is not confirmation of a successful knock**: the prototype does not recognize reward/animation completion. Failed interactions can therefore be marked on cooldown. E prompts for unrelated interactions are also a possible false positive.

Losing the player marker, being stuck, route timeout, or arriving without an E prompt releases movement and pauses. Fix the configuration/marker and resume. F6/F8 interrupt the animation wait. Exit also releases held movement keys. No automatic camera rotation, obstacle recovery, respawn handling, or scrolling-minimap localization is implemented.

## Tuning
- `clearance_px`: erosion of walkability before routing; increase for collision clearance.
- `cooldown_avoid_px`: radius around cooldown doors to avoid, in original map pixels.
- `max_door_snap_px`: maximum distance from a door to a reachable nav point.
- `knock_radius_px`: proximity gate for E recognition; smaller is safer once calibrated.
- `waypoint_radius_px`: waypoint acceptance distance; decrease if cutting corners.
- `stuck_timeout_s`, `route_timeout_s`: pause thresholds.

Defaults are placeholders, not measured movement calibration. The routing algorithm passed small synthetic obstacle/no-corner-cutting checks and an illustrative map route was generated. Live screen tracking, input, prompt detection and game behavior still require testing on your PC.
