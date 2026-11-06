# Google Cloud VM Deployment & Operations Manual

This guide details how to host the **BTC Swing Engine** on Google Cloud Compute Engine's **Always Free Tier** (`e2-micro`), enabling 24/7 continuous operation at **$0.00/month**.

---

## 1. Google Cloud Always Free Tier Specifications

| Component | Specification | Free Tier Eligibility |
|:---|:---|:---|
| **Instance Type** | `e2-micro` (2 vCPUs shared-core, 1 GB RAM) | Always Free (1 instance per billing account) |
| **Eligible Regions** | `us-central1` (Iowa), `us-east1` (S. Carolina), `us-west1` (Oregon) | Must choose one of these 3 regions |
| **Boot Disk** | 30 GB Standard Persistent Disk | Up to 30 GB is 100% free |
| **OS Image** | Ubuntu 22.04 LTS or Ubuntu 24.04 LTS | Free open-source OS |
| **Monthly Cost** | **$0.00 / month** | $0.00 forever within limits |

> **Critical Memory Note (2 GB Swapfile)**:
> The `e2-micro` has 1 GB of physical RAM. While the engine runs lean (~150 MB–200 MB), memory can briefly spike during `pip install` (e.g. compiling numpy/pandas wheels). Our `setup_gcp_vm.sh` script automatically provisions a **2 GB Swapfile** on the 30 GB persistent disk, ensuring the system never runs out of memory or terminates processes.

---

## 2. Step-by-Step GCP VM Creation (5 Minutes)

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **Compute Engine** -> **VM Instances** -> **Create Instance**.
3. Configure the VM:
   - **Name**: `btc-swing-engine`
   - **Region**: `us-central1` (Iowa) or `us-east1` (South Carolina)
   - **Zone**: Any available (e.g., `us-central1-a`)
   - **Machine Configuration**: Series `E2`, Machine type `e2-micro` (2 vCPU, 1 GB memory)
   - **Boot Disk**: Click *Change* -> Operating System: `Ubuntu`, Version: `Ubuntu 22.04 LTS` (or `24.04 LTS`), Size: `30 GB` Standard persistent disk.
   - **Firewall**: Default settings (SSH port 22 is open by default).
4. Click **Create**.
5. Once running, note the **External IP** address.

---

## 3. One-Command Automated Provisioning

Connect to the VM via SSH (click the **SSH** button in GCP Console, or run `gcloud compute ssh btc-swing-engine`), then run:

```bash
# 1. Clone or copy your btc_swing_engine project
git clone <your-repo-url> btc_swing_engine
cd btc_swing_engine

# 2. Run the automated provisioning script
bash deploy/setup_gcp_vm.sh
```

The script automatically:
1. Configures the 2 GB swapfile.
2. Updates APT and installs `python3-venv`, `python3-pip`, `tmux`, `git`, `htop`.
3. Creates `.venv` and installs dependencies.
4. Executes a 3-second live dry-run test to verify network connectivity.

---

## 4. Running the Engine in Persistent TMUX

To keep the engine running 24/7 even after you close your laptop or disconnect SSH:

```bash
# Launch inside persistent tmux session
bash deploy/run_tmux.sh
```

- **To Detach (leave engine running in background)**: Press `Ctrl+B`, release, then press `D`.
- **To Re-Attach**:
  ```bash
  tmux attach -t btc_engine
  ```
- **To Stop**: Press `Ctrl+C` inside the session.

---

## 5. Running Parallel with Local Machine (A/B Test)

You can run both your **Local PC** and the **Google Cloud VM** simultaneously:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│         LOCAL ENGINE            │       │         GOOGLE CLOUD VM         │
│  • Runs on home PC / WiFi       │       │  • Runs 24/7 on us-central1     │
│  • Independent forward test     │  vs   │  • Low latency datacenter link  │
│  • Uninterrupted baseline       │       │  • Accessible via Termius Phone │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

1. **Independent State**: Each instance maintains its own `logs/forward_test_state.json`.
2. **WebSocket Safety**: Public market data feeds (Binance Spot `data-stream.binance.vision`, Binance Perp, Coinbase) allow multiple concurrent read-only subscribers with zero conflict.
3. **State Sync**: If you ever want to migrate your forward-test scorecard between machines:
   ```powershell
   # From your local Windows PowerShell:
   .\deploy\sync_state.ps1 -VmHost "YOUR_VM_EXTERNAL_IP" -Direction "ToCloud"
   ```

---

## 6. Mobile Access via Termius

Follow the detailed instructions in [TERMIUS_MOBILE_SETUP.md](TERMIUS_MOBILE_SETUP.md) to turn your smartphone into a Bloomberg-grade mobile trading terminal with one-thumb hotkey buttons for `[P]`, `[F]`, `[W]`, `[0]`, `[L]`, and `[C]`.
