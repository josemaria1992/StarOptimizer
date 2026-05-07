# StarOptimizer

Home Assistant custom integration for VTAC battery systems connected to a Deye
hybrid inverter through Solarman entities.

It is inspired by Darkstar's Deye executor profile and starts safely in shadow
mode. The integration plans `charge`, `export`, `idle`, and `self_consumption`
intents from Nord Pool prices, battery SoC, and your Deye limits.

## HACS Installation

1. In Home Assistant, open HACS.
2. Go to Integrations.
3. Open the three-dot menu and choose Custom repositories.
4. Add this repository URL as an Integration:
   `https://github.com/josemaria1992/StarOptimizer`
5. Install `StarOptimizer`.
6. Restart Home Assistant.

## Add The Integration

Do not add anything to `configuration.yaml`.

After restart:

1. Go to `Settings -> Devices & services`.
2. Click `Add integration`.
3. Search for `VTAC Deye Optimizer`.
4. Submit the form. It is pre-filled with your Solarman entity names.
5. Keep `Shadow Mode` enabled at first.

## Default Entities

The setup form defaults to:

- `sensor.inverter_battery`
- `sensor.inverter_battery_state`
- `sensor.inverter_battery_current`
- `sensor.inverter_load_power`
- `sensor.inverter_external_ct1_power`
- `sensor.inverter_external_ct2_power`
- `sensor.inverter_external_ct3_power`
- `sensor.nordpool_kwh_se4_sek_3_10_025`
- `select.inverter_work_mode`
- `switch.inverter_battery_grid_charging`
- `number.inverter_program_1_soc` through `number.inverter_program_6_soc`
- `number.inverter_battery_max_charging_current`
- `number.inverter_battery_max_discharging_current`
- `number.inverter_battery_grid_charging_current`
- `switch.inverter_grid_peak_shaving`
- `number.inverter_grid_peak_shaving`

## Created Entities

- `sensor.vtac_deye_optimizer_status`
- `sensor.vtac_deye_optimizer_current_action`
- `sensor.vtac_deye_optimizer_schedule`
- `switch.vtac_deye_optimizer_shadow_mode`
- `switch.vtac_deye_optimizer_auto_execute`
- `button.vtac_deye_optimizer_replan`
- `button.vtac_deye_optimizer_apply_current`
- `button.vtac_deye_optimizer_force_charge`
- `button.vtac_deye_optimizer_force_export`
- `button.vtac_deye_optimizer_force_stop`

## Safety

This integration can write inverter control entities. Start in shadow mode and
confirm the generated schedule before enabling live execution. Battery BMS and
inverter hard limits remain your primary safety layer.
