"""SweepRetestFSM: Finite State Machine for BTC Liquidity Sweep & Retest Lifecycles.

Handles discrete bar transitions, structural validation, and atomic JSON state persistence.
Operates on 1H and 4H kline intervals to track multi-bar liquidity sweeps across time.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SweepDirection(str, Enum):
    """Direction of the structural sweep and resulting trade intent."""

    BULLISH = "BULLISH"  # Sell-side liquidity sweep -> Spot Accumulation
    BEARISH = "BEARISH"  # Buy-side liquidity sweep -> Spot Risk-Off / Capital Preservation


class FSMState(str, Enum):
    """Discrete states of the SweepRetest Finite State Machine."""

    SEEKING_REJECTION = "SEEKING_REJECTION"  # Wick broke level; waiting for candle close back inside
    PENDING_RETEST = "PENDING_RETEST"  # Confirmed rejection; awaiting retest envelope touch
    TRIGGERED = "TRIGGERED"  # Retest confirmed with structure intact; signal fired
    INVALIDATED = "INVALIDATED"  # Price accepted beyond sweep extreme
    EXPIRED = "EXPIRED"  # Setup exceeded allocated time horizons


@dataclass
class Candle:
    """Standardized OHLCV candle representation for FSM evaluations."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class SweepInstance:
    """Individual tracked sweep lifecycle instance."""

    instance_id: str
    direction: SweepDirection
    key_level: float
    sweep_extreme: float
    sweep_timestamp: int
    current_state: FSMState = FSMState.SEEKING_REJECTION
    bars_elapsed: int = 0
    rejection_timestamp: Optional[int] = None
    trigger_timestamp: Optional[int] = None
    invalidation_level: float = 0.0
    retest_band_high: float = 0.0
    retest_band_low: float = 0.0
    suggested_stop: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["direction"] = self.direction.value
        payload["current_state"] = self.current_state.value
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> SweepInstance:
        d = data.copy()
        d["direction"] = SweepDirection(d["direction"])
        d["current_state"] = FSMState(d["current_state"])
        return cls(**d)


