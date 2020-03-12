"""Sensor platform for blueprint."""
from homeassistant.helpers.entity import Entity
from .const import ATTRIBUTION, DEFAULT_NAME, ICON, DOMAIN


TTLOCK_SENSORS_MAP = {
    "battery": {"eid": "battery", "uom": "%", "icon": "mdi:battery-outline"},
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for device in hass.data[DOMAIN].get_locks(force_update = False):
        for sensor in SONOFF_SENSORS_MAP.keys():
            if device['params'].get(sensor) and device['params'].get(sensor) != "unavailable":
                entity = SonoffSensor(hass, device, sensor)
                entities.append(entity)

    if len(entities):
        async_add_entities(entities, update_before_add=False)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    async_add_devices([TTlockSensor(hass, {})], True)


class TTlockSensor(Entity):
    """blueprint Sensor class."""

    def __init__(self, hass, device, sensor=None):
        self.hass = hass
        self.attr = {}
        self._state = None

    async def async_update(self):
        """Update the sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN].update_data()

        # Get new data (if any)
        updated = self.hass.data[DOMAIN]["data"].get("data", {})

        # Check the data and update the value.
        if updated.get("static") is None:
            self._state = self._state
        else:
            self._state = updated.get("static")

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["time"] = str(updated.get("time"))
        self.attr["none"] = updated.get("none")

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return ""  # Don't hard code this, use something from the device/service.

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Blueprint",
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return ""

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.attr
