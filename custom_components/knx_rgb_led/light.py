"""KNX RGB LED Light Platform.

Implements a Home Assistant light entity backed by one or more KNX group
addresses using DPT 232.600 (3-byte RGB color).  Turning the light off sends
0x000000; turning it on re-sends the last used color.  The last color is
persisted via RestoreEntity so it survives HA restarts.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

try:
    from xknx.dpt import DPTArray
    from xknx.telegram import GroupAddress, Telegram
    from xknx.telegram.apci import GroupValueWrite
    _XKNX_AVAILABLE = True
except ImportError:
    _XKNX_AVAILABLE = False

from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_ADDRESSES, DEFAULT_COLOR

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ADDRESSES): vol.All(cv.ensure_list, [cv.string]),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the KNX RGB LED light platform from YAML configuration."""
    name: str = config[CONF_NAME]
    addresses: list[str] = config[CONF_ADDRESSES]
    async_add_entities([KNXRGBLEDLight(hass, name, addresses)])


class KNXRGBLEDLight(LightEntity, RestoreEntity):
    """Representation of a KNX RGB LED light (DPT 232.600).

    A single entity may write to multiple KNX group addresses so that one
    logical light can drive several physical LEDs simultaneously.
    """

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        addresses: list[str],
    ) -> None:
        """Initialize the KNX RGB LED light."""
        self._hass = hass
        self._attr_name = name
        sanitized = "_".join(addr.replace("/", "_") for addr in addresses)
        self._attr_unique_id = f"knx_rgb_led_{sanitized}"
        self._addresses = addresses
        self._is_on: bool = False
        self._rgb_color: tuple[int, int, int] = DEFAULT_COLOR

    # ------------------------------------------------------------------
    # RestoreEntity – recover state after a restart
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Restore last known state when HA starts."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        self._is_on = last_state.state == "on"
        if last_state.attributes.get(ATTR_RGB_COLOR):
            raw = last_state.attributes[ATTR_RGB_COLOR]
            if (
                isinstance(raw, (list, tuple))
                and len(raw) == 3
                and all(isinstance(v, int) for v in raw)
            ):
                self._rgb_color = (int(raw[0]), int(raw[1]), int(raw[2]))

    # ------------------------------------------------------------------
    # LightEntity properties
    # ------------------------------------------------------------------

    @property
    def is_on(self) -> bool:
        """Return True when the light is on."""
        return self._is_on

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the current RGB color."""
        return self._rgb_color

    # ------------------------------------------------------------------
    # Turn on / off
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally changing the RGB color."""
        if ATTR_RGB_COLOR in kwargs:
            self._rgb_color = kwargs[ATTR_RGB_COLOR]
        await self._send_color(self._rgb_color)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off by sending 0x000000 to all KNX addresses."""
        await self._send_color((0, 0, 0))
        self._is_on = False
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # KNX communication
    # ------------------------------------------------------------------

    async def _send_color(self, rgb: tuple[int, int, int]) -> None:
        """Send a 3-byte DPT 232.600 telegram to every configured address."""
        if not _XKNX_AVAILABLE:
            _LOGGER.error(
                "xknx library is not available – cannot send KNX telegrams. "
                "Ensure the KNX integration is installed."
            )
            return

        knx_module = self._hass.data.get("knx")
        if knx_module is None:
            _LOGGER.error(
                "KNX integration is not loaded. "
                "Make sure 'knx' is configured in configuration.yaml."
            )
            return

        xknx = knx_module.xknx
        r, g, b = (max(0, min(255, c)) for c in rgb)

        for address in self._addresses:
            try:
                telegram = Telegram(
                    destination_address=GroupAddress(address),
                    payload=GroupValueWrite(DPTArray((r, g, b))),
                )
                await xknx.telegrams.put(telegram)
                _LOGGER.debug(
                    "Sent RGB(%d, %d, %d) to KNX address %s", r, g, b, address
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "Failed to send telegram to KNX address %s", address
                )
