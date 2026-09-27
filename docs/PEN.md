# Pens

A pointer event (`input.Event`) says what sent it (`pointer_kind`: mouse, pen,
eraser or touch) and, for a pen, how it is held. The values are the same on
every platform; this page says what each platform reports and how it becomes
them.

## The portable values

| Field | Range | Meaning |
|---|---|---|
| `pressure` | 0..1 | How hard the tip (or eraser) presses. 0 while hovering, and from a mouse. A pen without a sensor reads 1 while touching. |
| `tilt_x`, `tilt_y` | -90..90 degrees | The pen's lean from upright: towards the screen's right (`tilt_x`), towards the user, down the screen (`tilt_y`). The W3C Pointer Events convention. |
| `azimuth` | 0..360 degrees | Which way the pen leans on the tablet plane, clockwise from the screen's right (90 leans down the screen). 0 when upright. |
| `altitude` | 0..90 degrees | How upright it stands: 90 upright, 0 flat. |
| `rotation` | 0..360 degrees | Barrel rotation, clockwise (the Wacom Art Pen's twist). 0 from pens that cannot twist. |
| `tangential` | -1..1 | The airbrush finger wheel; 0 at rest. The Wacom Airbrush only turns it forwards, 0..1. |
| `pointer_kind` | mouse, pen, eraser, touch | The eraser is the pen's other end (or a pen turned over). |

Only tilt is reported on all three platforms, so the azimuth and altitude are
always derived from it, by the W3C Pointer Events formulas
(`input.pen_azimuth`, `input.pen_altitude`; `input.pen_tilt` inverts them):

    azimuth  = atan2(tan(tilt_y), tan(tilt_x))            (0 when upright)
    altitude = atan(1 / sqrt(tan²(tilt_x) + tan²(tilt_y)))  (90 - |tilt| on one axis)

Tablets reach about 60 degrees of tilt (Wacom: ±64), so the altitude rarely
goes below 30.

## macOS (AppKit)

A tablet sends ordinary mouse events whose `subtype` is 1
(`NSEventSubtypeTabletPoint`), plus `NSEventTypeTabletPoint` events when the
pressure changes without a move, and `NSEventTypeTabletProximity` events when
a tool comes near or leaves (or mouse events of subtype 2 carrying the same).
Read on each tablet point:

- `pressure` (a C `float`, 0..1);
- `tilt` (an `NSPoint`, each axis -1..1, y positive up the tablet). Scaled by
  60 degrees and y negated, as Qt does, to the portable degrees;
- `rotation` (`float` degrees, counter-clockwise): turned to clockwise;
- `tangentialPressure` (`float`, -1..1).

The eraser is known from the proximity event: `pointingDeviceType` 3
(`NSPointingDeviceTypeEraser`) versus 1 (pen) or 2 (a puck), kept until the
next proximity event. The view answers `tabletPoint:` and `tabletProximity:`.
macOS has no touch screen; a trackpad is the mouse.

## Windows (Windows Ink, WM_POINTER)

Windows 8 and later send a pen's input as `WM_POINTERDOWN`, `WM_POINTERUPDATE`,
`WM_POINTERUP`, `WM_POINTERENTER` and `WM_POINTERLEAVE`. `GetPointerType` says
`PT_PEN`; `GetPointerPenInfo` gives a `POINTER_PEN_INFO`:

- `pressure` 0..1024 (valid when `PEN_MASK_PRESSURE`): divided by 1024;
- `tiltX`, `tiltY` -90..90 degrees (`PEN_MASK_TILT_X/Y`): already the W3C convention;
- `rotation` 0..359 degrees clockwise (`PEN_MASK_ROTATION`);
- `penFlags`: `PEN_FLAG_INVERTED` (the eraser end hovering) or
  `PEN_FLAG_ERASER` (it pressing) make the eraser; `PEN_FLAG_BARREL` is the
  side button, which also arrives as the second button (`ButtonChangeType` 3, 4).

There is no tangential pressure in Windows Ink. The samples Windows merged
between two messages come from `GetPointerPenInfoHistory` and are queued
oldest first, so fast strokes keep every sample. Handling the pen's messages
(not passing them to `DefWindowProc`) stops Windows turning them into mouse
messages and running press-and-hold right-click.

No Wintab is needed, but the tablet driver must have Windows Ink on (Wacom:
"Use Windows Ink" in the mapping settings). With it off, the pen is a plain
mouse with no pressure.

`EnableMouseInPointer` is not called: the mouse stays on the mouse messages,
which keep their merged-move recovery. A touch is left to `DefWindowProc`
too, and its promoted mouse messages are marked `touch` by their
`GetMessageExtraInfo` signature (`0xFF515700`, bit `0x80` for touch).

## Linux (X11, XInput 2)

Core X events carry no pressure. The X Input Extension 2 does: `libXi.so.6`
is opened at run time (a system without it simply has no pens). The window
selects `XI_Motion`, `XI_ButtonPress` and `XI_ButtonRelease` on each *slave*
device that is a pen: it has an "Abs Pressure" valuator, or its name says it
is an eraser or a touch screen. Selecting on slave devices only leaves the
master pointer's core events flowing, so everything else is unchanged; the
XI2 event records the device's axes and the core event of the same moment
(within 30 ms) takes them.

Axes are found by their labels (xserver-properties.h), as the `wacom` and
`libinput` X drivers set them:

| Label | Value |
|---|---|
| Abs Pressure | pressure, over the axis range |
| Abs Tilt X, Abs Tilt Y | tilt; the drivers report degrees (-64..63); a wider range is scaled to ±60 |
| Abs Wheel, Abs Throttle | tangential (the airbrush wheel), over the range, 0..1 |
| Abs Rotary Z, Abs Z | rotation, over the range, 0..360 |

The wacom driver makes a separate device for each end: "… Pen stylus" and
"… Pen eraser" (libinput: "… Pen (0x…)" and "… Eraser (0x…)"), so the
eraser is the device whose name contains "eraser". XI2 events carry only
the valuators that changed; the last value of each is kept. A tablet plugged
in later is found on `XI_HierarchyChanged`.

The wacom driver may carry an Art Pen's rotation on "Abs Wheel"; then it reads
as the tangential value. `xinput list <device>` shows a tablet's labels.

Under XWayland the tablet appears as `xwayland-tablet stylus:N`,
`xwayland-tablet eraser:N` and a pad, with the Wayland tablet protocol's
ranges (pressure 0..65535, tilt about ±64): every axis is normalized by the
minimum and maximum `XIQueryDevice` reports, never a fixed range.

Wayland is not supported natively: under XWayland, the compositor's tablet
protocol reaches X11 applications as XI2 devices, so the same code applies
where the compositor exposes them.

## Testing

The decoding functions take native values and are tested with synthetic ones
on every host (`luce-base test src/luce_window/window`). Real pens are checked
by hand on each platform.
