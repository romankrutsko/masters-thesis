# Energy and Runtime Measurement Protocol

## Purpose

This document defines a practical protocol for collecting runtime and CPU package
energy measurements with low external noise on Linux. The goal is not to create
an idealized machine state, but to reduce uncontrolled variance while preserving
a reproducible execution environment for the translated Python and R scripts in
this repository.

The repository runner is `scripts/evaluation/perf/measure_perf_energy.py`. It measures each
execution with `perf stat -e power/energy-pkg/` and records runtime, package
energy, and average power. The runner now checkpoints progress during execution:

- each measured CSV row is appended immediately after the run completes
- the CSV file is forced to disk after each script cycle
- the JSON summary is rewritten after each script cycle and at the final end

This persistence happens after `perf` has already finished measuring the target
process. Therefore, it does not change the recorded energy or runtime of the run
that has just completed. It may still affect the thermal state before the next
script, which is why the 60-second cooldown remains important.

## Methodological Position

The following principle should guide the experiment design:

1. Stabilize the platform state.
2. Keep the workload definition fixed across all candidates.
3. Avoid interventions that selectively favor one language or runtime.
4. Report all machine-state controls in the thesis methods section.

Some controls reduce noise without materially changing the workload, such as AC
power, fixed governor settings, thread caps for BLAS backends, CPU affinity, and
background-service reduction. Other controls can change the workload itself, such
as disabling turbo boost or offlining sibling SMT threads. Those stronger
controls should be applied only if they are used consistently for every run and
reported explicitly.

## Recommended Pre-Run Machine State

### 1. Use a dedicated session

Prefer a rebooted machine with no interactive desktop load. On a dedicated Linux
test machine, the cleanest option is a text console:

```bash
sudo systemctl isolate multi-user.target
```

If the machine must remain in graphical mode, close browsers, IDE indexing,
cloud sync clients, messaging clients, update managers, and any notebook-style
workloads before starting measurements.

### 2. Run on AC power

Confirm that the laptop is plugged in and battery-saving logic is disabled. If
the machine exposes a platform profile, use `performance`:

```bash
powerprofilesctl set performance
powerprofilesctl get
```

### 3. Disable screen blanking, auto-dimming, and suspend

Display energy is not part of the `power/energy-pkg/` metric, because that
counter measures CPU package energy rather than whole-system power. However,
screen blanking, dimming, and suspend logic may still introduce extra OS
activity during long experiments. Disabling them is a reasonable stability
control.

For GNOME-based sessions:

```bash
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
```

If X11 DPMS and screen saver controls are active:

```bash
xset s off
xset -dpms
```

### 4. Enable airplane mode or otherwise disable wireless radios

Wireless activity does not directly change CPU package-energy semantics, but it
can create interrupts, background scans, and network-driven wakeups. A simple
control is to enable airplane mode before the run.

On systems with NetworkManager:

```bash
nmcli radio all off
nmcli radio
```

To restore radios afterward:

```bash
nmcli radio all on
```

If the desktop environment exposes a hardware or software airplane-mode toggle,
that is also acceptable.

### 5. Set the CPU governor to `performance`

Install `cpupower` if needed and set every core to the performance governor:

```bash
sudo apt-get install linux-tools-common linux-tools-generic linux-tools-$(uname -r)
sudo cpupower frequency-set -g performance
cpupower frequency-info | grep "current policy"
```

If `cpupower` is unavailable but the kernel exposes `scaling_governor`:

```bash
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
  echo performance | sudo tee "$cpu/cpufreq/scaling_governor"
done
```

### 6. Optionally disable turbo boost

This step often reduces variance, but it also changes the processor behavior and
typically lowers absolute performance. Use it only if you want a stricter,
flatter frequency envelope and are prepared to report that choice.

```bash
cat /sys/devices/system/cpu/intel_pstate/no_turbo
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
```

To re-enable turbo afterward:

```bash
echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
```

### 7. Cap implicit thread pools

Many scientific Python and R dependencies call BLAS, OpenMP, or vectorized math
libraries that may spawn helper threads. Unless the experiment explicitly studies
parallel execution, set all common thread-pool variables to `1`:

```bash
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export BLIS_NUM_THREADS=1
```

### 8. Reduce avoidable background activity

On Ubuntu-like systems, the following services are commonly worth stopping for a
measurement session:

```bash
sudo systemctl stop unattended-upgrades
sudo systemctl stop apt-daily.service apt-daily-upgrade.service
sudo systemctl stop packagekit
sudo systemctl stop snapd
```

Before doing this on a shared machine, verify whether those services are needed
for other active users. Re-enable them after the experiment:

```bash
sudo systemctl start snapd
sudo systemctl start packagekit
sudo systemctl start apt-daily.service apt-daily-upgrade.service
sudo systemctl start unattended-upgrades
```

### 9. Prevent Hyper-Threading interference

If the system uses SMT/Hyper-Threading, two logical CPUs may share one physical
core. Pinning to a single logical CPU is helpful, but it does not fully prevent
interference if the sibling logical CPU remains online and available to other
work. A stronger control is to keep one sibling online and offline the other.

