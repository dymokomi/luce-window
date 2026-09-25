# luce-window

Native desktop windows for Luce: open and size a window, full screen, cursors, text input with the platform input method, keyboard, pointer, touchpad and stylus events, and files dragged in from other applications (`drag_entered`, `drag_moved`, `drag_left`, `drop`; `Window.drop_paths`, `Window.set_drop_accepted`).

## Modules

| import | what it holds |
| --- | --- |
| `import input` | Window input events, keys and cursors |
| `import window` | The portable desktop window |

## Using it

Add the dependency to `package.prisma`; the modules keep their short names:

```prisma
def dependency "luce-window" {
    str owner = "dymokomi"
    str version = "^0.1.0"
}
```

## Depends on

- luce-std

## Platforms

macOS (AppKit), Windows (Win32, OLE drag and drop) and Linux (X11 through Xlib, loaded at run time so no development packages are needed; it runs under Wayland desktops through XWayland; no drag and drop yet).

Native libraries it links, by platform (declared in `package.prisma`, linked only when the program reaches code that needs them):

- macos: objc, AppKit, Foundation
- windows: user32, ole32, shell32

## Tests

`./test.sh` runs every module's `test` blocks and the unit tests through the native and C backends, then the program checks under `tests/programs`. It expects the compiler beside this checkout at `../luce-base/build/luce-base` (or `--base PATH`).

## License

MIT or Apache-2.0, at your option.
