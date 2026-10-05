# luce-window

Native desktop windows for Luce: open, title and size a window, full screen, cursors, text input with the platform input method, keyboard, pointer, touchpad and pen events (pressure, tilt, azimuth and altitude, barrel rotation, the airbrush wheel, eraser versus tip, pen versus mouse versus touch on all three platforms: [docs/PEN.md](docs/PEN.md)), and files dragged in from other applications (`drag_entered`, `drag_moved`, `drag_left`, `drop`; `Window.drop_paths`, `Window.set_drop_accepted`).

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

## Using it

Add the dependency to `package.prisma`; the modules keep their short names:

```prisma
def dependency "luce-window" {
    str owner = "dymokomi"
    str version = "^0.5.0"
}
```

## Depends on

- luce-std

## Platforms

macOS (AppKit), Windows (Win32, OLE drag and drop) and Linux (X11 through Xlib, loaded at run time so no development packages are needed; it runs under Wayland desktops through XWayland; no drag and drop yet; pens through XInput 2, with libXi loaded at run time too).

Native libraries it links, by platform (declared in `package.prisma`, linked only when the program reaches code that needs them):

- macos: objc, AppKit, Foundation, CoreFoundation
- windows: user32, ole32, shell32, ws2_32

## Tests

`./test.sh` runs every module's `test` blocks and the unit tests through the native and C backends, then the program checks under `tests/programs`. It expects the compiler beside this checkout at `../luce-base/build/luce-base` (or `--base PATH`).

## License

MIT or Apache-2.0, at your option.
