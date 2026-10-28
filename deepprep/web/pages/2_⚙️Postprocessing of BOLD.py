#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# -------------------------------
# @Author : Ning An        @Email : Ning An <ninganme0317@gmail.com>

import streamlit as st
import subprocess
import os
import re
import shlex

st.markdown(f'# ⚙️Postprocessing of BOLD')
st.markdown(
    """
    
Currently, this module is exclusively designed for resting-state functional magnetic resonance imaging (rs-fMRI) data post-processing, following the preprocessing steps. 

The postprocessed data can be utilized for calculating resting-state functional connectivity (RSFC), individualized brain functional parcellation, or other relevant analyses.

For task-based fMRI (task-fMRI) data, it is recommended to employ alternative tools for subsequent analysis, such as FSL, SPM.

#### processing steps

Surface space: bandpass filtering -> regression -> smooth (optional)

Volume space:  bandpass filtering -> regression -> smooth (optional)

-----------------
"""
)

deepprep_cmd = ''
commond_error = False

bids_dir = st.text_input("Preprocessing Result Path:",
                         help="refers to the directory containing the preprocessed BOLD results by DeepPrep, which should be in BIDS format.")
if not bids_dir:
    st.error("The Preprocessing Result Path must be input!")
    deepprep_cmd += ' {bids_dir}'
    commond_error = True
elif not bids_dir.startswith('/'):
    st.error("The path must be an absolute path that starts with '/'.")
    deepprep_cmd += ' {bids_dir}'
    commond_error = True
elif not os.path.exists(bids_dir):
    st.error("The Preprocessing Result Path does not exist!")
    deepprep_cmd += ' {bids_dir}'
    commond_error = True
else:
    deepprep_cmd += f' {bids_dir}'

output_dir = st.text_input("Output Path:", help="refers to the output directory for the postprocessed BOLD data.")
if not output_dir:
    st.error("The Output Path must be input!")
    deepprep_cmd += ' {output_dir}'
    commond_error = True
elif not output_dir.startswith('/'):
    st.error("The path must be an absolute path that starts with '/'.")
    deepprep_cmd += ' {output_dir}'
    commond_error = True
elif output_dir == bids_dir:
    st.error("The Output Path must be different from the BIDS Path!")
    deepprep_cmd += ' {output_dir}'
    commond_error = True
else:
    deepprep_cmd += f' {output_dir}'
deepprep_cmd += f' participant'

freesurfer_license_file = st.text_input("FreeSurfer license file path", value='/opt/freesurfer/license.txt',
                                        help="FreeSurfer license file path. It is highly recommended to replace the license.txt path with your own FreeSurfer license! You can get it for free from https://surfer.nmr.mgh.harvard.edu/registration.html")
if not freesurfer_license_file.startswith('/'):
    st.error("The path must be an absolute path that starts with '/'.")
    commond_error = True
elif not os.path.exists(freesurfer_license_file):
    st.error("The FreeSurfer license file path does not exist!")
    commond_error = True
else:
    deepprep_cmd += f' --fs_license_file {freesurfer_license_file}'

confounds_file = st.text_input("Confounds File Path",
                               value='/opt/DeepPrep/deepprep/rest/denoise/12motion_6param_10bCompCor.txt',
                               help="The path to the text file that contains all the confound names needed for regression.")
if not confounds_file.startswith('/'):
    st.error("The path must be an absolute path that starts with '/'.")
    commond_error = True
elif not os.path.exists(confounds_file):
    st.error("The Confounds File Path does not exist!")
    commond_error = True
else:
    deepprep_cmd += f' --confounds_index_file {confounds_file}'

bold_task_type = st.text_input("BOLD task type", placeholder="i.e. rest, motor, 'rest motor'",
                               help="The task label of BOLD images. If there are multiple tasks, separate them with spaces.")
if bold_task_type:
    if 'task-' in bold_task_type:
        bold_task_type = bold_task_type.replace('task-', '')
    bold_task_type = bold_task_type.replace("'", "")
    bold_task_type = bold_task_type.replace('"', "")
    deepprep_cmd += f" --task_id '{bold_task_type}'"
else:
    st.error("The BOLD task type must be input!")
    commond_error = True

spaces = st.multiselect("required output spaces (optional)",
                        ["T1w", "MNI152NLin6Asym", "MNI152NLin2009cAsym", "fsnative", "fsaverage6", "fsaverage5",
                         "fsaverage4", "fsaverage3"], help="select the output spaces you need")
