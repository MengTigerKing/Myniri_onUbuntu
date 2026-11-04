# Lock screen styles

Settings Center → Theme → Lock screen selects `default` or `caelestia`.
The selection is saved as `theme.lockScreenStyle` in the personalization config.
Missing or invalid values use `default`; each lock session keeps its initial selection.

`CaelestiaLock.qml` preserves the original card layout and renders the current
wallpaper through a strong Qt Quick `MultiEffect` blur. `DefaultLock.qml` reveals a
blurred wallpaper over a frozen pre-lock desktop frame, with authentication UI
in `DefaultLockContent.qml`. Both styles share the session lock and PAM context.
The Caelestia style uses the wallpaper directly so application windows and desktop
panels do not show through the lock screen. The default style keeps the snapshot
underneath its wallpaper layer for the top-left disc reveal and exit fade.
Both styles capture through a short-lived Quickshell `ScreencopyView` config before
acquiring the session lock. No external screenshot program is required. The helper
uses a private temporary directory in XDG_RUNTIME_DIR (TMPDIR fallback) for a BMP.
It returns the local path and holds the file until the main shell releases its stdin
lease at unlock/cancellation. Main-shell Image preloading completes before requesting
the session lock; display Images reuse the same URL and decoded image cache.
There is no PNG/base64/data-URL round trip. The wallpaper itself is sourced from the
current wallpaper image.

Manual visual checks in a graphical session:

- Select each style and lock using the normal shell action.
- Verify the default style with image/solid-color wallpaper and multiple outputs.
- Verify 12-hour AM/PM and 24-hour clocks, and the date at midnight.
- Type, delete, submit an incorrect password, then authenticate successfully.
- Press Escape to clear input and restore the clock; click to reveal authentication.
- Verify the Caelestia style shows only the blurred wallpaper without a black flash.
- Verify the default style reveals the blurred wallpaper over the desktop snapshot.

If capture fails or times out, locking still proceeds. Default shows the wallpaper
without a disc reveal or a fade to a missing snapshot. The main shell does not
create a ScreencopyView: native capture stays on a separate Wayland connection
until the helper exits. The helper is bounded by a 1.5-second timeout.

No real session lock is started by development checks.
