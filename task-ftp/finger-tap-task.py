#!/usr/bin/python
"""
Simple TR-based fingertapping task.

Structure:
- General instructions before trigger
- After trigger:
    - optional initial_fixation
    - instruction before each block
    - task block with fixation cross only

Events:
- rest: "Don't move"
- move: "Do fingertapping when the cross appears"

All task blocks show only a fixation cross.

python finger-tap-task.py --TR 1.00 \
  --sequence rest,move,rest,move,rest \
  --block_trs 10,10,10,10,10 \
  --instruction_trs 2 \
  --initial_fixation_trs 2 \
  --trigger_mode kbd

python finger-tap-task.py --TR 1.50 --sequence rest,move,rest,move,rest,move,rest,move,rest,move --block_trs 20,20,20,20,20,20,20,20,20,20 --instruction_trs 4 --initial_fixation_trs 4 --trigger_mode kbd
python finger-tap-task.py --TR 1.50 --sequence rest,move,rest,move,rest,move,rest,move,rest,move,rest --block_trs 20,20,20,20,20,20,20,20,20,20,4 --instruction_trs 4 --initial_fixation_trs 4 --trigger_mode cedrus

"""

from argparse import ArgumentParser
from datetime import datetime

import numpy as np
if not hasattr(np, "product"):
    np.product = np.prod

# ---------------------------------------------------------------------
# Font sizes
# ---------------------------------------------------------------------
FIXATION_HEIGHT = 0.12
GENERAL_INSTRUCTION_HEIGHT = 0.12
BLOCK_INSTRUCTION_HEIGHT = 0.12


# ---------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------
def parse_csv_str(s):
    return [x.strip().lower() for x in s.split(",") if x.strip()]


def parse_csv_int(s):
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def validate_sequence(sequence, block_trs):
    allowed = {"rest", "move"}

    for block in sequence:
        if block not in allowed:
            raise ValueError(f"Unknown block '{block}'. Use only: rest, move.")

    if len(sequence) != len(block_trs):
        raise ValueError(
            f"--sequence has {len(sequence)} blocks, but --block_trs has "
            f"{len(block_trs)} values."
        )

    return sequence, block_trs


# ---------------------------------------------------------------------
# CLI arguments
# ---------------------------------------------------------------------
parser = ArgumentParser(description="Simple TR-based fingertapping task")

parser.add_argument("--TR", type=float, default=3.35)
parser.add_argument("--frate", type=float, default=60.0)

parser.add_argument(
    "--sequence",
    type=str,
    default="rest,move,rest,move,rest",
)

parser.add_argument(
    "--block_trs",
    type=str,
    default="10,10,10,10,10",
)

parser.add_argument(
    "--instruction_trs",
    type=int,
    default=2,
    help="Duration of each block instruction screen, in TRs.",
)

parser.add_argument(
    "--initial_fixation_trs",
    type=int,
    default=0,
    help="Optional fixation period after trigger and before first instruction.",
)

parser.add_argument("--trigger_mode", choices=["kbd", "cedrus"], default="kbd")
parser.add_argument("--mri_trigger_port", type=int, default=2)
parser.add_argument("--trigger_timeout", type=float, default=1e6)

args = parser.parse_args()

sequence = parse_csv_str(args.sequence)
block_trs = parse_csv_int(args.block_trs)
sequence, block_trs = validate_sequence(sequence, block_trs)


# =====================================================================
# PsychoPy execution
# =====================================================================
from psychopy import visual, core, event, gui


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
LOG_FH = None
timer = core.Clock()


def cli(msg):
    print(msg, flush=True)


def log_line(msg):
    if LOG_FH is not None:
        LOG_FH.write(msg + "\n")


# ---------------------------------------------------------------------
# GUI and logfile
# ---------------------------------------------------------------------
expInfo = {"subject": "phtm", "run": 1}
dlg = gui.DlgFromDict(expInfo, title="Fingertapping task")

if not dlg.OK:
    raise SystemExit(0)

theDate = datetime.now()

logFn = (
    f"fingertapping-s-{expInfo['subject']}-r-{expInfo['run']}-"
    f"{theDate.strftime('%d%b%y')}.log"
)

LOG_FH = open(logFn, "w", buffering=1)

log_line(f"TR={args.TR}")
log_line(f"frate={args.frate}")
log_line(f"sequence={sequence}")
log_line(f"block_trs={block_trs}")
log_line(f"instruction_trs={args.instruction_trs}")
log_line(f"initial_fixation_trs={args.initial_fixation_trs}")
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
    height=FIXATION_HEIGHT,
    color="white",
)

general_instruction_top = visual.TextStim(
    win,
    text=(
        "You will see a cross at the center of the screen.\n"
        "Keep your eyes focused on the cross during the entire experiment."
    ),
    pos=(0, 0.45),
    height=GENERAL_INSTRUCTION_HEIGHT,
    color="white",
    wrapWidth=1.5,
    alignText="center",
)

general_instruction_move = visual.TextStim(
    win,
    text=(
        "When instructed to move,\n"
        "repeatedly tap your\n"
        "index finger against\n"
        "your thumb until\n"
        "further instruction."
    ),
    pos=(-0.45, -0.3),
    height=GENERAL_INSTRUCTION_HEIGHT*.8,
    color="white",
    wrapWidth=0.7,
    alignText="center",
)

general_instruction_rest = visual.TextStim(
    win,
    text=(
        "When instructed not to move,\n"
        "remain completely still\n"
        "until further instruction."
    ),
    pos=(0.45, -0.3),
    height=GENERAL_INSTRUCTION_HEIGHT*.8,
    color="white",
    wrapWidth=0.7,
    alignText="center",
)


