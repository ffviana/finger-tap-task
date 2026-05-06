#!/usr/bin/python
"""
Simple TR-based finger movement task.

Events:
- rest: fixation cross only
- move: fixation cross with a circle around it

Before trigger wait, shows instructions:
"Move your index finger when a circle appear around the cross"

Trigger modes:
- --trigger_mode kbd    -> press 't'
- --trigger_mode cedrus -> Cedrus / pyxid2 MRI trigger

ESC aborts anytime.
"""

from argparse import ArgumentParser
from datetime import datetime

import numpy as np
if not hasattr(np, "product"):
    np.product = np.prod


# ---------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------
def parse_csv_str(s):
    return [x.strip().lower() for x in s.split(",") if x.strip()]


def parse_csv_int(s):
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def validate_sequence(sequence, event_trs):
    allowed = {"rest", "move"}

    for event in sequence:
        if event not in allowed:
            raise ValueError(f"Unknown event '{event}'. Use only: rest, move.")

    if len(sequence) != len(event_trs):
        raise ValueError(
            f"--sequence has {len(sequence)} events, but --event_trs has "
            f"{len(event_trs)} values."
        )

    return sequence, event_trs


# ---------------------------------------------------------------------
# CLI arguments
# ---------------------------------------------------------------------
parser = ArgumentParser(description="Simple TR-based finger movement task")

parser.add_argument("--TR", type=float, default=3.35)
parser.add_argument("--frate", type=float, default=60.0)

parser.add_argument(
    "--sequence",
    type=str,
    default="rest,move,rest,move,rest",
    help="Comma-separated event sequence using rest/move.",
)

parser.add_argument(
    "--event_trs",
    type=str,
    default="10,10,10,10,10",
    help="Comma-separated TR durations for each event.",
)

parser.add_argument("--trigger_mode", choices=["kbd", "cedrus"], default="kbd")
parser.add_argument("--mri_trigger_port", type=int, default=2)
parser.add_argument("--trigger_timeout", type=float, default=1e6)

args = parser.parse_args()

sequence = parse_csv_str(args.sequence)
event_trs = parse_csv_int(args.event_trs)
sequence, event_trs = validate_sequence(sequence, event_trs)


# =====================================================================
# PsychoPy execution
# =====================================================================
from psychopy import visual, core, event, gui


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
LOG_FH = None


def cli(msg):
    print(msg, flush=True)


def log_line(msg):
    if LOG_FH is not None:
        LOG_FH.write(msg + "\n")


def check_for_abort():
    if event.getKeys(keyList=["escape"]):
        log_line("Experiment aborted by user with ESC")
        cli("Experiment aborted by user with ESC")
        return True
    return False


# ---------------------------------------------------------------------
# Cedrus helpers
# ---------------------------------------------------------------------
def get_cedrus_triggers(dev, mri_trigger_port):
    triggers = []

    dev.poll_for_response()

    while dev.has_response():
        response = dev.get_next_response()

        if response.get("port", None) == mri_trigger_port:
            log_line(f"MRI_TRIGGER {response}")
            cli(f"MRI_TRIGGER {response}")
            triggers.append(response)
        else:
            log_line(f"DEVICE_RESPONSE {response}")

    return triggers


def wait_for_cedrus_trigger(dev, mri_trigger_port, timeout):
    dev.clear_response_queue()

    clock = core.Clock()

    while clock.getTime() < timeout:
        if check_for_abort():
            return False

        triggers = get_cedrus_triggers(dev, mri_trigger_port)

        if triggers:
            log_line("MRI trigger received")
            cli("MRI trigger received")
            return True

        core.wait(0.001)

    return False


# ---------------------------------------------------------------------
# GUI and logfile
# ---------------------------------------------------------------------
expInfo = {"subject": "phtm", "run": 1}
dlg = gui.DlgFromDict(expInfo, title="Finger movement task")

if not dlg.OK:
    raise SystemExit(0)

theDate = datetime.now()

logFn = (
    f"finger-move-s-{expInfo['subject']}-r-{expInfo['run']}-"
    f"{theDate.strftime('%d%b%y')}.log"
)

LOG_FH = open(logFn, "w", buffering=1)

log_line(f"TR={args.TR}")
log_line(f"frate={args.frate}")
log_line(f"sequence={sequence}")
log_line(f"event_trs={event_trs}")
log_line(f"trigger_mode={args.trigger_mode}")

cli(f"Logging to: {logFn}")


# ---------------------------------------------------------------------
# Window and stimuli
# ---------------------------------------------------------------------
win = visual.Window(
    size=(1600, 1200),
    fullscr=True,
    screen=1,
    allowGUI=True,
    winType="pyglet",
    monitor="testMonitor",
    units="norm",
)

fixation = visual.TextStim(
    win,
    text="+",
    pos=(0, 0),
    height=0.12,
    color="white",
)

