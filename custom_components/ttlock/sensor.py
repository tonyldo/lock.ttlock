"""Sensor platform for ttlock."""
from homeassistant.helpers.entity import Entity
from .const import ATTRIBUTION, DEFAULT_NAME, ICON, DOMAIN


TTLOCK_SENSORS_MAP = {
    "electricQuantity": {"eid": "battery", "uom": "%", "icon": "mdi:battery-outline"},
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for device in hass.data[DOMAIN].get_locks(force_update = False):
        for sensor in TTLOCK_SENSORS_MAP.keys():
            if device[sensor] :
                entity = TTlockSensor(hass, device, sensor)
                entities.append(entity)

    if len(entities):
        async_add_entities(entities, update_before_add=False)

class SonoffSensor(TTlockDevice):
    """Representation of a Sonoff sensor."""

    def __init__(self, hass, lock, sensor = None):
        """Initialize the lock."""
        TTLockDevice.__init__(self, hass, lock)
        self._sensor        = sensor
        self._name          = '{} {}'.format(lock['lockName'], TTLOCK_SENSORS_MAP[self._sensor]['eid'])
        self._attributes    = {}

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return SONOFF_SENSORS_MAP[self._sensor]['uom']

    @property
    def state(self):
       """Return the state of the sensor."""
       return self.get_lock()[self._sensor]

    # entity id is required if the name use other characters not in ascii
    @property
    def entity_id(self):
        """Return the unique id of the switch."""
        entity_id = "{}.{}_{}".format(DOMAIN, self._lockid, TTLOCK_SENSORS_MAP[self._sensor]['eid'])
        return entity_id

    @property
    def icon(self):
        """Return the icon."""
        return TTLOCK_SENSORS_MAP[self._sensor]['icon']
