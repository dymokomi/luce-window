# System cursors

`input.Cursor` describes intent without depending on a window system:
`arrow`, `text`, `pointer`, `resize_horizontal`, `resize_vertical`, `grab`,
`grabbing`, and `not_allowed`. `window.Window.set_cursor(cursor)` applies the
choice to that window's content; `cursor()` returns its current choice. Calls
require the main thread and an open window. Invalid enum values are rejected.

The macOS adapter uses shared NSCursor objects and restores its choice through
`cursorUpdate:` tracking events. Windows handles `WM_SETCURSOR` only for the
client area and uses shared system resources. Its standard move cursor represents
both grab states. Native title bars and borders retain OS cursor behavior.
Changing another window's stored choice does not set the cursor over this one.
An unchanged choice does not repeatedly call the native cursor setter.

Linux has the same portable enum; native Window operations continue to report
`unsupported` until that window backend is implemented. No platform identifiers
or native cursor handles escape the window package.

The UI framework chooses cursors from its own hit testing and pointer capture.
Applications should not recreate platform cursor policies in their controls.

## Verification

- Native AppKit tests exercise all shapes, invalid/closed calls, cursor-update
  restoration and two-window isolation in native levels 0–3 and both C modes.
- The Windows hidden-window contract checks all shapes through WM_SETCURSOR and
  GetCursor. Hosted Windows CI executes it; it also compiles to Windows assembly
  on the development host.
- Target checks include cursor methods and reject foreign native dependencies.
- All three bootstrap snapshots and embedded standard sources are refreshed.

Native behavior follows Apple's [cursor update contract](https://developer.apple.com/documentation/appkit/nsresponder/cursorupdate(with:))
and Microsoft's [cursor selection contract](https://learn.microsoft.com/en-us/windows/win32/learnwin32/setting-the-cursor-image).
