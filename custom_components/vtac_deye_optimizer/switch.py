"""Switches for VTAC Deye Optimizer."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import VtacDeyeCoordinator


async def async_setup_platform(
    hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Set up optimizer switches."""
    coordinator: VtacDeyeCoordinator = next(iter(hass.data[DOMAIN].values()))
    _add_entities(coordinator, async_add_entities)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up optimizer switches from a config entry."""
    coordinator: VtacDeyeCoordinator = hass.data[DOMAIN][entry.entry_id]
    _add_entities(coordinator, async_add_entities)


def _add_entities(coordinator: VtacDeyeCoordinator, async_add_entities) -> None:
    """Add switch entities."""
    entities: list[Entity] = [
        OptimizerAutoSwitch(coordinator),
        OptimizerShadowSwitch(coordinator),
    ]
    coordinator.entities.extend(entities)
    async_add_entities(entities)


class _BaseOptimizerSwitch(SwitchEntity):
    def __init__(self, coordinator: VtacDeyeCoordinator, suffix: str) -> None:
        self.coordinator = coordinator
        self._attr_name = f"{coordinator.name} {suffix}"
        self._attr_unique_id = f"{DOMAIN}_{suffix.lower().replace(' ', '_')}"


class OptimizerAutoSwitch(_BaseOptimizerSwitch):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Auto Execute")

    @property
    def is_on(self) -> bool:
        return self.coordinator.config.auto_execute

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.config.auto_execute = True
        self.coordinator.state.auto_execute = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.config.auto_execute = False
        self.coordinator.state.auto_execute = False
        self.async_write_ha_state()


class OptimizerShadowSwitch(_BaseOptimizerSwitch):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Shadow Mode")

    @property
    def is_on(self) -> bool:
        return self.coordinator.config.shadow_mode

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.config.shadow_mode = True
        self.coordinator.state.shadow_mode = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.config.shadow_mode = False
        self.coordinator.state.shadow_mode = False
        self.async_write_ha_state()