circle = visual.Circle(
    win,
    radius=0.12,
    edges=128,
    lineWidth=4,
    lineColor="white",
    fillColor=None,
    pos=(0, 0),
)

instruction_text = visual.TextStim(
    win,
    text="Move your index finger when a circle appear around the cross",
    pos=(0, 0.45),
    height=0.06,
    color="white",
    wrapWidth=1.5,
)

demo_cross_still = visual.TextStim(
    win,
    text="+",
    pos=(-0.35, 0.05),
    height=0.12,
    color="white",
)

demo_label_still = visual.TextStim(
    win,
    text="stay still",
    pos=(-0.35, -0.18),
    height=0.045,
    color="white",
)

demo_cross_move = visual.TextStim(
    win,
    text="+",
    pos=(0.35, 0.05),
    height=0.12,
    color="white",
)

demo_circle_move = visual.Circle(
    win,
    radius=0.12,
    edges=128,
    lineWidth=4,
    lineColor="white",
    fillColor=None,
    pos=(0.35, 0.05),
)

demo_label_move = visual.TextStim(
    win,
    text="move finger",
    pos=(0.35, -0.18),
    height=0.045,
    color="white",
)


# ---------------------------------------------------------------------
# Cedrus initialization
# ---------------------------------------------------------------------
cedrus = None

if args.trigger_mode == "cedrus":
    import pyxid2

    devices = pyxid2.get_xid_devices()

    if not devices:
        raise RuntimeError("No Cedrus device found. Check USB connection.")

    cedrus = devices[0]

    try:
        cedrus.reset_base_timer()
    except Exception:
        pass

    cedrus.clear_response_queue()


def poll_cedrus_during_task():
    if cedrus is not None:
        get_cedrus_triggers(cedrus, args.mri_trigger_port)


# ---------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------
def draw_instruction_screen():
    instruction_text.draw()

    demo_cross_still.draw()
    demo_label_still.draw()

    demo_circle_move.draw()
    demo_cross_move.draw()
    demo_label_move.draw()

    win.flip()


def draw_rest():
    fixation.draw()


def draw_move():
    circle.draw()
    fixation.draw()


# ---------------------------------------------------------------------
# Event runner
# ---------------------------------------------------------------------
timer = core.Clock()


def run_event(event_type, tr_count, frame_idx):
    nframes = int(round(tr_count * args.TR * args.frate))

    log_line(f"EVENT_BEGIN type={event_type} TRs={tr_count} frames={nframes}")
    cli(f"EVENT_BEGIN type={event_type} TRs={tr_count}")

    for _ in range(nframes):
        if check_for_abort():
            return frame_idx, False

        poll_cedrus_during_task()

        if event_type == "rest":
            draw_rest()
        elif event_type == "move":
            draw_move()
        else:
            raise ValueError(f"Unknown event type: {event_type}")

        log_line(
            f"FRAME frame={frame_idx} "
            f"time={timer.getTime():.6f} "
            f"event={event_type} "
            f"TR={frame_idx // int(args.TR * args.frate)}"
        )

        win.flip()
        frame_idx += 1

    log_line(f"EVENT_END type={event_type}")
    cli(f"EVENT_END type={event_type}")

    return frame_idx, True


# ---------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------
try:
    draw_instruction_screen()

    if args.trigger_mode == "kbd":
        cli("Waiting for keyboard trigger: press 't'")

        while True:
            keys = event.getKeys()

            if "t" in keys:
                log_line("Keyboard trigger received")
                cli("Keyboard trigger received")
                break

            if "escape" in keys:
                log_line("Experiment aborted during trigger wait")
                cli("Experiment aborted during trigger wait")
                raise SystemExit(0)

            core.wait(0.01)

    else:
        cli(f"Waiting for Cedrus MRI trigger, port={args.mri_trigger_port}")
        log_line(f"Waiting for Cedrus MRI trigger, port={args.mri_trigger_port}")

        ok = wait_for_cedrus_trigger(
            cedrus,
            mri_trigger_port=args.mri_trigger_port,
            timeout=args.trigger_timeout,
        )

        if not ok:
            log_line("MRI trigger timeout or abort")
            cli("MRI trigger timeout or abort")
            raise SystemExit(0)

    timer.reset()
    log_line("Experiment started")
    cli("Experiment started")

    frame_idx = 0

    for event_type, tr_count in zip(sequence, event_trs):
        frame_idx, ok = run_event(event_type, tr_count, frame_idx)

        if not ok:
            raise SystemExit(0)

    log_line("Experiment finished")
    cli("Experiment finished")

finally:
    try:
        if LOG_FH is not None:
            LOG_FH.flush()
            LOG_FH.close()
    except Exception:
        pass

    try:
        win.close()
    except Exception:
        pass

    core.quit()