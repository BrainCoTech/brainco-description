#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ROOT="${OUT_DIR:-${SCRIPT_DIR}}"
CONVERTER="${SCRIPT_DIR}/convert_urdf_v4.py"
ISAACSIM_PYTHON="${ISAACSIM_PYTHON:-}"
EXCLUDE_IGNORED=0
DRY_RUN=0
FLATTEN=1
SYSTEMS=(
  "revo2_system"
  "revo3_system"
  "revoarm_system"
  "revotron_system"
  "flexiv_system"
)

usage() {
  cat <<'EOF'
Usage: ./convert_all_urdf_to_usd.sh [--python PATH] [--exclude-ignored] [--no-flatten] [--dry-run]

No arguments are needed: defaults to --flatten and discovers models next to
this script, regardless of the current directory. Activate an Isaac Lab /
Isaac Sim Python environment first. No ROS or source workspace is required.
OUT_DIR optionally selects another packaged model root.

Outputs:
  <system>/usd/<urdf_name>.usd
  Each USD retains the complete visual appearance.

Converter: convert_urdf_v4.py (fixed base, merged fixed joints, zero drive gains,
disabled gravity, self-collision, solver iterations 16/4, Revo3 v4 colliders).

Options:
  --python PATH       Isaac Lab / Isaac Sim Python executable. Can also be set with ISAACSIM_PYTHON.
  --exclude-ignored  Skip URDF files ignored by git, such as *_none.urdf and flexiv_system.
  --flatten          Flatten to one USD per model (default); referenced textures remain external.
  --no-flatten       Keep the importer's configuration layers instead.
  --dry-run          Print planned conversions without invoking Isaac Sim.
EOF
}

git_ignored() {
  local path="$1"
  local rel_path
  rel_path="$(realpath --relative-to="${MODEL_ROOT}" "${path}")"
  git -C "${MODEL_ROOT}" check-ignore -q "${rel_path}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --python" >&2
        usage >&2
        exit 1
      fi
      ISAACSIM_PYTHON="$2"
      shift 2
      ;;
    --exclude-ignored)
      EXCLUDE_IGNORED=1
      shift
      ;;
    --include-ignored)
      # Kept as a harmless alias for older notes; ignored URDFs are included by default.
      shift
      ;;
    --flatten)
      FLATTEN=1
      shift
      ;;
    --no-flatten)
      FLATTEN=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "${CONVERTER}" ]]; then
  echo "Converter not found: ${CONVERTER}" >&2
  exit 1
fi

PYTHON_CMD="${ISAACSIM_PYTHON:-python3}"

planned=0
batch_pairs=()
converter_args=(--fix-base --headless)
if [[ "${FLATTEN}" -eq 1 ]]; then
  converter_args+=(--flatten)
fi
echo "USD settings: ${converter_args[*]}"

for system in "${SYSTEMS[@]}"; do
  urdf_dir="${MODEL_ROOT}/${system}/urdf"
  [[ -d "${urdf_dir}" ]] || continue

  usd_dir="${MODEL_ROOT}/${system}/usd"
  for urdf in "${urdf_dir}"/*.urdf; do
    [[ -e "${urdf}" ]] || continue

    if [[ "${EXCLUDE_IGNORED}" -eq 1 ]] && git_ignored "${urdf}"; then
      continue
    fi

    name="$(basename "${urdf}" .urdf)"
    output="${usd_dir}/${name}.usd"
    planned=$((planned + 1))

    echo "${urdf} -> ${output}"
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      continue
    fi

    batch_pairs+=("${urdf}" "${output}")
  done
done

if [[ "${planned}" -eq 0 ]]; then
  echo "No URDFs found under ${MODEL_ROOT}/*_system/urdf. Keep the packaged models beside this script or set OUT_DIR." >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo
  echo "Planned: ${planned}"
  exit 0
fi

if ! "${PYTHON_CMD}" - <<'PY'
import importlib.util
import sys
missing = [name for name in ("isaaclab", "isaacsim") if importlib.util.find_spec(name) is None]
if missing:
    print("Missing Python modules: " + ", ".join(missing), file=sys.stderr)
    raise SystemExit(1)
PY
then
  echo "USD conversion requires Isaac Lab and Isaac Sim in the selected Python environment." >&2
  echo "Activate that environment and rerun; see CONVERSION.md. Alternatively set ISAACSIM_PYTHON or use --python PATH." >&2
  exit 1
fi

# Start Kit once for the full batch rather than once per robot.
manifest="$(mktemp)"
trap 'rm -f "${manifest}"' EXIT
"${PYTHON_CMD}" - "${manifest}" "${batch_pairs[@]}" <<'PY'
import json
import sys
from pathlib import Path
pairs = sys.argv[2:]
Path(sys.argv[1]).write_text(json.dumps([
    {"input": pairs[i], "output": pairs[i+1]}
    for i in range(0, len(pairs), 2)
]))
PY
result=0
"${PYTHON_CMD}" "${CONVERTER}" "${MODEL_ROOT}" "${MODEL_ROOT}" \
  "${converter_args[@]}" --batch-manifest "${manifest}" || result=$?
exit "${result}"
