"""
Component to integrate with TTlock API.

For more details about this component, please refer to
https://github.com/tonyldo/lock.ttlock
"""
import os
import datetime
from datetime import timedelta
from datetime import datetime
from datetime import date
from datetime import time
import requests
import logging
import json
import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.util import Throttle

from integrationhelper.const import CC_STARTUP_VERSION

from .const import (
    CONF_CLIENT_ID,
    CONF_API_URI,
    CONF_CLIENT_SECRET,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    DEFAULT_NAME,
    DOMAIN,
    ISSUE_URL,
    PLATFORMS,
    REQUIRED_FILES,
    VERSION,
    CONF_TOKEN_FILENAME,
    CONF_API_OAUTH_RESOURCE,
    CONF_API_GATEWAY_RESOURCE,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
                vol.Required(CONF_ACCESS_TOKEN): cv.string,
                vol.Required(CONF_REFRESH_TOKEN): cv.string,
                vol.Optional(CONF_API_URI, default="https://api.ttlock.com"): cv.string,
                vol.Optional(
                    CONF_API_OAUTH_RESOURCE, default="oauth2/token"
                ): cv.string,
                vol.Optional(
                    CONF_API_GATEWAY_RESOURCE, default="v3/gateway/list"
                ): cv.string,
                vol.Optional(CONF_TOKEN_FILENAME, default="token.json"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up this component using YAML."""
    if config.get(DOMAIN) is None:
        # We get here if the integration is set up using config flow
        return True

    # Print startup message
    _LOGGER.info(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    # Create DATA dict
    hass.data[DOMAIN] = {}

    hass.data[DOMAIN] = TTlock(hass, config)

    # Check the token validated
    hass.data[DOMAIN].check_token_file()

    # Load platforms
    for platform in PLATFORMS:
        # Get platform specific configuration
        platform_config = config[DOMAIN].get(platform, {})

        # If platform is not enabled, skip.
        if not platform_config:
            continue

        for entry in platform_config:
            entry_config = entry

            hass.async_create_task(
                discovery.async_load_platform(
                    hass, platform, DOMAIN, entry_config, config
                )
            )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    return True


class TTlock:
    """This class handle communication with the TTlock API."""

    def __init__(self, hass, config):
        """Initialize the class."""
        # Get "global" configuration.
        self._hass = hass
        self.client_id = config[DOMAIN].get(CONF_CLIENT_ID)
        self.client_secret = config[DOMAIN].get(CONF_CLIENT_SECRET)
        self.access_token = config[DOMAIN].get(CONF_ACCESS_TOKEN)
        self.refresh_token = config[DOMAIN].get(CONF_REFRESH_TOKEN)
        self.api_uri = config[DOMAIN].get(CONF_API_URI)
        self.api_oauth_resource = config[DOMAIN].get(CONF_API_OAUTH_RESOURCE)
        self.api_gateway_resource = config[DOMAIN].get(CONF_API_GATEWAY_RESOURCE)
        self.redirect_url = f"{hass.config.api.base_url}/"
        self.component_path = f"{hass.config.path()}/custom_components/{DOMAIN}/"
        self._token_file = config[DOMAIN].get(CONF_TOKEN_FILENAME)
        self.gateways = ""
        self.locks = ""

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update_data(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        try:
            self.check_token_file()

        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.error("Could not update data - %s", error)

    def check_token_file(self):
        """Token validate verify."""
        fullpath = "{}{}".format(self.component_path, self._token_file)
        if not os.path.exists(fullpath):
            _LOGGER.info("Token File ({}) not exist.".format(self._token_file))
            self.refresh_access_token()
        else:
            will_expire = False
            with open(self._token_file) as json_file:
                data = json.load(json_file)
                expire_date = datetime.fromtimestamp(data["expire_date"])
                today = datetime.fromtimestamp(time.time())
                if (expire_date - today).delta < 7:
                    _LOGGER.info("Access token will expire soon.")
                    will_expire = True
            if will_expire:
                self.refresh_access_token()

    def get_gateway_from_account(self):
        """list of gateways"""
        _headers = {"Content-Type": "application/x-www-form-urlencoded"}
        _request = requests.post(
            "https://{}/{}?client_id={}&accessToken={}&pageNo=1&pageSize=20&date={}".format(
                self.api_uri,
                self.api_gateway_resource,
                self.client_id,
                self.access_token,
                time.time(),
            ),
            headers=_headers,
        )
        self.gateways = _request.json()

    def get_locks_from_gateway(self):
        """list of locks"""
        for gateway in self.gateways["list"]:
            _headers = {"Content-Type": "application/x-www-form-urlencoded"}
            _request = requests.post(
                "https://{}/{}?client_id={}&accessToken={}&gatewayId={}&date={}".format(
                    self.api_uri,
                    self.api_gateway_resource,
                    self.client_id,
                    self.access_token,
                    gateway["gatewayId"],
                    time.time(),
                ),
                headers=_headers,
            )
            self.locks = _request.json()

    def refresh_access_token(self):
        """if token will expire, refresh"""
        _LOGGER.info("Generating a new Access token.")
        _headers = {"Content-Type": "application/x-www-form-urlencoded"}
        _request = requests.post(
            "https://{}/{}?client_id={}&client_secret={}&grant_type=refresh_token&refresh_token={}&redirect_uri={}".format(
                self.api_uri,
                self.api_oauth_resource,
                self.client_id,
                self.client_secret,
                self.refresh_token,
                self.redirect_url,
            ),
            headers=_headers,
        )
        _response = _request.json()
        _expire_date = datetime.fromtimestamp(
            time.time() + (_response["expires_in"] * 1000)
        )
        _response["expire_date"] = _expire_date
        with open(self._token_file, "w") as outfile:
            json.dump(_response, outfile)
