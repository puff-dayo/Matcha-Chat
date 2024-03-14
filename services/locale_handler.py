import datetime
import locale

import pycountry
from workalendar.registry import registry


def get_iso_country_code():
    loc = locale.getdefaultlocale()[0]

    country_code = loc.split('_')[1]

    country = pycountry.countries.get(alpha_2=country_code)
    if country:
        return country.alpha_2
    else:
        return 'US'


def get_formatted_date_and_holiday(country_code):
    today = datetime.date.today()

    formatted_date = today.strftime("%Y-%m-%d %A")

    year = today.year

    CalendarClass = registry.get(country_code)
    calendar = CalendarClass()

    holidays = calendar.holidays(year)

    nearest_holiday = ""
    for _holiday in holidays:
        if 0 <= (_holiday[0] - today).days <= 3:
            nearest_holiday = _holiday
            break

    return formatted_date, nearest_holiday


if __name__ == "__main__":
    iso_code = get_iso_country_code()
    date, holiday = get_formatted_date_and_holiday(iso_code)
    print(f"Date: {date}, Location: {iso_code}, Holiday: {holiday}")