if spaces:
    spaces = ' '.join(spaces)
    deepprep_cmd += f" --space '{spaces}'"

if "fsnative" in spaces:
    subjects_dir = st.text_input("Recon Result Path",
                                 help=" the directory containing the recon files.")
    if not subjects_dir:
        st.error("The Recon Result Path must be input!")
        commond_error = True
    elif not subjects_dir.startswith('/'):
        st.error("The path must be an absolute path that starts with '/'.")
        commond_error = True
    elif not os.path.exists(subjects_dir):
        st.error("The Recon Result Path does not exist!")
        commond_error = True
    else:
        deepprep_cmd += f' --subjects_dir {subjects_dir}'

# bold_skip_frame = st.text_input("skip n frames of BOLD data", value="2",
#                                 help="skip n frames of BOLD fMRI; the default is `2`.")
# if not bold_skip_frame:
#     deepprep_cmd += f' --skip_frame 2'
# else:
#     deepprep_cmd += f' --skip_frame {bold_skip_frame}'
# -----------------------------------------------------------------------------
# Resolve skip_frame using the same priority as postprocess.sh:
#   explicitly set --skip_frame > preprocessing --QC_dir > postprocess.config.
# -----------------------------------------------------------------------------
def read_integer_config(config_path, param_name):
    """Read an active integer parameter assignment from a Nextflow config."""
    pattern = re.compile(
        rf"^\s*{re.escape(param_name)}\s*=\s*(\d+)(?=\s*(?://|#|;|$))"
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                return int(match.group(1))
    return None


preprocess_qc_dir = st.text_input(
    "Preprocessing QC Directory (optional)",
    value="",
    placeholder="/path/to/preprocessing/QC",
    help=(
        "If provided without a manual skip_frame, postprocess.sh will read "
        "bold_skip_frame from QC_dir/nextflow.run.config. "
        "This is the *preprocessing* QC directory, not the new output QC directory."
    ),
).strip()

if preprocess_qc_dir:
    if not os.path.isabs(preprocess_qc_dir):
        st.error("The Preprocessing QC Directory must be an absolute path.")
        commond_error = True
    else:
        deepprep_cmd += f' --QC_dir {shlex.quote(preprocess_qc_dir)}'

manual_skip_frame = st.checkbox(
    "Set skip_frame manually (highest priority)",
    value=False,
    help=(
        "Check to explicitly pass --skip_frame, including 0. "
        "Otherwise, the launcher reads QC_dir when supplied or falls back "
        "to postprocess.config."
    ),
)

if manual_skip_frame:
    bold_skip_frame = st.number_input(
        "skip n frames of BOLD data",
        min_value=0,
        value=0,
        step=1,
        help="User-provided skip_frame overrides both QC_dir and postprocess.config."
    )
    deepprep_cmd += f' --skip_frame {int(bold_skip_frame)}'
    st.info(
        f"Effective skip_frame: **{int(bold_skip_frame)}** "
        "(source: manual --skip_frame; overrides QC_dir if provided)."
    )
elif preprocess_qc_dir and os.path.isabs(preprocess_qc_dir):
    candidates = [
        os.path.join(preprocess_qc_dir, 'nextflow.run.config'),
        os.path.join(preprocess_qc_dir, 'nextflow', 'run.config'),
    ]
    qc_config = next((path for path in candidates if os.path.isfile(path)), None)
    if qc_config is None:
        st.error(
            "Cannot find nextflow.run.config under the preprocessing QC directory. "
            "Expected QC_dir/nextflow.run.config "
            "(or QC_dir/nextflow/run.config)."
        )
        commond_error = True
    else:
        try:
            qc_skip_frame = read_integer_config(qc_config, 'bold_skip_frame')
        except OSError as exc:
            st.error(f"Cannot read preprocessing QC config: {exc}")
            commond_error = True
        else:
            if qc_skip_frame is None:
                st.error(f"Cannot find valid bold_skip_frame in: {qc_config}")
                commond_error = True
            else:
                st.info(
                    f"Effective skip_frame: **{qc_skip_frame}** "
                    f"(source: {qc_config}, bold_skip_frame)."
                )
else:
    # No --skip_frame is forwarded. Let postprocess.sh/Nextflow use the default.
    default_config = '/opt/DeepPrep/deepprep/rest/denoise/postprocess.config'
    try:
        default_skip_frame = (
            read_integer_config(default_config, 'skip_frame')
            if os.path.isfile(default_config) else None
        )
    except OSError:
        default_skip_frame = None
    if default_skip_frame is None:
        st.info("Effective skip_frame: postprocess.config default (no override passed).")
    else:
        st.info(
            f"Effective skip_frame: **{default_skip_frame}** "
            "(source: postprocess.config, params.skip_frame)."
        )


bold_fwhm = st.text_input("fwhm", value="6", help="smooth by fwhm mm; the default is `6`.")
if not bold_fwhm:
    deepprep_cmd += f' --surface_fwhm 6 --volume_fwhm 6'
else:
    deepprep_cmd += f' --surface_fwhm {bold_fwhm} --volume_fwhm {bold_fwhm}'

bold_bandpass = st.text_input("bandpass filter", value="0.01-0.08", help="the default range is `0.01-0.08`.")
if not bold_bandpass:
    deepprep_cmd += f' --bandpass 0.01-0.08'
else:
    assert len(bold_bandpass.split('-')) == 2
    deepprep_cmd += f' --bandpass {bold_bandpass}'

participant_label = st.text_input("the subject IDs (optional)", placeholder="sub-001 sub-002 sub-003",
                                  help="Identify the subjects you'd like to process by their IDs, i.e. 'sub-001 sub-002 sub-003'.")
if participant_label:
    participant_label = participant_label.replace("'", "")
    participant_label = participant_label.replace('"', "")
    deepprep_cmd += f" --subject_id '{participant_label}'"

col1, col2, col3 = st.columns(3)

with col1:
    skip_bids_validation = st.checkbox("skip_bids_validation", value=True,
                                       help="with this flag, the BIDS format validation step of the input dataset will be skipped.")
    if skip_bids_validation:
        deepprep_cmd += ' --skip_bids_validation'
with col2:
    ignore_error = st.checkbox("ignore_error", help="ignores the errors that occurred during processing.")
    if ignore_error:
        deepprep_cmd += ' --ignore_error'
with col3:
    resume = st.checkbox("resume", value=True, help="allows the DeepPrep pipeline to start from the last exit point.")
    if resume:
        deepprep_cmd += ' --resume'


def run_command(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )

    while True:
        output = process.stdout.readline()
        print(output)
        if output == "" and process.poll() is not None:
            break
        if output:
            yield output + '\n'

    process.wait()


def run_command_with_display(cmd, max_lines=50):
    """
    Run command and display latest output in a scrolling manner
    max_lines: Maximum number of lines to display, default 50 lines
    """
    import time

    # Create an empty container for displaying output
    output_container = st.empty()
    output_lines = []

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Redirect stderr to stdout
        text=True,
        shell=True,
        bufsize=1,
        universal_newlines=True
    )

    while True:
        line = process.stdout.readline()
        if line == "" and process.poll() is not None:
            break
        if line:
            output_lines.append(line.rstrip())

            # Keep only the latest max_lines
            if len(output_lines) > max_lines:
                output_lines = output_lines[-max_lines:]

            # Update display content
            display_text = '\n'.join(output_lines)
            output_container.code(display_text, language='bash')

            # Brief delay to avoid excessive updates
            time.sleep(0.1)

    # Final check for stderr
    stderr = process.stderr
    if stderr:
        remaining_stderr = stderr.read()
        if remaining_stderr:
            output_lines.append(f"ERROR: {remaining_stderr}")
            if len(output_lines) > max_lines:
                output_lines = output_lines[-max_lines:]
            display_text = '\n'.join(output_lines)
            output_container.code(display_text, language='bash')

    process.wait()

    # If process returns non-zero code, display error message
    if process.returncode != 0:
        output_lines.append(f"Process exit code: {process.returncode}")
        display_text = '\n'.join(output_lines)
        output_container.code(display_text, language='bash')
        st.error(f"Command execution failed, exit code: {process.returncode}")
    else:
        st.success("Command executed successfully!")

    return process.returncode == 0


st.write(f'-----------  ------------')
st.write(f'postprocess {deepprep_cmd}')
max_display_lines = 200
if st.button("Run", disabled=commond_error):
    with st.spinner('Waiting for the process to finish, please do not leave this page...'):
        command = [f"/opt/DeepPrep/deepprep/web/pages/postprocess.sh {deepprep_cmd}"]
        with st.expander("------------ running log ------------"):
            # st.write_stream(run_command(command))
            run_command_with_display(command, max_display_lines)
        import time

        time.sleep(2)
    st.success("Done!")
