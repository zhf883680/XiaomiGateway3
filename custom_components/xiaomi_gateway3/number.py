from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    MAJOR_VERSION,
    MINOR_VERSION,
    LENGTH_METERS,
    TIME_SECONDS,
)
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .core.converters import Converter
from .core.device import XDevice
from .core.entity import XEntity, setup_entity
from .core.gateway import XGateway


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    def new_entity(gateway: XGateway, device: XDevice, conv: Converter) -> XEntity:
        return XiaomiNumber(gateway, device, conv)

    gw: XGateway = hass.data[DOMAIN][config_entry.entry_id]
    gw.add_setup(__name__, setup_entity(hass, config_entry, add_entities, new_entity))


UNITS = {
    "approach_distance": LENGTH_METERS,
    "occupancy_timeout": TIME_SECONDS,
}


# noinspection PyAbstractClass
class BackToTheNumberEntity(NumberEntity):
    if (MAJOR_VERSION, MINOR_VERSION) < (2022, 7):
        _attr_value: float = None

        async def async_set_value(self, value: float) -> None:
            await self.async_set_native_value(value)

        @property
        def _attr_native_value(self):
            return self._attr_value

        @_attr_native_value.setter
        def _attr_native_value(self, value):
            self._attr_value = value

        @property
        def _attr_native_min_value(self):
            return self._attr_min_value

        @_attr_native_min_value.setter
        def _attr_native_min_value(self, value):
            self._attr_min_value = value

        @property
        def _attr_native_max_value(self):
            return self._attr_max_value

        @_attr_native_max_value.setter
        def _attr_native_max_value(self, value):
            self._attr_max_value = value

        @property
        def _attr_native_step(self):
            return self._attr_step

        @_attr_native_step.setter
        def _attr_native_step(self, value):
            self._attr_step = value


# noinspection PyAbstractClass
class XiaomiNumber(XEntity, BackToTheNumberEntity):
    def __init__(self, gateway: "XGateway", device: XDevice, conv: Converter):
        super().__init__(gateway, device, conv)

        if self.attr in UNITS:
            self._attr_native_unit_of_measurement = UNITS[self.attr]

        if hasattr(conv, "min"):
            self._attr_native_min_value = conv.min
        if hasattr(conv, "max"):
            self._attr_native_max_value = conv.max
        if hasattr(conv, "step"):
            self._attr_native_step = conv.step

    @callback
    def async_set_state(self, data: dict):
        if self.attr in data:
            self._attr_native_value = data[self.attr]

    @callback
    def async_restore_last_state(self, state: float, attrs: dict):
        self._attr_native_value = state

    async def async_update(self):
        await self.device_read(self.subscribed_attrs)

    async def async_set_native_value(self, value: float) -> None:
        await self.device_send({self.attr: value})
