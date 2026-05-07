# VTAC Deye Optimizer

Home Assistant custom integration inspired by Darkstar's Deye executor profile.

It reads battery SoC, PV/load power, and optional Nord Pool style prices, builds a
simple rolling schedule, and writes these Deye/SunSynk controls:

- work mode: `Zero Export To CT` or `Export First`
- grid charging switch
- six Deye time-program SoC targets
- max charge current safety limit
- grid charge current target
- max discharge current
- optional peak shaving threshold
- optional export power limit

Start with `shadow_mode: true` and `auto_execute: false`.

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

The integration writes all six `number.inverter_program_*_soc` entities to the same target.
That keeps Deye's time-program SoC floor aligned with the current optimizer intent.

For grid charging, `max_charge_current` is treated as the 250 A safety ceiling, while
`grid_charging_current` is the actual target current calculated from the planned kW.

After restart, use:

- `sensor.vtac_deye_optimizer_status`
- `sensor.vtac_deye_optimizer_current_action`
- `sensor.vtac_deye_optimizer_schedule`
- `button.vtac_deye_optimizer_replan`
- `button.vtac_deye_optimizer_apply_current`
- `switch.vtac_deye_optimizer_shadow_mode`
- `switch.vtac_deye_optimizer_auto_execute`
