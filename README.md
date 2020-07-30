# TTLock

[![License][license-shield]](LICENSE.md)
[![hacs][hacsbadge]][hacs]
[![Project Stage][releases-shield]]

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show info from ttlock API.
`lock` | Control ttlock lock devices.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `blueprint`.
4. Download _all_ the files from the `custom_components/ttlock/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. Add `ttlock:` to your HA configuration.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/ttlock/.translations/en.json
custom_components/ttlock/.translations/nb.json
custom_components/ttlock/.translations/sensor.nb.json
custom_components/ttlock/__init__.py
custom_components/ttlock/binary_sensor.py
custom_components/ttlock/config_flow.py
custom_components/ttlock/const.py
custom_components/ttlock/manifest.json
custom_components/ttlock/sensor.py
custom_components/ttlock/switch.py
```

## Example configuration.yaml

```yaml
ttlock:
  client_id: ""
  client_secret: ""
  access_token: ""
  refresh_token: ""
```

## Configuration options

Key | Type | Required | Description
-- | -- | -- | --
`client_id` | `string` | `True` | The app_id which is assigned by system when you create an application.
`client_secret` | `string` | `True` | The app_secret which is assigned by system when you create an application.
`access_token` | `string` | `True` | Access token.
`refresh_token` | `string` | `True` | Refresh token.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***
[blueprint]: https://github.com/custom-components/blueprint
[buymecoffee]: https://www.buymeacoffee.com/ludeeus
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/blueprint.svg?style=for-the-badge
[commits]: https://github.com/custom-components/blueprint/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Joakim%20Sørensen%20%40ludeeus-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/custom-components/blueprint.svg?style=for-the-badge
[releases]: https://github.com/custom-components/blueprint/releases
