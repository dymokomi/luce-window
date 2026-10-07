# luce-window

Native desktop windows for Luce: open, title and size a window, full screen, cursors, text input with the platform input method, keyboard, pointer, touchpad and pen events (pressure, tilt, azimuth and altitude, barrel rotation, the airbrush wheel, eraser versus tip, pen versus mouse versus touch on all three platforms: [docs/PEN.md](docs/PEN.md)), files dragged in from other applications (`drag_entered`, `drag_moved`, `drag_left`, `drop`; `Window.drop_paths`, `Window.set_drop_accepted`), and the system's light or dark appearance.

## Modules

| import | what it holds |
| --- | --- |
| `import input` | Window input events, keys and cursors |
| `import window` | The portable desktop window |

## Waiting for events

`Window.poll()` returns the next event without blocking; `Window.wait(timeout_ns)` blocks until an event arrives or the timeout passes, so an idle program uses no CPU. Two things end a wait early:

- `window.wake()`, from any thread: a worker that finished a job makes the UI respond at once.
- A descriptor given to `window.watch(descriptor, window.Interest.readable)` (or `.writable`, `.both`) turning ready, so a program with sockets open (a browser loading pages) needn't wake on a short timer to poll them. `wait` only returns; find which descriptor is ready with a zero-deadline poll or nonblocking I/O. Readiness is level-triggered, as with `poll`: a descriptor left ready ends every wait until it is read, written or unwatched (`window.unwatch(descriptor)`, before closing it). Up to 64 descriptors.

Each platform adds them to its own wait: `poll` beside the X connection on Linux, a kqueue the main run loop watches on macOS, and a `WSAEventSelect` event beside the message queue on Windows. Sockets and pipes can be watched; on Windows only sockets, which watching makes nonblocking.

## Light and dark

`window.appearance()` returns `input.Appearance.light` or `.dark`: the user's system-wide choice, the same setting CSS reads as `prefers-color-scheme` and AppKit as NSAppearance. It works before any window opens. `Window.appearance()` gives the same answer for an open window, and when the user switches, `poll` and `wait` deliver an `appearance_changed` event whose `appearance` field holds the new value, so a loop handles it like `resized`:

```
if event.kind == input.EventKind.appearance_changed:
    restyle(event.appearance)
```

Where each platform keeps the setting:

- macOS: the global `AppleInterfaceStyle` default (`"Dark"`, or absent for light), and the distributed notification `AppleInterfaceThemeChangedNotification` for changes. The default is read rather than NSApp's `effectiveAppearance` because it answers before AppKit is running (`window.appearance()` with no window open) and the moment the notification arrives; Luce programs set no per-app appearance for `effectiveAppearance` to add.
- Windows: `AppsUseLightTheme` under `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize` (0 is dark), re-read on `WM_SETTINGCHANGE`.
- Linux: the XDG desktop portal's `org.freedesktop.appearance` `color-scheme` (1 prefers dark; 2 and 0, no preference, are light), read over the session D-Bus and followed through the portal's `SettingChanged` signal. libdbus-1 is loaded at run time; without it, a session bus or the portal, the appearance is light.

## Using it

Add the dependency to `package.prisma`; the modules keep their short names:

```prisma
def dependency "luce-window" {
    str owner = "dymokomi"
    str version = "^0.6.0"
}
```

## Depends on

- luce-std

## Platforms

macOS (AppKit), Windows (Win32, OLE drag and drop) and Linux (X11 through Xlib, loaded at run time so no development packages are needed; it runs under Wayland desktops through XWayland; no drag and drop yet; pens through XInput 2, with libXi loaded at run time too; the appearance through libdbus-1, also loaded at run time).

Native libraries it links, by platform (declared in `package.prisma`, linked only when the program reaches code that needs them):

- macos: objc, AppKit, Foundation, CoreFoundation
- windows: user32, ole32, shell32, ws2_32, advapi32

## Tests

`luc test` runs every module's `test` blocks and three test programs: `tests/native_window` (real AppKit windows when a desktop session is there, the X11 or Win32 backend elsewhere; `LUCE_TEST_WINDOW=required|optional|off`), `tests/window_targets` (each target's assembly calls only its own host's API) and `tests/appearance` (reads the system's appearance, and with a desktop checks an open window agrees; `probe.lucb watch SECONDS` prints changes while you switch the setting by hand). On Windows, `python tools/test_windows_native.py` runs the Win32 contracts under `tests/windows` by hand.

## License

MIT or Apache-2.0, at your option.
