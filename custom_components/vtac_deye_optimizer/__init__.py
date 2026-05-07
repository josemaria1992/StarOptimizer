"""Home Assistant integration for VTAC batteries with Deye inverters."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

from .const import (
    CONF_AUTO_EXECUTE,
    CONF_BATTERY_CAPACITY_KWH,
    CONF_BATTERY_CURRENT,
    CONF_BATTERY_SOC,
    CONF_BATTERY_STATE,
    CONF_CYCLE_COST,
    CONF_EXPORT_ENABLED,
    CONF_EXPORT_FLOOR_SOC,
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
    CONF_PEAK_SHAVING_ENABLE,
    CONF_PEAK_SHAVING_POWER,
    CONF_PEAK_SHAVING_THRESHOLD_W,
    CONF_MIN_SOC,
    CONF_MIN_VOLTAGE,
    CONF_NOMINAL_VOLTAGE,
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
    CONF_GRID_CHARGING_ENABLE,
    CONF_GRID_CHARGING_CURRENT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_CHARGE,
    MODE_EXPORT,
    MODE_IDLE,
    MODE_SELF_CONSUMPTION,
)
from .coordinator import VtacDeyeCoordinator
from .models import OptimizerConfig

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default="VTAC Deye Optimizer"): cv.string,
                vol.Required(CONF_BATTERY_SOC): cv.entity_id,
                vol.Optional(CONF_PV_POWER): cv.entity_id,
                vol.Optional(CONF_PV_POWER_SENSORS, default=[]): vol.All(
                    cv.ensure_list, [cv.entity_id]
                ),
                vol.Optional(CONF_LOAD_POWER): cv.entity_id,
                vol.Optional(CONF_GRID_POWER): cv.entity_id,
                vol.Optional(CONF_GRID_POWER_SENSORS, default=[]): vol.All(
                    cv.ensure_list, [cv.entity_id]
                ),
                vol.Optional(CONF_BATTERY_CURRENT): cv.entity_id,
                vol.Optional(CONF_BATTERY_STATE): cv.entity_id,
                vol.Optional(CONF_PRICE_SENSOR): cv.entity_id,
                vol.Optional(CONF_WORK_MODE): cv.entity_id,
                vol.Optional(CONF_GRID_CHARGING_ENABLE): cv.entity_id,
                vol.Optional(CONF_SOC_TARGET): cv.entity_id,
                vol.Optional(CONF_SOC_TARGETS, default=[]): vol.All(cv.ensure_list, [cv.entity_id]),
                vol.Optional(CONF_MAX_CHARGE_CURRENT): cv.entity_id,
                vol.Optional(CONF_MAX_DISCHARGE_CURRENT): cv.entity_id,
                vol.Optional(CONF_GRID_CHARGING_CURRENT): cv.entity_id,
                vol.Optional(CONF_GRID_MAX_EXPORT_POWER): cv.entity_id,
                vol.Optional(CONF_PEAK_SHAVING_ENABLE): cv.entity_id,
                vol.Optional(CONF_PEAK_SHAVING_POWER): cv.entity_id,
                vol.Optional(CONF_BATTERY_CAPACITY_KWH, default=32.14): vol.Coerce(float),
                vol.Optional(CONF_NOMINAL_VOLTAGE, default=51.2): vol.Coerce(float),
                vol.Optional(CONF_MIN_VOLTAGE, default=48.0): vol.Coerce(float),
                vol.Optional(CONF_MIN_SOC, default=15.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_SOC, default=100.0): vol.Coerce(float),
                vol.Optional(CONF_TARGET_SOC, default=80.0): vol.Coerce(float),
                vol.Optional(CONF_EXPORT_FLOOR_SOC, default=35.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_A, default=250.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_DISCHARGE_A, default=250.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_W, default=12000.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_DISCHARGE_W, default=12000.0): vol.Coerce(float),
                vol.Optional(CONF_MIN_CHARGE_A, default=10.0): vol.Coerce(float),
                vol.Optional(CONF_ROUND_STEP_A, default=5.0): vol.Coerce(float),
                vol.Optional(CONF_CYCLE_COST, default=0.08): vol.Coerce(float),
                vol.Optional(CONF_PEAK_SHAVING_THRESHOLD_W): vol.Coerce(float),
                vol.Optional(CONF_EXPORT_ENABLED, default=True): cv.boolean,
                vol.Optional(CONF_SHADOW_MODE, default=True): cv.boolean,
                vol.Optional(CONF_AUTO_EXECUTE, default=False): cv.boolean,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the optimizer from YAML."""
    raw = dict(config[DOMAIN])
    optimizer_config = OptimizerConfig(
        battery_soc=raw[CONF_BATTERY_SOC],
        pv_power=raw.get(CONF_PV_POWER),
        pv_power_sensors=list(raw.get(CONF_PV_POWER_SENSORS, [])),
        load_power=raw.get(CONF_LOAD_POWER),
        grid_power=raw.get(CONF_GRID_POWER),
        grid_power_sensors=list(raw.get(CONF_GRID_POWER_SENSORS, [])),
        battery_current=raw.get(CONF_BATTERY_CURRENT),
        battery_state=raw.get(CONF_BATTERY_STATE),
        price_sensor=raw.get(CONF_PRICE_SENSOR),
        work_mode=raw.get(CONF_WORK_MODE),
        grid_charging_enable=raw.get(CONF_GRID_CHARGING_ENABLE),
        soc_target=raw.get(CONF_SOC_TARGET),
        soc_targets=list(raw.get(CONF_SOC_TARGETS, [])),
        max_charge_current=raw.get(CONF_MAX_CHARGE_CURRENT),
        max_discharge_current=raw.get(CONF_MAX_DISCHARGE_CURRENT),
        grid_charging_current=raw.get(CONF_GRID_CHARGING_CURRENT),
        grid_max_export_power=raw.get(CONF_GRID_MAX_EXPORT_POWER),
        peak_shaving_enable=raw.get(CONF_PEAK_SHAVING_ENABLE),
        peak_shaving_power=raw.get(CONF_PEAK_SHAVING_POWER),
        battery_capacity_kwh=raw[CONF_BATTERY_CAPACITY_KWH],
        nominal_voltage_v=raw[CONF_NOMINAL_VOLTAGE],
        min_voltage_v=raw[CONF_MIN_VOLTAGE],
        min_soc_percent=raw[CONF_MIN_SOC],
        max_soc_percent=raw[CONF_MAX_SOC],
        target_soc_percent=raw[CONF_TARGET_SOC],
        export_floor_soc_percent=raw[CONF_EXPORT_FLOOR_SOC],
        max_charge_a=raw[CONF_MAX_CHARGE_A],
        max_discharge_a=raw[CONF_MAX_DISCHARGE_A],
        max_charge_w=raw[CONF_MAX_CHARGE_W],
        max_discharge_w=raw[CONF_MAX_DISCHARGE_W],
        min_charge_a=raw[CONF_MIN_CHARGE_A],
        round_step_a=raw[CONF_ROUND_STEP_A],
        cycle_cost_per_kwh=raw[CONF_CYCLE_COST],
        peak_shaving_threshold_w=raw.get(CONF_PEAK_SHAVING_THRESHOLD_W),
        enable_export=raw[CONF_EXPORT_ENABLED],
        shadow_mode=raw[CONF_SHADOW_MODE],
        auto_execute=raw[CONF_AUTO_EXECUTE],
        scan_interval=raw[CONF_SCAN_INTERVAL],
    )

    coordinator = VtacDeyeCoordinator(hass, optimizer_config)
    coordinator.name = raw.get(CONF_NAME, "VTAC Deye Optimizer")
    coordinator.entities = []
    hass.data[DOMAIN] = coordinator

    await coordinator.async_start()
    await async_load_platform(hass, "sensor", DOMAIN, {}, config)
    await async_load_platform(hass, "switch", DOMAIN, {}, config)
    await async_load_platform(hass, "button", DOMAIN, {}, config)

    async def _handle_replan(call: ServiceCall) -> None:
        await coordinator.async_refresh(execute=False)

    async def _handle_apply(call: ServiceCall) -> None:
        await coordinator.async_apply_current()

    async def _handle_force(call: ServiceCall) -> None:
        mode = call.data["mode"]
        minutes = int(call.data.get("minutes", 60))
        await coordinator.async_force(mode, minutes)

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
