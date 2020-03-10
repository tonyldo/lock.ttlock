"""
Component to integrate with TTlock API.

For more details about this component, please refer to
https://github.com/tonyldo/lock.ttlock
"""
import datetime
import json
import logging
import os
from datetime import datetime, time, timedelta

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
from integrationhelper.const import CC_STARTUP_VERSION

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_API_GATEWAY_LOCKS_RESOURCE,
    CONF_API_GATEWAY_RESOURCE,
    CONF_API_OAUTH_RESOURCE,
    CONF_API_URI,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_FILENAME,
    DEFAULT_NAME,
    DOMAIN,
    ISSUE_URL,
    PLATFORMS,
    REQUIRED_FILES,
    VERSION,
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
                vol.Optional(
                    CONF_API_GATEWAY_LOCKS_RESOURCE, default="v3/gateway/listLock"
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

    hass.data[DOMAIN] = TTlock(hass, config)

    # Check the token validated
    try:
        hass.data[DOMAIN].check_token_file()
    except Exception as e:
        _LOGGER.error("Erro while setup ttlock component: {}".format(e.__cause__))
        return False

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
        self.api_gateway_locks_resource = config[DOMAIN].get(
            CONF_API_GATEWAY_LOCKS_RESOURCE
        )
        self.redirect_url = f"{hass.config.api.base_url}/"
        self.full_path_token_file = f"{hass.config.path()}/custom_components/{DOMAIN}/{config[DOMAIN].get(CONF_TOKEN_FILENAME)}"
        self.gateways = ""
        self.locks = ""

    async def update_data(self):
        """Update data."""
        # This is where the main logic to update platform data goes.
        try:
            self.check_token_file()
        except Exception as error:
            _LOGGER.info(repr(error))

    def check_token_file(self):
        """Token validate verify."""
        if not os.path.exists(self.full_path_token_file):
            _LOGGER.info("Token File ({}) not exist.".format(self.full_path_token_file))
            self.refresh_access_token()
        else:
            will_expire = False
            with open(self.full_path_token_file) as json_file:
                data = json.load(json_file)
                expire_date = datetime.fromtimestamp(data["expire_date"])
                today = datetime.fromtimestamp(time.time())
                if (expire_date - today).delta < 7:
                    _LOGGER.info("Access token will expire soon.")
                    will_expire = True
            if will_expire:
                self.refresh_access_token()

    def get_gateway_from_account(self,_pageNo=1):
        """list of gateways"""
        _url_request = "https://{}/{}?client_id={}&accessToken={}&pageNo={}&pageSize=20&date={}".format(
            self.api_uri,
            self.api_gateway_resource,
            self.client_id,
            self.access_token,
            _pageNo,
            time.time(),
        )
        _response = self.send_resources_request(_url_request).json()

        if len(_response["list"])==0:
            return _response["list"]
        else:
            return _response["list"] + self.get_gateway_from_account(_pageNo=_pageNo+1)

    def get_locks_from_gateway(self):
        """list of locks"""
        for gateway in self.gateways:
            _url_request = "https://{}/{}?clientId={}&accessToken={}&gatewayId={}&date={}".format(
                self.api_uri,
                self.api_gateway_locks_resource,
                self.client_id,
                self.access_token,
                gateway["gatewayId"],
                time.time(),
            )
            _request = self.send_resources_request(_url_request)
            self.locks = self.locks + [(gateway["gatewayId"],_request.json()["list"])]

    def send_resources_request(self, _url_request):
        try:
            return self.send_request(_url_request)
        except PermissionError as error:
            _LOGGER.info(repr(error))
            self.refresh_access_token()

    def refresh_access_token(self):
        """if token will expire, refresh"""
        _LOGGER.info("Generating a new Access token.")
        _url_request = "https://{}/{}?client_id={}&client_secret={}&grant_type=refresh_token&refresh_token={}&redirect_uri={}".format(
            self.api_uri,
            self.api_oauth_resource,
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.redirect_url,
        )

        _response = self.send_request(_url_request)

        self.access_token = _response["access_token"]
        self.refresh_token = _response["refresh_token"]
        _expire_date = datetime.fromtimestamp(
            time.time() + (_response["expires_in"] * 1000)
        )
        _response["expire_date"] = _expire_date

        try:
            os.remove(self.full_path_token_file)
        except:
            _LOGGER.info("Error while deleting Token file")

        with open(self.full_path_token_file, "w") as outfile:
            json.dump(_response, outfile)

    def send_request(self, _url_request):
        from integrationhelper.const import GOOD_HTTP_CODES

        TOKEN_ERROR_CODES = [10003]
        _headers = {"Content-Type": "application/x-www-form-urlencoded"}
        _request = requests.post(_url_request, headers=_headers)
        if _request.status_code not in GOOD_HTTP_CODES:
            raise Exception("HTTP_ERROR", _request.status_code)
        else:
            if _request.json()["errcode"]
                if _request.json()["errcode"] in TOKEN_ERROR_CODES:
                    raise PermissionError("API_TOKEN_ERROR",_request.json()["errcode"])
                else:
                    raise Exception("API_ERROR", _request.json()["errcode"])
                    
        return _request.json()
