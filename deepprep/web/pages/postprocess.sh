#!/bin/bash
# -------------------------------
# @Author : Cong Lin        @Email : Cong Lin <lincong8722@gmail.com>
# @Author : Ning An        @Email : Ning An <ninganme0317@gmail.com>

original_args=("$@")
echo "INFO: args: ${original_args[*]}"

cpus=""
memory=""
freesurfer_home="/opt/freesurfer"
fs_license_file=""
subjects_dir=""
deepprep_home="/opt/DeepPrep"
ignore_error=""
debug=""
resume=""
preprocess_qc_dir=""
user_skip_frame=""

help="DeepPrep args:
deepprep-docker [bids_dir] [output_dir] [{participant}]
                 [--fs_license_file PATH] [--subjects_dir PATH] [--confounds_index_file PATH]
                 [--task_id '[task1 task2 ...]'] [--participant_label '[sub-001 sub-002 ...]']
                 [--QC_dir PATH] [--skip_frame N] [--repetition_time TR]
                 [--spaces '[None MNI152NLin6Asym fsnative fsaverage6 ...]']
                 [--cpus N] [--memory GB] [--ignore_error] [--resume] [--debug]

skip_frame priority:
  1. Explicit --skip_frame N (including 0)
  2. Otherwise --QC_dir/nextflow.run.config: params.bold_skip_frame
  3. Otherwise the default params.skip_frame in postprocess.config"

if [[ $# -lt 2 ]]; then
    printf 'ERROR: Expected at least [bids_dir] [output_dir].\n%s\n' "$help" >&2
    exit 1
fi

bids_dir="$1"
output_dir="$2"
shift 2

# The original launcher ignored an optional third positional participant argument.
# Only consume it when it is not an option; otherwise --QC_dir/--skip_frame may be lost.
if [[ $# -gt 0 && "$1" != -* ]]; then
    participant="$1"
    shift
fi

# Rebuild forwarded args so that --QC_dir is a launcher-only option and --skip_frame
# appears exactly once with the resolved value at the end.
args=("--bids_dir" "$bids_dir" "--output_dir" "$output_dir")

while [[ $# -gt 0 ]]; do
    key="$1"
    case "$key" in
        --QC_dir|--qc_dir)
            if [[ $# -lt 2 || -z "$2" ]]; then
                echo "ERROR: $key requires a directory path." >&2
                exit 1
            fi
            preprocess_qc_dir="$2"
            echo "Input $key : ${preprocess_qc_dir}"
            shift 2
            ;;
        --QC_dir=*|--qc_dir=*)
            preprocess_qc_dir="${key#*=}"
            echo "Input --QC_dir : ${preprocess_qc_dir}"
            shift
            ;;
        --skip_frame)
            if [[ $# -lt 2 || -z "$2" ]]; then
                echo "ERROR: --skip_frame requires a non-negative integer." >&2
                exit 1
            fi
            user_skip_frame="$2"
            echo "Input --skip_frame : ${user_skip_frame}"
            shift 2
            ;;
        --skip_frame=*)
            user_skip_frame="${key#*=}"
            echo "Input --skip_frame : ${user_skip_frame}"
            shift
            ;;
        --deepprep_home|--fs_license_file|--subjects_dir|--cpus|--memory)
            if [[ $# -lt 2 || -z "$2" ]]; then
                echo "ERROR: $key requires a value." >&2
                exit 1
            fi
            case "$key" in
                --deepprep_home) deepprep_home="$2" ;;
                --fs_license_file) fs_license_file="$2" ;;
                --subjects_dir) subjects_dir="$2" ;;
                --cpus) cpus="$2" ;;
                --memory) memory="$2" ;;
            esac
            echo "Input $key : $2"
            args+=("$key" "$2")
            shift 2
            ;;
        --ignore_error)
            ignore_error="True"
            echo "Input --ignore_error : True"
            args+=("$key")
            shift
            ;;
        --resume)
            resume="True"
            echo "Input --resume : True"
            args+=("-resume")
            shift
            ;;
        --debug)
            debug="True"
            echo "Input --debug : True"
            args+=("$key")
            shift
            ;;
        -h|-help|--help)
            echo "$help"
            exit 0
            ;;
        *)
            args+=("$key")
            shift
            ;;
    esac
done

# Resolve skip_frame before calling Nextflow.
# Do not forward --QC_dir (not a Nextflow parameter) to the pipeline.
resolved_skip_frame=""
if [[ -n "$user_skip_frame" ]]; then
    resolved_skip_frame="$user_skip_frame"
    skip_frame_source="explicit --skip_frame"
