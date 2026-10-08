import pytest
from weather import WeatherClient

@pytest.mark.slow
@pytest.mark.network
def test_open_meteo_live():
    client = WeatherClient(cache_dir='processed/test-weather-cache')
    forecast = client.get_7_day_forecast(lat=29.68, lon=76.99)
    assert len(forecast) > 0
    assert forecast[0].precipitation_sum >= 0
