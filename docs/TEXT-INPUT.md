# Native committed text

`window.Window.set_text_input(true)` enables committed Unicode characters from
the OS keyboard layout and input method. `input.EventKind.text_input` carries a
single Unicode scalar in `codepoint`. Physical `key_down`/`key_up` events remain
available for navigation and shortcuts; applications must not guess typed text
from USB key positions. Control characters are handled as editing commands.

The macOS adapter implements `NSTextInputClient`, keeps composition storage in
the native view, and copies committed scalars into the portable event queue.
Disabling text input cancels marked text. The Windows adapter combines UTF-16
surrogate pairs from `WM_CHAR` and accepts UTF-32 `WM_UNICHAR` messages. Neither
event type retains OS pointers. Polling returns after a queued event so a control
can update text focus before the next native key is interpreted.

This first API exposes committed text. Inline composition display, surrounding
document replacement and precise candidate-window caret placement remain future
text-service extensions. Oversized macOS commits report queue overflow as a whole
instead of inserting their trailing fragment. Applications must handle overflow.

The macOS desktop regression checks real key interpretation, owned commit data,
supplementary scalars and composition cleanup in six compiler modes. The Windows
contract uses hidden native windows and runs with the CPU/OS suite in seven modes.

Native contracts follow Apple's
[text input client](https://developer.apple.com/documentation/appkit/nstextinputclient)
and Microsoft's [WM_CHAR](https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-char)
and [WM_UNICHAR](https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-unichar)
interfaces.
