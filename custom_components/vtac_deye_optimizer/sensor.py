"""Sensors for VTAC Deye Optimizer."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import VtacDeyeCoordinator


async def async_setup_platform(
    hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Set up optimizer sensors."""
    coordinator: VtacDeyeCoordinator = hass.data[DOMAIN]
    entities: list[Entity] = [
        OptimizerStatusSensor(coordinator),
        OptimizerActionSensor(coordinator),
        OptimizerScheduleSensor(coordinator),
    ]
    coordinator.entities.extend(entities)
    async_add_entities(entities)


class _BaseOptimizerSensor(SensorEntity):
    def __init__(self, coordinator: VtacDeyeCoordinator, suffix: str) -> None:
        self.coordinator = coordinator
        self._attr_name = f"{coordinator.name} {suffix}"
        self._attr_unique_id = f"{DOMAIN}_{suffix.lower().replace(' ', '_')}"

    @property
    def available(self) -> bool:
        return self.coordinator.state.last_error is None


class OptimizerStatusSensor(_BaseOptimizerSensor):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Status")

    @property
    def native_value(self) -> str:
        if self.coordinator.state.last_error:
            return "error"
        if self.coordinator.state.shadow_mode:
            return "shadow"
        return "auto" if self.coordinator.state.auto_execute else "ready"

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.coordinator.state.snapshot
        return {
            "last_error": self.coordinator.state.last_error,
            "last_update": self.coordinator.state.last_update.isoformat()
            if self.coordinator.state.last_update
            else None,
            "soc_percent": snapshot.soc_percent if snapshot else None,
            "pv_kw": snapshot.pv_kw if snapshot else None,
            "load_kw": snapshot.load_kw if snapshot else None,
            "grid_kw": snapshot.grid_kw if snapshot else None,
            "battery_current_a": snapshot.battery_current_a if snapshot else None,
            "battery_state": snapshot.battery_state if snapshot else None,
        }


class OptimizerActionSensor(_BaseOptimizerSensor):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Current Action")

    @property
    def native_value(self) -> str:
        slot = self.coordinator.state.current_slot
        return slot.mode if slot else "unknown"

    @property
    def extra_state_attributes(self) -> dict:
        slot = self.coordinator.state.current_slot
        return slot.as_dict() if slot else {}


class OptimizerScheduleSensor(_BaseOptimizerSensor):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Schedule")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.state.schedule)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "slots": [slot.as_dict() for slot in self.coordinator.state.schedule],
            "last_action": self.coordinator.state.last_action,
        }
