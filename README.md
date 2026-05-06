# Finger-Tap Task fMRI Study

A neuroimaging study using a simple finger-tapping task paradigm designed for fMRI acquisition.

## Project Overview

This repository contains code and data for a finger-tapping task experiment, where participants alternate between rest and active finger-tapping blocks during fMRI scanning. The task is presented with a fixation cross and clear instructions for each condition.

## Project Structure

```
finger-tap-task/
├── task-ftp/                    # Task stimulus script and experiment logs
│   └── finger-tap-task.py       # Main task presentation script
├── code/                        # Analysis and preprocessing code
│   ├── preprocessing/           # fMRI preprocessing pipelines
│   └── analysis/                # Event-based analysis and statistics
└── data/                        # BIDS-formatted neuroimaging data
    ├── sub-*/                   # Subject directories
    └── dataset_description.json # BIDS dataset metadata
```

## Task Description

The finger-tapping task implements a block design with:
- **Conditions**: Rest (no movement) and Active (finger-tapping)
- **Visual cues**: Fixation cross during all blocks
- **Instructions**: Clear text instructions before each condition block
- **Flexibility**: Configurable TR, block durations, and trigger modes

### Example Usage

```bash
python task-ftp/finger-tap-task.py \
  --TR 1.50 \
  --sequence rest,move,rest,move,rest \
  --block_trs 20,20,20,20,20 \
  --instruction_trs 4 \
  --initial_fixation_trs 4 \
  --trigger_mode kbd
```

## Data Organization

The `data/` folder follows the [Brain Imaging Data Structure (BIDS)](https://bids-standard.github.io/) standard for consistent, shareable neuroimaging datasets. This enables:
- Compatibility with standard analysis tools
- Easy sharing and collaboration
- Automated data validation

### BIDS Format Overview

```
data/
├── sub-<label>/
│   ├── ses-<label>/
│   │   ├── anat/           # Anatomical images (T1w, T2w)
│   │   ├── func/           # Functional scans (task-ftp_bold.nii.gz + .json sidecars)
│   │   ├── fmap/           # Field maps (if available)
│   │   └── *_scans.tsv     # List of acquisition files
│   └── sub-<label>_scans.tsv
├── dataset_description.json
├── CHANGES
├── participants.tsv
└── README
```

## Analysis Pipeline

### Preprocessing
- Motion correction
- Brain extraction
- Registration to standard space
- Smoothing

### Event-Based Analysis
- GLM setup with task regressors
- Contrast estimation
- ROI analysis (e.g., motor cortex)
- Statistical inference

## Requirements

- Python 3.x
- PsychoPy (for task presentation)
- Standard neuroimaging tools (SPM, FSL, AFNI, or Nilearn for analysis)

## Usage

1. **Run task**: Execute `finger-tap-task.py` with appropriate parameters
2. **Organize data**: Ensure data follows BIDS structure in the `data/` folder
3. **Preprocess**: Use `code/preprocessing/` scripts
4. **Analyze**: Run event-based analysis with `code/analysis/` scripts

## References

- BIDS Standard: https://bids-standard.github.io/
- Brain Imaging Data Structure validation: https://bids-standard.github.io/dev/tools.html

## License

[Specify your license here]

## Contact

[Your name/contact information]