block_instruction = visual.TextStim(
    win,
    text="",
    pos=(0, 0),
    height=BLOCK_INSTRUCTION_HEIGHT,
    color="white",
    wrapWidth=1.5,
)


# ---------------------------------------------------------------------
# Cedrus helpers
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


def get_cedrus_triggers(dev):
    triggers = []

    dev.poll_for_response()

    while dev.has_response():
        response = dev.get_next_response()

        if response.get("port", None) == args.mri_trigger_port:
            log_line(f"MRI_TRIGGER time={timer.getTime():.6f} raw={response}")
            cli(f"MRI_TRIGGER {response}")
            triggers.append(response)
        else:
            log_line(f"DEVICE_RESPONSE time={timer.getTime():.6f} raw={response}")

    return triggers


def poll_triggers_during_task():
    keys = event.getKeys(keyList=["t", "escape"])

    if "escape" in keys:
        log_line(f"ABORT time={timer.getTime():.6f} reason=escape")
        cli("Experiment aborted by user with ESC")
        return False

    if args.trigger_mode == "kbd" and "t" in keys:
        log_line(f"KEYBOARD_TRIGGER time={timer.getTime():.6f}")
        cli("KEYBOARD_TRIGGER")

    if cedrus is not None:
        get_cedrus_triggers(cedrus)

    return True


# ---------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------
def draw_general_instruction():
    general_instruction_top.draw()
    general_instruction_move.draw()
    general_instruction_rest.draw()

    win.flip()

def draw_fixation():
    fixation.draw()


def draw_block_instruction(block_type):
    if block_type == "rest":
        block_instruction.setText("Remain still")
    elif block_type == "move":
        block_instruction.setText("When the cross appears, repeatedly tap your index finger against your thumb")
    else:
        raise ValueError(f"Unknown block type: {block_type}")

    block_instruction.draw()


# ---------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------
def trs_to_frames(trs):
    return int(round(trs * args.TR * args.frate))


def run_period(period_name, tr_count, frame_idx, draw_func, block_type=None):
    if tr_count <= 0:
        log_line(f"PERIOD_OMITTED name={period_name} TRs={tr_count}")
        return frame_idx, True

    nframes = trs_to_frames(tr_count)

    log_line(
        f"PERIOD_BEGIN name={period_name} "
        f"block_type={block_type} TRs={tr_count} frames={nframes}"
    )
    cli(f"PERIOD_BEGIN name={period_name} block_type={block_type} TRs={tr_count}")

    for _ in range(nframes):
        if not poll_triggers_during_task():
            return frame_idx, False

        draw_func()
        log_line(
            f"FRAME frame={frame_idx} "
            f"time={timer.getTime():.6f} "
            f"period={period_name} "
            f"block_type={block_type} "
            f"TR={frame_idx // int(args.TR * args.frate)}"
        )

        win.flip()
        frame_idx += 1

    log_line(f"PERIOD_END name={period_name} block_type={block_type}")
    cli(f"PERIOD_END name={period_name} block_type={block_type}")

    return frame_idx, True


# ---------------------------------------------------------------------
# Trigger wait
# ---------------------------------------------------------------------
def wait_for_trigger():
    if args.trigger_mode == "kbd":
        cli("Waiting for keyboard start trigger: press 't'")

        while True:
            keys = event.getKeys(keyList=["t", "escape"])

            if "t" in keys:
                log_line("START_TRIGGER mode=kbd")
                cli("Keyboard start trigger received")
                return True

            if "escape" in keys:
                log_line("ABORT during_trigger_wait reason=escape")
                cli("Experiment aborted during trigger wait")
                return False

            core.wait(0.01)

    cli(f"Waiting for Cedrus MRI trigger, port={args.mri_trigger_port}")
    log_line(f"Waiting for Cedrus MRI trigger, port={args.mri_trigger_port}")

    cedrus.clear_response_queue()
    wait_clock = core.Clock()

    while wait_clock.getTime() < args.trigger_timeout:
        keys = event.getKeys(keyList=["escape"])

        if "escape" in keys:
            log_line("ABORT during_trigger_wait reason=escape")
            cli("Experiment aborted during trigger wait")
            return False

        triggers = get_cedrus_triggers(cedrus)

        if triggers:
            log_line("START_TRIGGER mode=cedrus")
            cli("Cedrus start trigger received")
            return True

        core.wait(0.001)

    log_line("MRI_TRIGGER_TIMEOUT")
    cli("MRI trigger timeout")
    return False


# ---------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------
try:
    draw_general_instruction()

    ok = wait_for_trigger()

    if not ok:
        raise SystemExit(0)

    timer.reset()
    log_line("EXPERIMENT_START time=0.000000")
    cli("Experiment started")

    frame_idx = 0

    frame_idx, ok = run_period(
        period_name="initial_fixation",
        tr_count=args.initial_fixation_trs,
        frame_idx=frame_idx,
        draw_func=draw_fixation,
        block_type="fixation",
    )

    if not ok:
        raise SystemExit(0)

    for block_type, tr_count in zip(sequence, block_trs):
        frame_idx, ok = run_period(
            period_name="instruction",
            tr_count=args.instruction_trs,
            frame_idx=frame_idx,
            draw_func=lambda bt=block_type: draw_block_instruction(bt),
            block_type=block_type,
        )

        if not ok:
            raise SystemExit(0)

        frame_idx, ok = run_period(
            period_name="task_block",
            tr_count=tr_count,
            frame_idx=frame_idx,
            draw_func=draw_fixation,
            block_type=block_type,
        )

        if not ok:
            raise SystemExit(0)

    log_line("EXPERIMENT_END")
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