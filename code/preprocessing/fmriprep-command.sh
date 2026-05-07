#!/usr/bin/env bash
set -euo pipefail

parent_folder='/mnt/data1/francisco/Projects/ESBS_certificate/finger-tap-task'
rawdata="$parent_folder/data/rawdata"
derivs="$parent_folder/data/derivatives/fmriprep"
logs="$parent_folder/data/derivatives/fmriprep/logs"

fs_license='/home/francisco/freesurfer/license.txt'

mkdir -p "$derivs" "$logs"

subs=$(printf "sub-esbs%02d\n" 1)
# subs=$(printf "sub-21\n")

for sub in $subs; do
  echo "Processing $sub..."
  docker run --rm \
    -u 1000:1000 \
    -v "$rawdata:/data:ro" \
    -v "$derivs:/out" \
    -v "$logs:/logs" \
    -v "$fs_license:/opt/freesurfer/license.txt:ro" \
    nipreps/fmriprep:25.2.5 \
    /data /out participant \
    --participant-label "${sub#sub-}" \
    --me-output-echos \
    --fs-no-reconall \
    --me-t2s-fit-method loglin \
    --n_cpus 32 \
    --fs-license-file /opt/freesurfer/license.txt \
    2>&1 | tee "$logs/fmriprep_${sub}.stdout"
done