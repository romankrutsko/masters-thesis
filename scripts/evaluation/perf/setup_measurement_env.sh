#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_NAME="$(basename "$0")"

# Print CLI usage because this script changes system state and should be explicit.
usage() {
  cat <<'EOF'
Usage:
  scripts/evaluation/perf/setup_measurement_env.sh setup [--pin-cpu N] [--offline-cpu N]...
  scripts/evaluation/perf/setup_measurement_env.sh restore [--online-cpu N]...
  scripts/evaluation/perf/setup_measurement_env.sh status

Commands:
  setup
    Applies the recommended low-noise measurement settings:
    - performance power profile if available
    - performance CPU governor
    - disables screen idle/suspend where supported
    - disables radios through NetworkManager where supported
    - exports single-thread math-library variables for the current shell output
    - optionally offlines specified logical CPUs to avoid SMT/Hyper-Threading interference
    - prints the taskset command to use for the benchmark

  restore
    Restores radios and re-enables any CPUs explicitly provided with --online-cpu.
    Screen and governor settings are not fully reverted automatically because the
    original values are system-dependent.

  status
    Prints a compact summary of the current machine state relevant to measurement.

Options:
  --pin-cpu N       Logical CPU to recommend for taskset in the final run command.
  --offline-cpu N   Logical CPU to offline during setup. May be passed multiple times.
  --online-cpu N    Logical CPU to re-enable during restore. May be passed multiple times.
  -h, --help        Show this help text.

Examples:
  scripts/evaluation/perf/setup_measurement_env.sh status
  scripts/evaluation/perf/setup_measurement_env.sh setup --pin-cpu 2 --offline-cpu 10
  scripts/evaluation/perf/setup_measurement_env.sh restore --online-cpu 10
EOF
}

# Fail early when a command is mandatory for a status/setup step.
require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

# Disable desktop idle/sleep behavior so long benchmark runs are not interrupted.
set_gnome_power_settings() {
  if command -v gsettings >/dev/null 2>&1; then
    gsettings set org.gnome.desktop.session idle-delay 0 || true
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing' || true
    gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing' || true
  fi

  if command -v xset >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
    xset s off || true
    xset -dpms || true
  fi
}

# Ask the OS power-profile manager for the highest-performance profile if present.
set_performance_profile() {
  if command -v powerprofilesctl >/dev/null 2>&1; then
    powerprofilesctl set performance || true
  fi
}

# Force a fixed performance CPU governor to reduce frequency-scaling noise.
set_performance_governor() {
  if command -v cpupower >/dev/null 2>&1; then
    sudo cpupower frequency-set -g performance
    return
  fi

  local cpu
  for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    if [[ -w "$cpu/cpufreq/scaling_governor" ]]; then
      echo performance | sudo tee "$cpu/cpufreq/scaling_governor" >/dev/null
    fi
  done
}

# Turn off radios to reduce background network/Bluetooth activity during measurement.
disable_radios() {
  if command -v nmcli >/dev/null 2>&1; then
    nmcli radio all off || true
  fi
}

# Re-enable radios after a measurement session.
enable_radios() {
  if command -v nmcli >/dev/null 2>&1; then
    nmcli radio all on || true
  fi
}

# Offline a logical CPU to avoid scheduler or SMT sibling interference.
offline_cpu() {
  local cpu="$1"
  if [[ "$cpu" == "0" ]]; then
    echo "Refusing to offline cpu0." >&2
    exit 1
  fi
  if [[ ! -e "/sys/devices/system/cpu/cpu${cpu}/online" ]]; then
    echo "CPU ${cpu} does not expose an online control file." >&2
    exit 1
  fi
  echo 0 | sudo tee "/sys/devices/system/cpu/cpu${cpu}/online" >/dev/null
}

# Bring an explicitly offlined logical CPU back online.
online_cpu() {
  local cpu="$1"
  if [[ ! -e "/sys/devices/system/cpu/cpu${cpu}/online" ]]; then
    echo "CPU ${cpu} does not expose an online control file." >&2
    exit 1
  fi
  echo 1 | sudo tee "/sys/devices/system/cpu/cpu${cpu}/online" >/dev/null
}

