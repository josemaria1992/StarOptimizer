"""Coordinator for the VTAC Deye Optimizer integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .executor import apply_slot
from .models import OptimizerConfig, OptimizerState, PlanSlot
from .planner import build_schedule, read_prices, read_snapshot

_LOGGER = logging.getLogger(__name__)


class VtacDeyeCoordinator:
    """Owns planning, execution, and shared entity state."""

    def __init__(self, hass: HomeAssistant, config: OptimizerConfig) -> None:
        self.hass = hass
        self.config = config
        self.state = OptimizerState(
            shadow_mode=config.shadow_mode,
            auto_execute=config.auto_execute,
        )
        self._unsub_interval = None

    async def async_start(self) -> None:
        """Start periodic updates."""
        await self.async_refresh(execute=self.config.auto_execute)
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._handle_interval,
            timedelta(seconds=self.config.scan_interval),
        )

    async def async_stop(self) -> None:
        """Stop periodic updates."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None

    async def _handle_interval(self, _now) -> None:
        await self.async_refresh(execute=self.config.auto_execute)

    async def async_refresh(self, execute: bool = False) -> None:
        """Rebuild schedule and optionally apply the current slot."""
        try:
            snapshot = read_snapshot(self.hass, self.config)
            prices = read_prices(self.hass, self.config.price_sensor)
            schedule = build_schedule(self.config, snapshot, prices)
            current = schedule[0] if schedule else None

            self.state.snapshot = snapshot
            self.state.schedule = schedule
            self.state.current_slot = current
            self.state.last_error = None
            self.state.last_update = snapshot.timestamp
            self.state.shadow_mode = self.config.shadow_mode
            self.state.auto_execute = self.config.auto_execute

            if execute and current:
                self.state.last_action = await apply_slot(self.hass, self.config, current)

            self.async_write_ha_state()
        except Exception as err:  # noqa: BLE001 - HA integrations should surface runtime failures
            _LOGGER.exception("VTAC/Deye optimizer refresh failed")
            self.state.last_error = str(err)
            self.async_write_ha_state()

    async def async_apply_current(self) -> None:
        """Apply the current planned slot now."""
        if not self.state.current_slot:
            await self.async_refresh(execute=False)
        if not self.state.current_slot:
            raise RuntimeError("No current slot available")
        self.state.last_action = await apply_slot(self.hass, self.config, self.state.current_slot)
        self.async_write_ha_state()

    async def async_force(self, mode: str, minutes: int = 60) -> None:
        """Apply an immediate temporary intent."""
        if not self.state.current_slot:
            await self.async_refresh(execute=False)
        base = self.state.current_slot
        if not base:
            raise RuntimeError("No current slot available")

        target_soc = self.config.target_soc_percent
        if mode == "export":
            target_soc = self.config.export_floor_soc_percent
        elif mode == "idle" and self.state.snapshot:
            target_soc = self.state.snapshot.soc_percent

        slot = PlanSlot(
            start=base.start,
            end=base.end,
            price=base.price,
            mode=mode,
            charge_kw=self.config.max_charge_w / 1000.0 if mode == "charge" else 0.0,
            discharge_kw=self.config.max_discharge_w / 1000.0 if mode == "export" else 0.0,
            export_kw=self.config.max_discharge_w / 1000.0 if mode == "export" else 0.0,
            soc_target=round(target_soc),
            reason=f"manual force for {minutes} minutes",
        )
        self.state.current_slot = slot
        self.state.last_action = await apply_slot(self.hass, self.config, slot)
        self.async_write_ha_state()

    def async_write_ha_state(self) -> None:
        """Notify registered entities that coordinator state changed."""
        for entity in getattr(self, "entities", []):
            entity.async_write_ha_state()
