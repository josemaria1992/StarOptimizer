"""Home Assistant integration for VTAC batteries with Deye inverters."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_AUTO_EXECUTE,
    CONF_BATTERY_CAPACITY_KWH,
    CONF_BATTERY_CURRENT,
    CONF_BATTERY_SOC,
    CONF_BATTERY_STATE,
    CONF_CYCLE_COST,
    CONF_EXPORT_ENABLED,
    CONF_EXPORT_FLOOR_SOC,
    CONF_GRID_CHARGING_CURRENT,
    CONF_GRID_CHARGING_ENABLE,
    CONF_GRID_MAX_EXPORT_POWER,
    CONF_GRID_POWER,
    CONF_GRID_POWER_SENSORS,
    CONF_LOAD_POWER,
    CONF_MAX_CHARGE_A,
    CONF_MAX_CHARGE_CURRENT,
    CONF_MAX_CHARGE_W,
    CONF_MAX_DISCHARGE_A,
    CONF_MAX_DISCHARGE_CURRENT,
    CONF_MAX_DISCHARGE_W,
    CONF_MAX_SOC,
    CONF_MIN_CHARGE_A,
    CONF_MIN_SOC,
    CONF_MIN_VOLTAGE,
    CONF_NOMINAL_VOLTAGE,
    CONF_PEAK_SHAVING_ENABLE,
    CONF_PEAK_SHAVING_POWER,
    CONF_PEAK_SHAVING_THRESHOLD_W,
    CONF_PRICE_SENSOR,
    CONF_PV_POWER,
    CONF_PV_POWER_SENSORS,
    CONF_ROUND_STEP_A,
    CONF_SCAN_INTERVAL,
    CONF_SHADOW_MODE,
    CONF_SOC_TARGET,
    CONF_SOC_TARGETS,
    CONF_TARGET_SOC,
    CONF_WORK_MODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_CHARGE,
    MODE_EXPORT,
    MODE_IDLE,
    MODE_SELF_CONSUMPTION,
)
from .coordinator import VtacDeyeCoordinator
from .models import OptimizerConfig

PLATFORMS = ["sensor", "switch", "button"]


def _as_list(value) -> list[str]:
    """Parse entity lists from UI strings, YAML lists, or comma-separated values."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).replace(",", "\n")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _as_optional_str(data: dict, key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_float(data: dict, key: str, default: float) -> float:
    value = data.get(key, default)
    if value in (None, ""):
        return default
    return float(value)


def _as_bool(data: dict, key: str, default: bool) -> bool:
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on")


