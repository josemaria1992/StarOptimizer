# VTAC Deye Optimizer

Home Assistant custom integration for VTAC battery systems connected to a Deye
hybrid inverter through Solarman entities.

It is inspired by Darkstar's Deye executor profile and starts safely in shadow
mode. The integration plans `charge`, `export`, `idle`, and `self_consumption`
intents from Nord Pool prices, battery SoC, and your Deye limits.

## HACS Installation

1. In Home Assistant, open HACS.
2. Go to Integrations.
3. Open the three-dot menu and choose Custom repositories.
4. Add this repository URL as an Integration.
5. Install `VTAC Deye Optimizer`.
6. Restart Home Assistant.

## Configuration

Add this to `configuration.yaml` and keep `shadow_mode: true` until the planned
actions look right.

```yaml
vtac_deye_optimizer:
  name: VTAC Deye Optimizer
  battery_soc: sensor.inverter_battery
  battery_state: sensor.inverter_battery_state
  battery_current: sensor.inverter_battery_current
  load_power: sensor.inverter_load_power
  grid_power_sensors:
    - sensor.inverter_external_ct1_power
    - sensor.inverter_external_ct2_power
    - sensor.inverter_external_ct3_power
  price_sensor: sensor.nordpool_kwh_se4_sek_3_10_025

  work_mode: select.inverter_work_mode
  grid_charging_enable: switch.inverter_battery_grid_charging
  soc_targets:
    - number.inverter_program_1_soc
    - number.inverter_program_2_soc
    - number.inverter_program_3_soc
    - number.inverter_program_4_soc
    - number.inverter_program_5_soc
    - number.inverter_program_6_soc
  max_charge_current: number.inverter_battery_max_charging_current
  max_discharge_current: number.inverter_battery_max_discharging_current
  grid_charging_current: number.inverter_battery_grid_charging_current
  peak_shaving_enable: switch.inverter_grid_peak_shaving
  peak_shaving_power: number.inverter_grid_peak_shaving

  battery_capacity_kwh: 32.14
  nominal_voltage_v: 51.2
  min_voltage_v: 48.0
  min_soc_percent: 15
  target_soc_percent: 80
  export_floor_soc_percent: 35
  max_charge_a: 250
  max_discharge_a: 250
  max_charge_w: 12000
  max_discharge_w: 12000
  peak_shaving_threshold_w: 10000

  cycle_cost_per_kwh: 0.08
  enable_export: false
  shadow_mode: true
  auto_execute: false
  scan_interval: 300
```

## Entities

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
