"""Config flow for VTAC Deye Optimizer."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

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
    CONF_GRID_POWER_SENSORS,
    CONF_LOAD_POWER,
    CONF_MAX_CHARGE_A,
    CONF_MAX_CHARGE_CURRENT,
    CONF_MAX_CHARGE_W,
    CONF_MAX_DISCHARGE_A,
    CONF_MAX_DISCHARGE_CURRENT,
    CONF_MAX_DISCHARGE_W,
    CONF_MIN_CHARGE_A,
    CONF_MIN_SOC,
    CONF_MIN_VOLTAGE,
    CONF_NOMINAL_VOLTAGE,
    CONF_PEAK_SHAVING_ENABLE,
    CONF_PEAK_SHAVING_POWER,
    CONF_PEAK_SHAVING_THRESHOLD_W,
    CONF_PRICE_SENSOR,
    CONF_ROUND_STEP_A,
    CONF_SCAN_INTERVAL,
    CONF_SHADOW_MODE,
    CONF_SOC_TARGETS,
    CONF_TARGET_SOC,
    CONF_WORK_MODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

DEFAULT_SOC_TARGETS = "\n".join(
    [
        "number.inverter_program_1_soc",
        "number.inverter_program_2_soc",
        "number.inverter_program_3_soc",
        "number.inverter_program_4_soc",
        "number.inverter_program_5_soc",
        "number.inverter_program_6_soc",
    ]
)

DEFAULT_GRID_POWER_SENSORS = "\n".join(
    [
        "sensor.inverter_external_ct1_power",
        "sensor.inverter_external_ct2_power",
        "sensor.inverter_external_ct3_power",
    ]
)


class VtacDeyeOptimizerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle UI setup for VTAC Deye Optimizer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Create the integration from a UI form."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id("vtac_deye_optimizer")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "VTAC Deye Optimizer"),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default="VTAC Deye Optimizer"): str,
                vol.Required(CONF_BATTERY_SOC, default="sensor.inverter_battery"): str,
                vol.Optional(
                    CONF_BATTERY_STATE, default="sensor.inverter_battery_state"
                ): str,
                vol.Optional(
                    CONF_BATTERY_CURRENT, default="sensor.inverter_battery_current"
                ): str,
                vol.Optional(CONF_LOAD_POWER, default="sensor.inverter_load_power"): str,
                vol.Optional(CONF_GRID_POWER_SENSORS, default=DEFAULT_GRID_POWER_SENSORS): str,
                vol.Optional(
                    CONF_PRICE_SENSOR, default="sensor.nordpool_kwh_se4_sek_3_10_025"
                ): str,
                vol.Required(CONF_WORK_MODE, default="select.inverter_work_mode"): str,
                vol.Required(
                    CONF_GRID_CHARGING_ENABLE,
                    default="switch.inverter_battery_grid_charging",
                ): str,
                vol.Required(CONF_SOC_TARGETS, default=DEFAULT_SOC_TARGETS): str,
                vol.Required(
                    CONF_MAX_CHARGE_CURRENT,
                    default="number.inverter_battery_max_charging_current",
                ): str,
                vol.Required(
                    CONF_MAX_DISCHARGE_CURRENT,
                    default="number.inverter_battery_max_discharging_current",
                ): str,
                vol.Required(
                    CONF_GRID_CHARGING_CURRENT,
                    default="number.inverter_battery_grid_charging_current",
                ): str,
                vol.Optional(
                    CONF_PEAK_SHAVING_ENABLE, default="switch.inverter_grid_peak_shaving"
                ): str,
                vol.Optional(CONF_PEAK_SHAVING_POWER, default="number.inverter_grid_peak_shaving"): str,
                vol.Optional(CONF_BATTERY_CAPACITY_KWH, default=32.14): vol.Coerce(float),
                vol.Optional(CONF_NOMINAL_VOLTAGE, default=51.2): vol.Coerce(float),
                vol.Optional(CONF_MIN_VOLTAGE, default=48.0): vol.Coerce(float),
                vol.Optional(CONF_MIN_SOC, default=15.0): vol.Coerce(float),
                vol.Optional(CONF_TARGET_SOC, default=80.0): vol.Coerce(float),
                vol.Optional(CONF_EXPORT_FLOOR_SOC, default=35.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_A, default=250.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_DISCHARGE_A, default=250.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_W, default=12000.0): vol.Coerce(float),
                vol.Optional(CONF_MAX_DISCHARGE_W, default=12000.0): vol.Coerce(float),
                vol.Optional(CONF_PEAK_SHAVING_THRESHOLD_W, default=10000.0): vol.Coerce(float),
                vol.Optional(CONF_MIN_CHARGE_A, default=10.0): vol.Coerce(float),
                vol.Optional(CONF_ROUND_STEP_A, default=5.0): vol.Coerce(float),
                vol.Optional(CONF_CYCLE_COST, default=0.08): vol.Coerce(float),
                vol.Optional(CONF_EXPORT_ENABLED, default=False): bool,
                vol.Optional(CONF_SHADOW_MODE, default=True): bool,
                vol.Optional(CONF_AUTO_EXECUTE, default=False): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
