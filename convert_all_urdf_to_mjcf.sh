#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ROOT="${OUT_DIR:-${SCRIPT_DIR}}"
CONVERTER="${SCRIPT_DIR}/urdf_to_mjcf.py"
METHOD="urdf"
PYTHON_CMD="${MJCF_PYTHON:-python3}"

SYSTEMS=(
  "revo2_system"
  "revo3_system"
  "revoarm_system"
  "revotron_system"
  "flexiv_system"
)

if [[ ! -f "${CONVERTER}" ]]; then
  echo "Converter not found: ${CONVERTER}" >&2
  exit 1
fi

usage() {
  cat <<'EOF'
Usage: ./convert_all_urdf_to_mjcf.sh [--method urdf|collision-inertia|visual-inertia|all|both]

No arguments are needed: defaults to --method urdf and discovers models next
to this script, regardless of the current directory. Requires Python 3.10+.
Activate your Python environment first; MJCF_PYTHON can override its interpreter.
OUT_DIR optionally selects another packaged model root.

Appearance: all visuals use group 2; collision geometry uses group 3.

Methods:
  urdf               Copy URDF body inertial values into MJCF. Output: name.xml
  collision-inertia  Let MuJoCo compute inertia from collision mesh mass.
                     Output: name_collision_inertia.xml
  visual-inertia     Let MuJoCo compute inertia from visual mesh mass.
                     Output: name_visual_inertia.xml
  both               Generate urdf and collision-inertia variants.
  all                Generate all variants.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --method" >&2
        usage >&2
        exit 1
      fi
      METHOD="$2"
      shift 2
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

if [[ "${METHOD}" != "urdf" && "${METHOD}" != "collision-inertia" && "${METHOD}" != "visual-inertia" && "${METHOD}" != "both" && "${METHOD}" != "all" ]]; then
  echo "Invalid method: ${METHOD}" >&2
  usage >&2
  exit 1
fi

failures=0
converted=0

if ! "${PYTHON_CMD}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "MJCF conversion requires Python 3.10+. Activate that environment or set MJCF_PYTHON." >&2
  exit 1
fi

for system in "${SYSTEMS[@]}"; do
  urdf_dir="${MODEL_ROOT}/${system}/urdf"
  mjcf_dir="${MODEL_ROOT}/${system}/mjcf"

  if [[ ! -d "${urdf_dir}" ]]; then
    echo "Skip ${system}: no urdf directory"
    continue
  fi

  mkdir -p "${mjcf_dir}"
  echo "==> ${system}"

  while IFS= read -r -d '' urdf; do
    name="$(basename "${urdf}" .urdf)"
    rel_urdf="${urdf#${SCRIPT_DIR}/}"

    if [[ "${METHOD}" == "urdf" || "${METHOD}" == "both" || "${METHOD}" == "all" ]]; then
      output="${mjcf_dir}/${name}.xml"
      rel_output="${output#${SCRIPT_DIR}/}"

      echo "  [urdf] ${rel_urdf} -> ${rel_output}"
      if "${PYTHON_CMD}" "${CONVERTER}" "${urdf}" --inertia-mode urdf -o "${output}"; then
        converted=$((converted + 1))
      else
        echo "  failed: ${rel_urdf} [urdf]" >&2
        failures=$((failures + 1))
      fi
    fi

    if [[ "${METHOD}" == "collision-inertia" || "${METHOD}" == "both" || "${METHOD}" == "all" ]]; then
      output="${mjcf_dir}/${name}_collision_inertia.xml"
      rel_output="${output#${SCRIPT_DIR}/}"

      echo "  [collision-inertia] ${rel_urdf} -> ${rel_output}"
      if "${PYTHON_CMD}" "${CONVERTER}" "${urdf}" --inertia-mode collision -o "${output}"; then
        converted=$((converted + 1))
      else
        echo "  failed: ${rel_urdf} [collision-inertia]" >&2
        failures=$((failures + 1))
      fi
    fi

    if [[ "${METHOD}" == "visual-inertia" || "${METHOD}" == "all" ]]; then
      output="${mjcf_dir}/${name}_visual_inertia.xml"
      rel_output="${output#${SCRIPT_DIR}/}"

      echo "  [visual-inertia] ${rel_urdf} -> ${rel_output}"
      if "${PYTHON_CMD}" "${CONVERTER}" "${urdf}" --inertia-mode visual -o "${output}"; then
        converted=$((converted + 1))
      else
        echo "  failed: ${rel_urdf} [visual-inertia]" >&2
        failures=$((failures + 1))
      fi
    fi
  done < <(find "${urdf_dir}" -maxdepth 1 -type f -name "*.urdf" -print0 | sort -z)
done

echo
echo "Converted: ${converted}"
echo "Failures: ${failures}"

if [[ "${failures}" -ne 0 ]]; then
  exit 1
fi
if [[ "${converted}" -eq 0 ]]; then
  echo "No URDFs found under ${MODEL_ROOT}/*_system/urdf. Keep the packaged models beside this script or set OUT_DIR." >&2
  exit 1
fi
