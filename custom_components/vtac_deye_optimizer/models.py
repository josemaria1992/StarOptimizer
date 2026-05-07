"""Data models for VTAC Deye Optimizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class OptimizerConfig:
    """Runtime configuration for the optimizer."""

    battery_soc: str
    pv_power: str | None = None
    pv_power_sensors: list[str] = field(default_factory=list)
    load_power: str | None = None
    grid_power: str | None = None
    grid_power_sensors: list[str] = field(default_factory=list)
    battery_current: str | None = None
    battery_state: str | None = None
    price_sensor: str | None = None

    work_mode: str | None = None
    grid_charging_enable: str | None = None
    soc_target: str | None = None
    soc_targets: list[str] = field(default_factory=list)
    max_charge_current: str | None = None
    max_discharge_current: str | None = None
    grid_charging_current: str | None = None
    grid_max_export_power: str | None = None
    peak_shaving_enable: str | None = None
    peak_shaving_power: str | None = None

    battery_capacity_kwh: float = 10.0
    nominal_voltage_v: float = 51.2
    min_voltage_v: float = 48.0
    min_soc_percent: float = 15.0
    max_soc_percent: float = 100.0
    target_soc_percent: float = 80.0
    export_floor_soc_percent: float = 35.0
    max_charge_a: float = 250.0
    max_discharge_a: float = 250.0
    max_charge_w: float = 12000.0
    max_discharge_w: float = 12000.0
    min_charge_a: float = 10.0
    round_step_a: float = 5.0
    cycle_cost_per_kwh: float = 0.08
    peak_shaving_threshold_w: float | None = None
    enable_export: bool = True
    shadow_mode: bool = True
    auto_execute: bool = False
    scan_interval: int = 300


@dataclass(slots=True)
class SystemSnapshot:
    """Current power and battery state read from Home Assistant."""

    soc_percent: float
    pv_kw: float = 0.0
    load_kw: float = 0.0
    grid_kw: float = 0.0
    battery_current_a: float = 0.0
    battery_state: str = ""
    timestamp: datetime | None = None


@dataclass(slots=True)
class PlanSlot:
    """One planned control slot."""

    start: datetime
    end: datetime
    price: float
    mode: str
    charge_kw: float = 0.0
    discharge_kw: float = 0.0
    export_kw: float = 0.0
    soc_target: int = 50
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable slot."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "price": round(self.price, 5),
            "mode": self.mode,
            "charge_kw": round(self.charge_kw, 3),
            "discharge_kw": round(self.discharge_kw, 3),
            "export_kw": round(self.export_kw, 3),
            "soc_target": self.soc_target,
            "reason": self.reason,
        }


@dataclass(slots=True)
class OptimizerState:
    """Coordinator state exposed by entities."""

    snapshot: SystemSnapshot | None = None
    schedule: list[PlanSlot] = field(default_factory=list)
    current_slot: PlanSlot | None = None
    last_action: str = "none"
    last_error: str | None = None
    last_update: datetime | None = None
    shadow_mode: bool = True
    auto_execute: bool = False
