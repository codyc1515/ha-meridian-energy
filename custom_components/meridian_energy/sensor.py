"""Meridian Energy sensors"""
from datetime import datetime, timedelta

import csv
from io import StringIO
from pytz import timezone
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.const import ENERGY_KILO_WATT_HOUR, CURRENCY_DOLLAR
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    clear_statistics,
    #day_start_end,
    get_last_statistics,
    list_statistic_ids,
    #month_start_end,
    statistics_during_period,
)
import homeassistant.util.dt as dt_util
import math

from .api import MeridianEnergyApi

from .const import (
    DOMAIN,
    SENSOR_NAME
)

NAME = DOMAIN
ISSUEURL = "https://github.com/codyc1515/ha-meridian-energy/issues"

STARTUP = f"""
-------------------------------------------------------------------
{NAME}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUEURL}
-------------------------------------------------------------------
"""

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})

SCAN_INTERVAL = timedelta(hours=3)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None
):
    email = entry.data.get(CONF_EMAIL)
    password = entry.data.get(CONF_PASSWORD)
        
    api = MeridianEnergyApi(email, password)

    _LOGGER.debug('Setting up sensor(s)...')

    sensors = []
    sensors.append(MeridianEnergyUsageSensor(SENSOR_NAME, api))
    async_add_entities(sensors, True)

class MeridianEnergyUsageSensor(SensorEntity):
    def __init__(self, name, api):
        self._name = name
        self._icon = "mdi:meter-electric"
        self._state = 0
        #self._unit_of_measurement = 'kWh'
        self._unique_id = DOMAIN
        #self._device_class = "energy"
        #self._state_class = "total"
        self._state_attributes = {}
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement
    
    @property
    def state_class(self):
        """Return the state class."""
        return self._state_class
    
    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class
        
    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    def update(self):
        _LOGGER.debug('Beginning usage update')

        solarStatistics = []
        solarRunningSum = 0

        dayStatistics = []
        dayRunningSum = 0

        nightStatistics = []
        nightRunningSum = 0

        # Login to the website
        self._api.token()

        # Get the latest usage data
        response = self._api.get_data()

        # Process the CSV consumption file
        csv_file = csv.reader(StringIO(response))

        for row in csv_file:
            # Accessing columns by index in each row
            if len(row) >= 2:  # Checking if there are at least two columns
                if row[0] == 'HDR':
                    _LOGGER.debug('HDR line arrived')
                    continue
                elif row[0] == 'DET':
                    _LOGGER.debug('DET line arrived')
                
                # Row definitions from EIEP document 13A (https://www.ea.govt.nz/documents/182/EIEP_13A_Electricity_conveyed_information_for_consumers.pdf)
                record_type = row[0]
                consumer_authorisation_code = row[1]
                icp_identifier = row[2]
                response_code = row[3]
                nzdt_adjustment = row[4]
                metering_component_serial_number = row[5]
                energy_flow_direction = row[6]
                register_content_code = row[7]
                period_of_availability = row[8]
                # refer below for date logic of row[9]
                read_period_end_date_time = row[10]
                read_status = row[11]
                unit_quantity_active_energy_volume = row[12]
                unit_quantity_reactive_energy_volume = row[13]
                
                # Assuming row[9] contains the date in the format 'dd/mm/YYYY HH:MM:SS'
                read_period_start_date_time = row[9]

                # Assuming tz is your timezone (e.g., pytz.timezone('Your/Timezone'))
                tz = timezone('Pacific/Auckland')

                # Parse the date string into a datetime object
                start_date = datetime.strptime(read_period_start_date_time, '%d/%m/%Y %H:%M:%S')

                # Localize the datetime object
                start_date = tz.localize(start_date)
                
                # Exclude any readings that are at the 59th minute
                if start_date.minute == 59:
                    continue

                # Round down to the nearest hour as HA can only handle hourly
                rounded_date = start_date.replace(minute=0, second=0, microsecond=0)
                
                # Skip any estimated reads
                if read_status != "RD":
                    _LOGGER.debug('HDR line skipped as its estimated')
                    continue
                
                # Process solar export channels
                if energy_flow_direction == 'I':
                    solarRunningSum = solarRunningSum + float(unit_quantity_active_energy_volume)
                    solarStatistics.append(StatisticData(
                        start=rounded_date,
                        sum=solarRunningSum
                    ))
                
                # Process regular channels
                else:
                    # Night rate channel
                    if rounded_date.time() >= datetime.strptime("21:00", "%H:%M").time() or rounded_date.time() < datetime.strptime("07:00", "%H:%M").time():
                        nightRunningSum = nightRunningSum + float(unit_quantity_active_energy_volume)
                        nightStatistics.append(StatisticData(
                            start=rounded_date,
                            sum=nightRunningSum
                        ))
                    
                    # Day rate channel
                    else:
                        dayRunningSum = dayRunningSum + float(unit_quantity_active_energy_volume)
                        dayStatistics.append(StatisticData(
                            start=rounded_date,
                            sum=dayRunningSum
                        ))
            else:
                _LOGGER.warning("Not enough columns in this row")

        solarMetadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=f"{SENSOR_NAME} (Solar Export)",
            source=DOMAIN,
            statistic_id=f"{DOMAIN}:return_to_grid",
            unit_of_measurement=ENERGY_KILO_WATT_HOUR
        )
        async_add_external_statistics(self.hass, solarMetadata, solarStatistics)

        dayMetadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=f"{SENSOR_NAME} (Day)",
            source=DOMAIN,
            statistic_id=f"{DOMAIN}:consumption_day",
            unit_of_measurement=ENERGY_KILO_WATT_HOUR
        )
        async_add_external_statistics(self.hass, dayMetadata, dayStatistics)

        nightMetadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=f"{SENSOR_NAME} (Night)",
            source=DOMAIN,
            statistic_id=f"{DOMAIN}:consumption_night",
            unit_of_measurement=ENERGY_KILO_WATT_HOUR
        )
        async_add_external_statistics(self.hass, nightMetadata, nightStatistics)