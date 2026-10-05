#!/usr/bin/env python3
"""Exercise actual AppKit objects across native optimization levels and C.

All generated files live in a temporary directory. LUCE_TEST_WINDOW=required
runs the GUI checks; optional runs them when a desktop is available, otherwise
records the missing coverage. off explicitly runs only non-GUI contracts. On
Linux, required with DISPLAY set demands that the X11 window really opens.
"""
from pathlib import Path
import ctypes
import os
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
COMPILER = Path(sys.argv[1]).resolve()


def run(command, *, expected=None, timeout=90):
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    if result.returncode or (expected is not None and result.stdout.strip() != expected):
        raise AssertionError(f"{command}\nstatus={result.returncode}\n{result.stdout}{result.stderr}")
    return result.stdout


def desktop_available():
    # A display alone does not imply a logged-in desktop (for example hosted CI).
    graphics = ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    foundation = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    graphics.CGSessionCopyCurrentDictionary.restype = ctypes.c_void_p
    foundation.CFRelease.argtypes = [ctypes.c_void_p]
    session = graphics.CGSessionCopyCurrentDictionary()
    if session:
        foundation.CFRelease(session)
    return bool(session)


def main():
    mac = platform.system() == 'Darwin' and platform.machine() == 'arm64'
    machine = platform.machine().lower()
    backend = (platform.system() == 'Linux' and machine in {'x86_64', 'amd64', 'aarch64', 'arm64'}) or (platform.system() == 'Windows' and machine in {'amd64', 'x86_64'})
    policy = os.environ.get('LUCE_TEST_WINDOW', 'optional')
    if policy not in {'required', 'optional', 'off'}:
        raise ValueError('LUCE_TEST_WINDOW must be required, optional, or off')
    gui = mac and policy != 'off' and desktop_available()
    if mac and policy == 'required' and not gui:
        raise AssertionError('native window tests require a logged-in macOS desktop')
    with tempfile.TemporaryDirectory(prefix='luce-window-test-') as temporary:
        work = Path(temporary)
        for source in SOURCE.glob('*.lucb'):
            shutil.copy2(source, work / source.name)
        dependency = f'    def dependency "luce-window" {{\n        str owner = "dymokomi"\n        str version = "^0.1.0"\n        str path = "{ROOT}"\n    }}\n'
        manifest = '#prisma 4.0\ndef package "native-window-test" {\n' + dependency
        if mac:
            manifest += '    def native "inputs" {\n        str[] frameworks = ["CoreGraphics"]\n    }\n'
        (work / 'package.prisma').write_text(manifest + '}\n')
        modes = [(f'native-{level}', ['--native', '--opt', str(level)]) for level in range(4)]
        modes += [('c', ['--backend=c']), ('c-release', ['--backend=c', '--release'])]
        for name, flags in modes:
            binary = work / name
            # macOS runs the full probe; Linux and Windows have a backend
            # (supported.lucb); any other host must refuse (unsupported.lucb).
            other = 'supported' if backend else 'unsupported'
            entry = work / ('probe.lucb' if mac else other + '.lucb')
            run([str(COMPILER), 'build', str(entry), *flags, '-o', str(binary)])
            if mac:
                run([str(binary)], expected='ok window contracts without WindowServer')
            elif other == 'unsupported':
                run([str(binary)], expected='ok unsupported window target')
            else:
                # The probe says "(opened)" only when a real window opened; with a display
                # and LUCE_TEST_WINDOW=required, a refused window fails the gate.
                output = run([str(binary)]).strip()
                opened = output == 'ok supported window target (opened)'
                assert opened or output == 'ok supported window target', output
                if policy == 'required' and os.environ.get('DISPLAY') and platform.system() == 'Linux':
                    assert opened, 'LUCE_TEST_WINDOW=required with DISPLAY set, but no X11 window opened'
                print(f'native_window {name}: ' + ('a window opened' if opened else 'no window (refused as unsupported)'), flush=True)
            if gui:
                run([str(binary), 'gui'], expected='ok native window lifecycle, ABI, input, isolation, and overflow')
            if mac:
                assert 'SDL' not in run(['otool', '-L', str(binary)]), 'native window linked SDL'
            print(f'ok native_window {name}' + (' (GUI)' if gui else ' (contracts)'), flush=True)
        # A portable input-only program must not acquire AppKit linkage.
        (work / 'package.prisma').write_text('#prisma 4.0\ndef package "input_only" {\n' + dependency + '}\n')
        (work / 'input_only.lucb').write_text('from luce_window import input\npub func main(arguments: str[]) -> i32:\n    _ = arguments\n    assert((u16)input.Key.a == 4)\n    return 0\n')
        binary = work / 'input-only'
        run([str(COMPILER), 'build', str(work / 'input_only.lucb'), '-o', str(binary)])
        run([str(binary)])
        if mac:
            dependencies = run(['otool', '-L', str(binary)])
            assert 'AppKit' not in dependencies and 'SDL' not in dependencies
    if mac and not gui:
        message = 'skip native_window GUI: no desktop session or LUCE_TEST_WINDOW=off; contracts passed'
        print(message)
        (ROOT / 'build').mkdir(exist_ok=True)
        with (ROOT / 'build/hardware-skip.txt').open('a') as record:
            record.write(message + '\n')


if __name__ == '__main__':
    main()