elif [[ -n "$preprocess_qc_dir" ]]; then
    # The first path is the requested preprocessing QC format.
    # A second layout is supported for installations storing run.config in nextflow/.
    qc_config=""
    for candidate in \
        "${preprocess_qc_dir%/}/nextflow.run.config" \
        "${preprocess_qc_dir%/}/nextflow/run.config"; do
        if [[ -f "$candidate" ]]; then
            qc_config="$candidate"
            break
        fi
    done
    if [[ -z "$qc_config" ]]; then
        echo "ERROR: Cannot find nextflow.run.config under --QC_dir: ${preprocess_qc_dir}" >&2
        echo "       Checked: ${preprocess_qc_dir%/}/nextflow.run.config" >&2
        echo "                ${preprocess_qc_dir%/}/nextflow/run.config" >&2
        exit 1
    fi

    # Match only an active, integer-valued assignment, not a commented-out line.
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*bold_skip_frame[[:space:]]*=[[:space:]]*([0-9]+)([[:space:]]|$) ]]; then
            resolved_skip_frame="${BASH_REMATCH[1]}"
            break
        fi
    done < "$qc_config"
    if [[ -z "$resolved_skip_frame" ]]; then
        echo "ERROR: No valid 'bold_skip_frame = <integer>' found in $qc_config" >&2
        exit 1
    fi
    skip_frame_source="$qc_config (bold_skip_frame)"
else
    # Do NOT add --skip_frame; Nextflow will read params.skip_frame from postprocess.config.
    skip_frame_source="postprocess.config (params.skip_frame default)"
fi

if [[ -n "$resolved_skip_frame" ]]; then
    if [[ ! "$resolved_skip_frame" =~ ^[0-9]+$ ]]; then
        echo "ERROR: skip_frame must be a non-negative integer, got: $resolved_skip_frame" >&2
        exit 1
    fi
    args+=("--skip_frame" "$resolved_skip_frame")
    echo "INFO: resolved skip_frame=${resolved_skip_frame}; source=${skip_frame_source}"
else
    echo "INFO: skip_frame not overridden; source=${skip_frame_source}"
fi

if [[ ! -d "$deepprep_home" ]]; then
    echo "ERROR: deepprep_home does not exist: ${deepprep_home}" >&2
    exit 1
fi

if [[ -z "$freesurfer_home" || ! -d "$freesurfer_home" ]]; then
    echo "ERROR: freesurfer_home is empty or does not exist: ${freesurfer_home}" >&2
    exit 1
fi
export FREESURFER_HOME="$freesurfer_home"
echo "FREESURFER_HOME is set to: $FREESURFER_HOME"
# NOTE: The original script tested the literal string 'FSF_OUTPUT_FORMAT',
# which never sources setup. Test the variable value instead.
if [[ -z "${FSF_OUTPUT_FORMAT:-}" ]]; then
    echo "source ${freesurfer_home}/SetUpFreeSurfer.sh"
    source "${freesurfer_home}/SetUpFreeSurfer.sh"
fi

if [[ -z "$fs_license_file" ]]; then
    echo "WARNING: using bundled FreeSurfer license; replace if needed."
    fs_license_file="${deepprep_home}/deepprep/FreeSurfer/license.txt"
fi
if [[ ! -f "$fs_license_file" ]]; then
    echo "ERROR: fs_license_file does not exist: ${fs_license_file}" >&2
    exit 1
fi
export FS_LICENSE="$fs_license_file"

nextflow_work_dir="${output_dir}/WorkDir/nextflow"
qc_dir="${output_dir}/QC"  # Postprocess QC output; different from --QC_dir.
mkdir -p "$nextflow_work_dir" "${output_dir}/WorkDir/home" "${output_dir}/WorkDir/tmp" "$qc_dir"

nextflow_file="${deepprep_home}/deepprep/rest/denoise/postprocess.nf"
common_config="${deepprep_home}/deepprep/rest/denoise/postprocess.config"
if [[ -n "$debug" ]]; then
    echo "DEBUG: nextflow_file : ${nextflow_file}"
    echo "DEBUG: common_config : ${common_config}"
fi
if [[ ! -f "$common_config" ]]; then
    echo "ERROR: config_file does not exist: ${common_config}" >&2
    exit 1
fi

run_config="${nextflow_work_dir}/run.config"
echo "INFO: run_config : ${run_config}"
cp "$common_config" "$run_config"

if [[ -n "$cpus" ]]; then
    sed -i "s@//cpus=@    cpus=${cpus}@g" "$run_config"
fi
if [[ -n "$memory" ]]; then
    sed -i "s@//memory=@    memory='${memory} GB'@g" "$run_config"
fi
if [[ -n "$ignore_error" ]]; then
    sed -i "s@//errorStrategy@    errorStrategy@g" "$run_config"
fi

cd "$nextflow_work_dir" || exit 1
nextflow run "$nextflow_file" \
    -c "$run_config" \
    -w "$nextflow_work_dir" \
    -with-report "$qc_dir/report.html" \
    -with-timeline "$qc_dir/timeline.html" \
    "${args[@]}"