# Limit common numeric backends to one thread so each benchmark measures one script process, not variable internal parallelism.
print_thread_exports() {
  cat <<'EOF'
# OpenMP users, including several compiled scientific libraries.
export OMP_NUM_THREADS=1
# OpenBLAS used by NumPy/SciPy/R builds on many Linux systems.
export OPENBLAS_NUM_THREADS=1
# Intel MKL used by some NumPy/SciPy/scikit-learn installations.
export MKL_NUM_THREADS=1
# NumExpr used by pandas/numpy expression evaluation when installed.
export NUMEXPR_NUM_THREADS=1
# Apple Accelerate/vecLib backend used on macOS.
export VECLIB_MAXIMUM_THREADS=1
# BLIS backend used by some NumPy/R linear algebra builds.
export BLIS_NUM_THREADS=1
EOF
}

# Show the system settings that most affect runtime/energy repeatability.
print_status() {
  echo "Power profile:"
  if command -v powerprofilesctl >/dev/null 2>&1; then
    powerprofilesctl get || true
  else
    echo "  powerprofilesctl not available"
  fi

  echo
  echo "CPU governor policy:"
  if command -v cpupower >/dev/null 2>&1; then
    cpupower frequency-info | grep "current policy" || true
  else
    grep . /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || echo "  governor info unavailable"
  fi

  echo
  echo "Radio state:"
  if command -v nmcli >/dev/null 2>&1; then
    nmcli radio || true
  else
    echo "  nmcli not available"
  fi

  echo
  echo "CPU topology:"
  require_command lscpu
  lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE
}

# Apply low-noise settings and print the exact shell exports/benchmark command to use.
do_setup() {
  local pin_cpu=""
  local -a offline_cpus=()

  while (($#)); do
    case "$1" in
      --pin-cpu)
        pin_cpu="${2:?missing value for --pin-cpu}"
        shift 2
        ;;
      --offline-cpu)
        offline_cpus+=("${2:?missing value for --offline-cpu}")
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown setup option: $1" >&2
        exit 1
        ;;
    esac
  done

  # Stabilize power, display, network, and CPU-frequency behavior before measuring.
  set_performance_profile
  set_gnome_power_settings
  disable_radios
  set_performance_governor

  # Optionally disable selected logical CPUs, usually SMT siblings of the pinned CPU.
  local cpu
  for cpu in "${offline_cpus[@]}"; do
    offline_cpu "$cpu"
  done

  echo
  echo "Apply these thread limits in the shell before running the benchmark:"
  print_thread_exports

  echo
  # RAPL energy counters require perf access; this confirms the event is readable.
  echo "Verify perf access:"
  echo "perf stat -e power/energy-pkg/ -- sleep 0.1"

  echo
  # Pinning keeps the measured process on one logical CPU for more stable runs.
  if [[ -n "$pin_cpu" ]]; then
    echo "Recommended benchmark command:"
    echo "taskset -c ${pin_cpu} python scripts/evaluation/perf/measure_translation_perf_energy.py --runs 30 --warmup-runs 1 --pause-between-runs 1 --pause-seconds 60 --timeout 120 --output-dir results/perf_energy_runs/run_30x_60s_pinned_cpu${pin_cpu}"
  else
    echo "No --pin-cpu value was provided. Use lscpu output from 'status' to pick a logical CPU."
  fi
}

# Restore the reversible pieces that this script can safely restore by argument.
do_restore() {
  local -a online_cpus=()

  while (($#)); do
    case "$1" in
      --online-cpu)
        online_cpus+=("${2:?missing value for --online-cpu}")
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown restore option: $1" >&2
        exit 1
        ;;
    esac
  done

  # Only re-enable CPUs that the caller explicitly names.
  local cpu
  for cpu in "${online_cpus[@]}"; do
    online_cpu "$cpu"
  done

  enable_radios

  echo "Restore completed for requested CPUs and radios."
}

# Dispatch the requested subcommand.
main() {
  if (($# == 0)); then
    usage
    exit 1
  fi

  case "$1" in
    setup)
      shift
      do_setup "$@"
      ;;
    restore)
      shift
      do_restore "$@"
      ;;
    status)
      shift
      print_status
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown command: $1" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
