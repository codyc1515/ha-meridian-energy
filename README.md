![Company logo](https://github.com/home-assistant/brands/blob/87e2d7c60931ee822776d2204244ef3eff4d22cf/custom_integrations/meridian_energy/logo.png?raw=true)

# Meridian Energy integration for Home Assistant
![image](https://github.com/codyc1515/ha-meridian-energy/assets/50791984/26e62938-ea81-4e7f-86a2-c5adf7da5d1f)

## Compatible plans

* Consumer EV Plan (Day & Night rates, with Solar)

Possibly others - let me know if you find one that works.

## Getting started
You will need to have an existing active consumer Meridian Energy account.

## Installation
Once installed, simply set-up from the `Devices and services` area. The first field is email and the next field is password for your account.

### HACS (recommended)
1. [Install HACS](https://hacs.xyz/docs/setup/download), if you did not already
2. [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=codyc1515&repository=ha-meridian-energy&category=integration)
3. Install the Meridian Energy integration
4. Restart Home Assistant

### Manually
Copy all files in the custom_components/meridian-energy folder to your Home Assistant folder *config/custom_components/meridian-energy*.

## Known issues

* Labels don't show when using the config_flow

## Future enhancements
Your support is welcomed.

* Support for multiple ICPs (haven't tried a login with multiple ICPs)
* Support for energy rates (currently need to be set-up manually and is static thereafter)

## Acknowledgements
This integration is not supported / endorsed by, nor affiliated with, Meridian Energy.
