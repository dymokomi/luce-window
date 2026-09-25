#!/usr/bin/env python3
"""Ensure the public text-input API emits only the selected host's native calls."""
import argparse
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler', type=Path, default=ROOT.parent / 'luce-base/build/luce-base')
a = p.parse_args()
with tempfile.TemporaryDirectory(prefix='luce-window-targets-') as directory:
    work = Path(directory)
    source = work / 'probe.lucb'
    # The probe is a package of its own that depends on this one.
    (work / 'package.prisma').write_text('#prisma 4.0\ndef package "window-targets-probe" {\n    str owner = "dymokomi"\n    str version = "0.0.0"\n    str kind = "tool"\n    str language = "luce-base"\n    str entry = "probe.lucb"\n    def dependency "luce-window" {\n        str owner = "dymokomi"\n        str version = "^0.1.0"\n        str path = "' + str(ROOT) + '"\n    }\n}\n')
    source.write_text('''import window
import input
import platform
pub func main(arguments: str[]) -> i32!:
    var host = try window.Window.open(window.Options(title = "Input target contract"))
    defer host.destroy()
    try host.set_text_input(true)
    try host.set_text_input(false)
    try host.set_cursor(input.Cursor.text)
    try host.set_cursor(input.Cursor.resize_horizontal)
    assert((try host.cursor()) == input.Cursor.resize_horizontal)
    discard(try host.wait(1000000))
    try window.wake()
    var lease = try host.acquire_presentation()
    defer lease.destroy()
    if platform.linux:
        discard(try lease.x11_display())
        discard(try lease.x11_window())
    return 0
''')
    for target in ['arm64-macos', 'x86_64-windows', 'x86_64-linux', 'arm64-linux']:
        for level in [0, 3]:
            output = work / 'probe.s'
            subprocess.run([str(a.compiler.resolve()), 'build', str(source), '--target', target,
                            '--native', '--opt', str(level), '--emit=asm', '-o', str(output)], check=True, timeout=120)
            assembly = output.read_text()
            if not target.endswith('macos'):
                for symbol in ['objc_msgSend', 'sel_registerName', 'objc_getClass']:
                    assert symbol not in assembly, (target, level, symbol)
            if target.endswith('linux'):
                for symbol in ['CreateWindowExW', 'DefWindowProcW', 'GetModuleHandleW', 'LoadCursorW', 'SetCursor', 'GetCursorPos',
                               'MsgWaitForMultipleObjectsEx', 'PostThreadMessageW']:
                    assert symbol not in assembly, (target, level, symbol)
            # wait/wake must emit the host's own blocking-pump and thread-safe post
            if target.endswith('macos'):
                for symbol in ['nextEventMatchingMask', 'postEvent:atStart:', 'dateWithTimeIntervalSinceNow:']:
                    assert symbol in assembly, (target, level, symbol)
            if target.endswith('windows'):
                for symbol in ['MsgWaitForMultipleObjectsEx', 'PostThreadMessageW']:
                    assert symbol in assembly, (target, level, symbol)
            # Linux loads Xlib at run time and blocks in poll() on the display and a wake pipe
            if target.endswith('linux'):
                for symbol in ['libX11.so.6', 'XOpenDisplay', 'XCreateSimpleWindow', 'Xutf8LookupString', 'dlopen', 'pipe2', 'poll']:
                    assert symbol in assembly, (target, level, symbol)
            else:
                for symbol in ['libX11.so.6', 'XOpenDisplay']:
                    assert symbol not in assembly, (target, level, symbol)
            print('PASS text input, cursor, wait and wake target', target, level, flush=True)