class SweepRetestFSM:
    """State machine governing liquidity sweep detection, rejection, and retest execution."""

    def __init__(
        self,
        rejection_window_bars: int = 2,
        max_retest_bars: int = 12,
        retest_tolerance_pct: float = 0.002,  # 0.20% retest envelope around level
        invalidation_buffer_pct: float = 0.0015,  # 0.15% beyond sweep wick extreme
    ) -> None:
        self.rejection_window_bars = rejection_window_bars
        self.max_retest_bars = max_retest_bars
        self.retest_tolerance_pct = retest_tolerance_pct
        self.invalidation_buffer_pct = invalidation_buffer_pct

    def register_sweep(
        self,
        direction: SweepDirection,
        key_level: float,
        sweep_bar: Candle,
        timeframe: str = "1H",
    ) -> SweepInstance:
        """Initializes a new sweep lifecycle upon structural penetration."""
        instance_id = f"FSM_{direction.value}_{int(key_level)}_{sweep_bar.timestamp}"

        if direction == SweepDirection.BEARISH:
            sweep_extreme = sweep_bar.high
            invalidation = sweep_extreme * (1.0 + self.invalidation_buffer_pct)
            retest_high = key_level * (1.0 + self.retest_tolerance_pct)
            retest_low = key_level * (1.0 - self.retest_tolerance_pct)
        else:
            sweep_extreme = sweep_bar.low
            invalidation = sweep_extreme * (1.0 - self.invalidation_buffer_pct)
            retest_high = key_level * (1.0 + self.retest_tolerance_pct)
            retest_low = key_level * (1.0 - self.retest_tolerance_pct)

        return SweepInstance(
            instance_id=instance_id,
            direction=direction,
            key_level=round(key_level, 2),
            sweep_extreme=round(sweep_extreme, 2),
            sweep_timestamp=sweep_bar.timestamp,
            current_state=FSMState.SEEKING_REJECTION,
            bars_elapsed=0,
            invalidation_level=round(invalidation, 2),
            retest_band_high=round(retest_high, 2),
            retest_band_low=round(retest_low, 2),
            suggested_stop=round(invalidation, 2),
            metadata={"timeframe": timeframe},
        )

    def transition(self, instance: SweepInstance, current_bar: Candle) -> SweepInstance:
        """Evaluates bar-close conditions and advances instance across FSM states."""
        if instance.current_state in (FSMState.TRIGGERED, FSMState.INVALIDATED, FSMState.EXPIRED):
            return instance

        instance.bars_elapsed += 1

        # 1. Structural Invalidation Checks
        if instance.direction == SweepDirection.BEARISH:
            if current_bar.close > instance.invalidation_level:
                instance.current_state = FSMState.INVALIDATED
                instance.metadata["invalidation_reason"] = "Bar closed above sweep extreme buffer"
                return instance
            if current_bar.high > instance.sweep_extreme and instance.current_state == FSMState.SEEKING_REJECTION:
                instance.sweep_extreme = round(current_bar.high, 2)
                instance.invalidation_level = round(current_bar.high * (1.0 + self.invalidation_buffer_pct), 2)
                instance.suggested_stop = instance.invalidation_level
        else:
            if current_bar.close < instance.invalidation_level:
                instance.current_state = FSMState.INVALIDATED
                instance.metadata["invalidation_reason"] = "Bar closed below sweep extreme buffer"
                return instance
            if current_bar.low < instance.sweep_extreme and instance.current_state == FSMState.SEEKING_REJECTION:
                instance.sweep_extreme = round(current_bar.low, 2)
                instance.invalidation_level = round(current_bar.low * (1.0 - self.invalidation_buffer_pct), 2)
                instance.suggested_stop = instance.invalidation_level

        # 2. State: SEEKING_REJECTION
        if instance.current_state == FSMState.SEEKING_REJECTION:
            if instance.direction == SweepDirection.BEARISH and current_bar.close < instance.key_level:
                instance.current_state = FSMState.PENDING_RETEST
                instance.rejection_timestamp = current_bar.timestamp
                return instance
            elif instance.direction == SweepDirection.BULLISH and current_bar.close > instance.key_level:
                instance.current_state = FSMState.PENDING_RETEST
                instance.rejection_timestamp = current_bar.timestamp
                return instance

            if instance.bars_elapsed >= self.rejection_window_bars:
                instance.current_state = FSMState.EXPIRED
                instance.metadata["expiry_reason"] = "Failed to close inside level within rejection window"
                return instance

        # 3. State: PENDING_RETEST
        elif instance.current_state == FSMState.PENDING_RETEST:
            if instance.bars_elapsed > self.max_retest_bars:
                instance.current_state = FSMState.EXPIRED
                instance.metadata["expiry_reason"] = "Exceeded maximum bars waiting for retest"
                return instance

            if instance.direction == SweepDirection.BEARISH:
                touched_band = current_bar.high >= instance.retest_band_low
                held_structure = current_bar.close <= instance.retest_band_high
                if touched_band and held_structure:
                    instance.current_state = FSMState.TRIGGERED
                    instance.trigger_timestamp = current_bar.timestamp
                    return instance
            else:
                touched_band = current_bar.low <= instance.retest_band_high
                held_structure = current_bar.close >= instance.retest_band_low
                if touched_band and held_structure:
                    instance.current_state = FSMState.TRIGGERED
                    instance.trigger_timestamp = current_bar.timestamp
                    return instance

        return instance


class FSMStorageManager:
    """Atomic file persistence for SweepRetestFSM state records."""

    def __init__(self, storage_path: str = "sweep_fsm_state.json") -> None:
        self.storage_path = storage_path

    def load_active_instances(self) -> Dict[str, SweepInstance]:
        """Loads non-terminal active FSM instances from disk."""
        if not os.path.exists(self.storage_path):
            return {}
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                raw_payload = json.load(f)
                instances = raw_payload.get("instances", {})
                return {
                    k: SweepInstance.from_dict(v)
                    for k, v in instances.items()
                    if v.get("current_state") in [FSMState.SEEKING_REJECTION.value, FSMState.PENDING_RETEST.value]
                }
        except (json.JSONDecodeError, KeyError, OSError):
            return {}

    def commit(self, active_instances: Dict[str, SweepInstance]) -> None:
        """Atomically replaces the persistent JSON state file."""
        payload = {
            "version": "1.0.0",
            "fsm_engine": "SweepRetestFSM",
            "instances": {k: v.to_dict() for k, v in active_instances.items()},
        }
        dir_name = os.path.dirname(os.path.abspath(self.storage_path)) or "."
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(payload, tf, indent=2)
            temp_name = tf.name

        try:
            os.replace(temp_name, self.storage_path)
        except OSError:
            import shutil
            try:
                shutil.copyfile(temp_name, self.storage_path)
                os.remove(temp_name)
            except Exception:
                pass
