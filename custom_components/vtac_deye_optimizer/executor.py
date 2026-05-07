"""Deye executor profile for VTAC battery systems."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    DEYE_WORK_MODE_CHARGE,
    DEYE_WORK_MODE_EXPORT,
    DEYE_WORK_MODE_SELF_USE,
    MODE_CHARGE,
    MODE_EXPORT,
    MODE_IDLE,
    MODE_SELF_CONSUMPTION,
)
from .models import OptimizerConfig, PlanSlot

_LOGGER = logging.getLogger(__name__)


async def _call(hass: HomeAssistant, domain: str, service: str, data: dict[str, Any]) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


async def _set_select(hass: HomeAssistant, entity_id: str | None, option: str) -> None:
    if entity_id:
        state = hass.states.get(entity_id)
        if state is not None and str(state.state).strip().lower() == option.strip().lower():
            return
        await _call(hass, "select", "select_option", {"entity_id": entity_id, "option": option})


async def _set_switch(hass: HomeAssistant, entity_id: str | None, turn_on: bool) -> None:
    if entity_id:
        state = hass.states.get(entity_id)
        desired = "on" if turn_on else "off"
        if state is not None and str(state.state).lower() == desired:
            return
        await _call(hass, "switch", "turn_on" if turn_on else "turn_off", {"entity_id": entity_id})


async def _set_number(hass: HomeAssistant, entity_id: str | None, value: float) -> None:
    if entity_id:
        state = hass.states.get(entity_id)
        if state is not None:
            try:
                if abs(float(state.state) - float(value)) < 0.01:
                    return
            except (TypeError, ValueError):
                pass
        domain = entity_id.split(".", 1)[0]
        service = "set_value"
        await _call(hass, domain, service, {"entity_id": entity_id, "value": value})


def _charge_current_for_slot(config: OptimizerConfig, slot: PlanSlot) -> float:
    if slot.charge_kw <= 0:
        return 0.0
    raw = (slot.charge_kw * 1000.0) / max(1.0, config.min_voltage_v)
    rounded = round(raw / config.round_step_a) * config.round_step_a
    return max(config.min_charge_a, min(config.max_charge_a, rounded))


async def _set_soc_targets(hass: HomeAssistant, config: OptimizerConfig, value: int) -> None:
    """Write the same SoC target to all configured Deye time programs."""
    targets = list(config.soc_targets)
    if config.soc_target and config.soc_target not in targets:
        targets.append(config.soc_target)
    for entity_id in targets:
        await _set_number(hass, entity_id, value)


async def _set_peak_shaving(hass: HomeAssistant, config: OptimizerConfig) -> None:
    """Enable and configure peak shaving if entities are configured."""
    if config.peak_shaving_enable:
        await _set_switch(hass, config.peak_shaving_enable, True)
    if config.peak_shaving_power and config.peak_shaving_threshold_w is not None:
        await _set_number(hass, config.peak_shaving_power, config.peak_shaving_threshold_w)


async def apply_slot(hass: HomeAssistant, config: OptimizerConfig, slot: PlanSlot) -> str:
    """Apply one Darkstar-style mode intent to a Deye inverter."""
    if config.shadow_mode:
        return f"shadow: would apply {slot.mode}"

    await _set_peak_shaving(hass, config)

    if slot.mode == MODE_CHARGE:
        await _set_select(hass, config.work_mode, DEYE_WORK_MODE_CHARGE)
        await _set_switch(hass, config.grid_charging_enable, True)
        await _set_number(hass, config.max_charge_current, config.max_charge_a)
        await _set_number(hass, config.grid_charging_current, _charge_current_for_slot(config, slot))
        await _set_soc_targets(hass, config, slot.soc_target)
    elif slot.mode == MODE_EXPORT:
        await _set_select(hass, config.work_mode, DEYE_WORK_MODE_EXPORT)
        await _set_switch(hass, config.grid_charging_enable, False)
        await _set_number(hass, config.max_discharge_current, config.max_discharge_a)
        await _set_number(hass, config.grid_max_export_power, slot.export_kw * 1000.0)
        await _set_soc_targets(hass, config, slot.soc_target)
    elif slot.mode == MODE_IDLE:
        await _set_select(hass, config.work_mode, DEYE_WORK_MODE_SELF_USE)
        await _set_switch(hass, config.grid_charging_enable, False)
        await _set_number(hass, config.max_discharge_current, 15.0)
        await _set_number(hass, config.max_charge_current, config.max_charge_a)
        await _set_soc_targets(hass, config, slot.soc_target)
    elif slot.mode == MODE_SELF_CONSUMPTION:
        await _set_select(hass, config.work_mode, DEYE_WORK_MODE_SELF_USE)
        await _set_switch(hass, config.grid_charging_enable, False)
        await _set_number(hass, config.max_charge_current, config.max_charge_a)
        await _set_number(hass, config.max_discharge_current, config.max_discharge_a)
        await _set_soc_targets(hass, config, slot.soc_target)
    else:
        raise ValueError(f"Unsupported optimizer mode: {slot.mode}")

    _LOGGER.info("Applied VTAC/Deye optimizer mode %s", slot.mode)
    return f"applied {slot.mode}"