First inspect topology:

```bash
lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE
```

Interpretation:

- rows with the same `CORE` value are sibling logical CPUs on the same physical core
- keep one sibling online
- offline the other sibling before the benchmark
- avoid offlining `cpu0` unless you are certain the system tolerates it

Example: if `CPU 2` and `CPU 10` share the same `CORE`, keep `CPU 2` and
offline `CPU 10`:

```bash
echo 0 | sudo tee /sys/devices/system/cpu/cpu10/online
```

To restore the sibling afterward:

```bash
echo 1 | sudo tee /sys/devices/system/cpu/cpu10/online
```

This is a stronger platform control than simple affinity pinning, and it should
be reported explicitly in the thesis because it changes the machine
configuration.

### 10. Choose stable CPU affinity

Pin the benchmark controller to one physical core, or to a small set of physical
cores, and avoid sharing them with unrelated heavy processes. This improves
scheduler stability and reduces migration noise.

First inspect topology:

```bash
lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE
```

Then choose one CPU or one set of physical cores. Example using CPU 2:

```bash
taskset -c 2 .venv/bin/python scripts/evaluation/perf/measure_perf_energy.py --runs 100 --warmup-runs 1 --pause-seconds 60
```

If SMT/Hyper-Threading siblings are visible, prefer selecting one logical CPU
per physical core rather than both siblings of the same core. If the machine is
dedicated to the experiment, a stronger control is to offline sibling threads,
but this should be treated as an explicit platform modification:

```bash
lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE
echo 0 | sudo tee /sys/devices/system/cpu/cpu3/online
```

Re-enable afterward:

```bash
echo 1 | sudo tee /sys/devices/system/cpu/cpu3/online
```

If the benchmark is launched with `taskset`, the benchmark controller, `perf`,
and the child script processes inherit that affinity. In other words, the runs
are effectively pinned to the selected logical CPU set. Without `taskset`, the
OS scheduler may migrate them between CPUs.

### 11. Check `perf` permissions and RAPL visibility

The benchmark depends on Linux `perf` and Intel RAPL package counters:

```bash
perf stat -e power/energy-pkg/ -- sleep 0.1
cat /proc/sys/kernel/perf_event_paranoid
```

If permissions are too restrictive:

```bash
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid
```

For a persistent setting:

```bash
echo "kernel.perf_event_paranoid = -1" | sudo tee /etc/sysctl.d/99-perf.conf
sudo sysctl --system
```

## Recommended Execution Procedure

1. Reboot the machine.
2. Connect AC power.
3. Enter the dedicated measurement session.
4. Disable screen dimming, blanking, and suspend.
5. Enable airplane mode or disable radios.
6. Set performance governor and optional performance power profile.
7. Optionally disable turbo boost.
8. Stop avoidable background services.
9. Export thread-pool limits.
10. Inspect topology and, if desired, offline Hyper-Threading siblings.
11. Verify `perf stat -e power/energy-pkg/ -- sleep 0.1` works.
12. Choose CPU affinity with `taskset`.
13. Run a short pilot with `--runs 2` to confirm output and permissions.
14. Run the full benchmark with `--runs 100 --pause-seconds 60`.

Example command:

```bash
cd /home/romakrut/PycharmProjects/masters-thesis
source .venv/bin/activate
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
nmcli radio all off
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export BLIS_NUM_THREADS=1
taskset -c 2 python scripts/evaluation/perf/measure_perf_energy.py \
  --runs 100 \
  --warmup-runs 1 \
  --pause-seconds 60 \
  --timeout 120 \
  --output-dir results/perf_energy_runs/run_100x_60s_pinned_cpu2
```

## Suggested Thesis Wording

The following text can be adapted directly into the methods section:

> Runtime and energy measurements were collected on Linux using `perf stat`
> with the Intel RAPL package-energy counter (`power/energy-pkg/`). Each script
> was executed 100 times in a separate subprocess, preceded by one warm-up run,
> and a 60-second cooldown interval was inserted between script-level execution
> cycles. To reduce exogenous variance, the machine was connected to AC power,
> the CPU governor was fixed to `performance`, screen blanking and automatic
> suspend were disabled, wireless radios were disabled during the benchmark
> session, implicit numerical thread pools were limited to one thread, sibling
> SMT/Hyper-Threading logical CPUs were excluded where applicable, benchmark
> execution was pinned to a fixed CPU via `taskset`, and non-essential
> background services were stopped during the measurement session. Results were
> checkpointed incrementally to disk after execution progress to mitigate data
> loss in long-running experiments.

## Notes on Interpretation

- `power/energy-pkg/` measures CPU package energy, not whole-system wall-socket
  power.
- Disk flushes and summary checkpoint writes happen after a measured execution
  ends; they do not alter the recorded metrics of that completed run.
- They can still influence subsequent thermal conditions, which is one reason
  the 60-second inter-script pause should be preserved.
- If you disable turbo boost or SMT, document that explicitly because it changes
  the platform rather than merely reducing variance.
