"""Darkstar-inspired lightweight planning for Deye hybrid inverters.

This is intentionally smaller than Darkstar's MILP/Aurora stack. It keeps the
same operational contract: generate charge, export, idle, or self-consumption
intents and let the Deye executor apply those intents safely.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median

from homeassistant.core import HomeAssistant

from .const import MODE_CHARGE, MODE_EXPORT, MODE_IDLE, MODE_SELF_CONSUMPTION
from .models import OptimizerConfig, PlanSlot, SystemSnapshot


def _state_float(hass: HomeAssistant, entity_id: str | None, default: float = 0.0) -> float:
    """Read a numeric HA state."""
    if not entity_id:
        return default
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable", ""):
        return default
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return default
    unit = str(state.attributes.get("unit_of_measurement", "")).lower()
    if unit == "w":
        return value / 1000.0
    return value


def _state_string(hass: HomeAssistant, entity_id: str | None, default: str = "") -> str:
    """Read a string HA state."""
    if not entity_id:
        return default
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return default
    return str(state.state)


def _state_float_sum(hass: HomeAssistant, entity_ids: list[str], default: float = 0.0) -> float:
    """Read and sum numeric HA states."""
    if not entity_ids:
        return default
    return sum(_state_float(hass, entity_id) for entity_id in entity_ids)


def read_snapshot(hass: HomeAssistant, config: OptimizerConfig) -> SystemSnapshot:
    """Read the current battery and power state."""
    pv_kw = _state_float_sum(hass, config.pv_power_sensors)
    if pv_kw == 0.0:
        pv_kw = _state_float(hass, config.pv_power)

    grid_kw = _state_float_sum(hass, config.grid_power_sensors)
    if grid_kw == 0.0:
        grid_kw = _state_float(hass, config.grid_power)

    return SystemSnapshot(
        soc_percent=_state_float(hass, config.battery_soc, 50.0),
        pv_kw=pv_kw,
        load_kw=_state_float(hass, config.load_power),
        grid_kw=grid_kw,
        battery_current_a=_state_float(hass, config.battery_current),
        battery_state=_state_string(hass, config.battery_state),
        timestamp=datetime.now().astimezone(),
    )


def read_prices(hass: HomeAssistant, entity_id: str | None) -> list[float]:
    """Read hourly prices from common Nord Pool style sensors."""
    if not entity_id:
        return []
    state = hass.states.get(entity_id)
    if state is None:
        return []

    attrs = state.attributes
    candidates = []
    for key in ("raw_today", "raw_tomorrow", "today", "tomorrow"):
        value = attrs.get(key)
        if isinstance(value, list):
            candidates.extend(value)

    prices: list[float] = []
    for item in candidates:
        if isinstance(item, dict):
            raw = item.get("value", item.get("price", item.get("total")))
        else:
            raw = item
        try:
            prices.append(float(raw))
        except (TypeError, ValueError):
            continue

    if prices:
        return prices[:48]

    try:
        return [float(state.state)]
    except (TypeError, ValueError):
        return []


def _percentile(values: list[float], fraction: float) -> float:
    """Return an approximate percentile from sorted values."""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[idx]


def _charge_current_for_kw(config: OptimizerConfig, kw: float) -> float:
    raw = (kw * 1000.0) / max(1.0, config.min_voltage_v)
    rounded = round(raw / config.round_step_a) * config.round_step_a
    return max(config.min_charge_a, min(config.max_charge_a, rounded))


def build_schedule(
    config: OptimizerConfig,
    snapshot: SystemSnapshot,
    prices: list[float],
    now: datetime | None = None,
) -> list[PlanSlot]:
    """Build a 24-48 hour schedule using price bands and current SoC."""
    now = now or datetime.now().astimezone()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    horizon_prices = prices or [0.0] * 24

    low_price = _percentile(horizon_prices, 0.25)
    high_price = _percentile(horizon_prices, 0.75)
    middle = median(horizon_prices)
    spread = high_price - low_price

    soc = max(config.min_soc_percent, min(config.max_soc_percent, snapshot.soc_percent))
    capacity = max(0.1, config.battery_capacity_kwh)
    max_charge_kw = min(
        config.max_charge_w / 1000.0,
        config.max_charge_a * config.min_voltage_v / 1000.0,
    )
    max_discharge_kw = min(
        config.max_discharge_w / 1000.0,
        config.max_discharge_a * config.nominal_voltage_v / 1000.0,
    )
    soc_per_charge_hour = (max_charge_kw / capacity) * 100.0
    soc_per_discharge_hour = (max_discharge_kw / capacity) * 100.0

    schedule: list[PlanSlot] = []
    for idx, price in enumerate(horizon_prices[:48]):
        start = hour_start + timedelta(hours=idx)
        end = start + timedelta(hours=1)
        reason = "normal self consumption"
        mode = MODE_SELF_CONSUMPTION
        charge_kw = 0.0
        discharge_kw = 0.0
        export_kw = 0.0
        target = round(max(config.min_soc_percent, min(config.target_soc_percent, soc)))

        cheap_enough = price <= low_price and soc < config.target_soc_percent
        profitable = config.enable_export and spread > config.cycle_cost_per_kwh
        expensive_enough = price >= high_price and soc > config.export_floor_soc_percent

        if cheap_enough:
            mode = MODE_CHARGE
            charge_kw = max_charge_kw
            soc = min(config.target_soc_percent, soc + soc_per_charge_hour)
            target = round(config.target_soc_percent)
            amps = _charge_current_for_kw(config, charge_kw)
            reason = f"cheap slot; charge at about {amps:.0f} A"
        elif profitable and expensive_enough:
            mode = MODE_EXPORT
            discharge_kw = max_discharge_kw
            export_kw = max(0.0, max_discharge_kw - max(0.0, snapshot.load_kw - snapshot.pv_kw))
            soc = max(config.export_floor_soc_percent, soc - soc_per_discharge_hour)
            target = round(config.export_floor_soc_percent)
            reason = f"high price above median {middle:.3f}; export allowed"
        elif soc <= config.min_soc_percent + 1:
            mode = MODE_IDLE
            target = round(soc)
            reason = "at minimum SoC; hold battery"

        schedule.append(
            PlanSlot(
                start=start,
                end=end,
                price=price,
                mode=mode,
                charge_kw=charge_kw,
                discharge_kw=discharge_kw,
                export_kw=export_kw,
                soc_target=target,
                reason=reason,
            )
        )

    return schedule
