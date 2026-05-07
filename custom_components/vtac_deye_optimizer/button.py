"""Buttons for VTAC Deye Optimizer."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MODE_CHARGE, MODE_EXPORT, MODE_IDLE
from .coordinator import VtacDeyeCoordinator


async def async_setup_platform(
    hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Set up optimizer buttons."""
    coordinator: VtacDeyeCoordinator = hass.data[DOMAIN]
    entities: list[Entity] = [
        ReplanButton(coordinator),
        ApplyCurrentButton(coordinator),
        ForceModeButton(coordinator, "Force Charge", MODE_CHARGE),
        ForceModeButton(coordinator, "Force Export", MODE_EXPORT),
        ForceModeButton(coordinator, "Force Stop", MODE_IDLE),
    ]
    coordinator.entities.extend(entities)
    async_add_entities(entities)


class _BaseOptimizerButton(ButtonEntity):
    def __init__(self, coordinator: VtacDeyeCoordinator, suffix: str) -> None:
        self.coordinator = coordinator
        self._attr_name = f"{coordinator.name} {suffix}"
        self._attr_unique_id = f"{DOMAIN}_{suffix.lower().replace(' ', '_')}"


class ReplanButton(_BaseOptimizerButton):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Replan")

    async def async_press(self) -> None:
        await self.coordinator.async_refresh(execute=False)


class ApplyCurrentButton(_BaseOptimizerButton):
    def __init__(self, coordinator: VtacDeyeCoordinator) -> None:
        super().__init__(coordinator, "Apply Current")

    async def async_press(self) -> None:
        await self.coordinator.async_apply_current()


class ForceModeButton(_BaseOptimizerButton):
    def __init__(self, coordinator: VtacDeyeCoordinator, suffix: str, mode: str) -> None:
        super().__init__(coordinator, suffix)
        self._mode = mode

    async def async_press(self) -> None:
        await self.coordinator.async_force(self._mode)