def config_from_data(data: dict) -> OptimizerConfig:
    """Build runtime config from a config entry or YAML dict."""
    return OptimizerConfig(
        battery_soc=str(data[CONF_BATTERY_SOC]),
        pv_power=_as_optional_str(data, CONF_PV_POWER),
        pv_power_sensors=_as_list(data.get(CONF_PV_POWER_SENSORS)),
        load_power=_as_optional_str(data, CONF_LOAD_POWER),
        grid_power=_as_optional_str(data, CONF_GRID_POWER),
        grid_power_sensors=_as_list(data.get(CONF_GRID_POWER_SENSORS)),
        battery_current=_as_optional_str(data, CONF_BATTERY_CURRENT),
        battery_state=_as_optional_str(data, CONF_BATTERY_STATE),
        price_sensor=_as_optional_str(data, CONF_PRICE_SENSOR),
        work_mode=_as_optional_str(data, CONF_WORK_MODE),
        grid_charging_enable=_as_optional_str(data, CONF_GRID_CHARGING_ENABLE),
        soc_target=_as_optional_str(data, CONF_SOC_TARGET),
        soc_targets=_as_list(data.get(CONF_SOC_TARGETS)),
        max_charge_current=_as_optional_str(data, CONF_MAX_CHARGE_CURRENT),
        max_discharge_current=_as_optional_str(data, CONF_MAX_DISCHARGE_CURRENT),
        grid_charging_current=_as_optional_str(data, CONF_GRID_CHARGING_CURRENT),
        grid_max_export_power=_as_optional_str(data, CONF_GRID_MAX_EXPORT_POWER),
        peak_shaving_enable=_as_optional_str(data, CONF_PEAK_SHAVING_ENABLE),
        peak_shaving_power=_as_optional_str(data, CONF_PEAK_SHAVING_POWER),
        battery_capacity_kwh=_as_float(data, CONF_BATTERY_CAPACITY_KWH, 32.14),
        nominal_voltage_v=_as_float(data, CONF_NOMINAL_VOLTAGE, 51.2),
        min_voltage_v=_as_float(data, CONF_MIN_VOLTAGE, 48.0),
        min_soc_percent=_as_float(data, CONF_MIN_SOC, 15.0),
        max_soc_percent=_as_float(data, CONF_MAX_SOC, 100.0),
        target_soc_percent=_as_float(data, CONF_TARGET_SOC, 80.0),
        export_floor_soc_percent=_as_float(data, CONF_EXPORT_FLOOR_SOC, 35.0),
        max_charge_a=_as_float(data, CONF_MAX_CHARGE_A, 250.0),
        max_discharge_a=_as_float(data, CONF_MAX_DISCHARGE_A, 250.0),
        max_charge_w=_as_float(data, CONF_MAX_CHARGE_W, 12000.0),
        max_discharge_w=_as_float(data, CONF_MAX_DISCHARGE_W, 12000.0),
        min_charge_a=_as_float(data, CONF_MIN_CHARGE_A, 10.0),
        round_step_a=_as_float(data, CONF_ROUND_STEP_A, 5.0),
        cycle_cost_per_kwh=_as_float(data, CONF_CYCLE_COST, 0.08),
        peak_shaving_threshold_w=(
            None
            if data.get(CONF_PEAK_SHAVING_THRESHOLD_W) in (None, "")
            else float(data[CONF_PEAK_SHAVING_THRESHOLD_W])
        ),
        enable_export=_as_bool(data, CONF_EXPORT_ENABLED, False),
        shadow_mode=_as_bool(data, CONF_SHADOW_MODE, True),
        auto_execute=_as_bool(data, CONF_AUTO_EXECUTE, False),
        scan_interval=int(_as_float(data, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
    )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration services."""
    hass.data.setdefault(DOMAIN, {})

    async def _first_coordinator() -> VtacDeyeCoordinator | None:
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        return coordinators[0] if coordinators else None

    async def _handle_replan(call: ServiceCall) -> None:
        coordinator = await _first_coordinator()
        if coordinator:
            await coordinator.async_refresh(execute=False)

    async def _handle_apply(call: ServiceCall) -> None:
        coordinator = await _first_coordinator()
        if coordinator:
            await coordinator.async_apply_current()

    async def _handle_force(call: ServiceCall) -> None:
        coordinator = await _first_coordinator()
        if coordinator:
            await coordinator.async_force(call.data["mode"], int(call.data.get("minutes", 60)))

    hass.services.async_register(DOMAIN, "replan", _handle_replan)
    hass.services.async_register(DOMAIN, "apply_current", _handle_apply)
    hass.services.async_register(
        DOMAIN,
        "force_mode",
        _handle_force,
        schema=vol.Schema(
            {
                vol.Required("mode"): vol.In(
                    [MODE_CHARGE, MODE_EXPORT, MODE_IDLE, MODE_SELF_CONSUMPTION]
                ),
                vol.Optional("minutes", default=60): vol.Coerce(int),
            }
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up a config entry created from the UI."""
    optimizer_config = config_from_data(dict(entry.data))
    coordinator = VtacDeyeCoordinator(hass, optimizer_config)
    coordinator.name = entry.data.get(CONF_NAME, "VTAC Deye Optimizer")
    coordinator.entry_id = entry.entry_id
    coordinator.entities = []

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if coordinator:
        await coordinator.async_stop()
    return unload_ok
