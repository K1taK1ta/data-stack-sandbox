import requests
import time
from datetime import datetime, timedelta
from logger import log


class WordstatApiClient():

    URL_RG_INFO = "https://api.wordstat.yandex.net/v1/getRegionsTree"
    URL_TOP_REQUESTS = "https://api.wordstat.yandex.net/v1/topRequests"
    URL_DYNAMICS = "https://api.wordstat.yandex.net/v1/dynamics"
    URL_REGIONS = "https://api.wordstat.yandex.net/v1/regions"
    URL_USERS = "https://api.wordstat.yandex.net/v1/userInfo"

    def __init__(self, TOKEN_WORDSTAT):
        super().__init__()
        self.session = requests.Session()
        self.headers = {
            "Authorization": f"Bearer {TOKEN_WORDSTAT}",
            "Content-Type": "application/json; charset=utf-8"
            }
        self.session.headers.update(self.headers)
        self.log = log

    def _post_json(
        self, URL: str, payload: dict, max_retries: int = 2
            ) -> tuple[dict, int]:

        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.post(URL, json=payload)
                response.raise_for_status()
                break

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                retry = self._handle_429(
                    status, e.response.text, attempt, max_retries)

                if retry:
                    continue

                self._handle_503(status, e.response.text)
                raise

        else:
            raise RuntimeError("Max retries exceeded for Too Many Requests")

        resp_json = self._parse_response(response)
        return resp_json, response.status_code

    def _parse_response(self, response: requests.Response) -> dict:
        try:
            resp_json = response.json()
        except ValueError as e:
            self.log.critical(f"Response (truncated): {response.text[:200]}")
            raise ValueError(
                "Response is not valid JSON, aborting execution"
                ) from e

        return resp_json

    def _handle_503(self, status: int, e_text: str) -> None:
        if status == 503:
            self.log.warning(e_text)
            raise RuntimeError(
                "Possibly General API quota exceeded, aborting execution"
            )

    def _handle_429(
            self, status: int, e_text: str, attempt: int, max_retries: int
            ) -> bool | None:
        if status == 429:
            user_quota = self.get_user_quota()
            remaining = int(user_quota.get('userInfo', {}).get(
                'dailyLimitRemaining', 0))

            if remaining == 0:
                self.log.warning(e_text)
                raise RuntimeError(
                    "Possibly OAuth-APP: API quota exceeded, \
                        aborting execution"
                )
            else:
                self.log.warning(e_text)
                print(
                    f"429 Too Many Requests, sleep 1 sec, \
                          retry {attempt}/{max_retries}"
                    )
                time.sleep(1)
                return True

    def get_user_quota(self) -> dict:
        user_quota = self.session.post(self.URL_USERS, json=None)
        return user_quota.json()

    def fetch_top_requests(
        self,
        phrase: str,
        region: list[int],
        numPhrases: int = 1000,
    ) -> dict:
        payload = {
            "phrase": phrase,
            "numPhrases": numPhrases,
            "regions": region,
            "devices": ["all"]
        }
        resp_json, _ = self._post_json(self.URL_TOP_REQUESTS, payload)
        return resp_json

    def _validate_dates(self, fromDate: str, toDate: str, period: str) -> None:
        fromDate_dt = datetime.strptime(fromDate, "%Y-%m-%d").date()
        toDate_dt = datetime.strptime(toDate, "%Y-%m-%d").date()
        today_date = datetime.today().date()

        current_week_monday = today_date - timedelta(days=today_date.weekday())
        two_weeks_ago_sunday = current_week_monday - timedelta(days=8)

        none_data = (
            today_date,
            today_date - timedelta(days=1),
            today_date - timedelta(days=2)
        )

        if fromDate_dt in none_data and toDate_dt in none_data:
            raise ValueError("No data available for the selected period")
        elif toDate_dt in none_data:
            self.log.warning(
                "Data for the selected period may be incomplete or unavailable"
                )

        if period == 'weekly':
            if fromDate_dt.weekday() != 0:
                raise ValueError(
                    "For weekly period, fromDate must be a Monday")
            elif toDate_dt.weekday() != 6:
                raise ValueError("For weekly period, toDate must be a Sunday")
            elif toDate_dt > two_weeks_ago_sunday:
                self.log.warning(
                    "Data for the selected period may be \
                        incomplete or unavailable")

    def fetch_dynamics(
        self,
        phrase: str,
        region: list[int],
        fromDate: str,
        toDate: str,
        period: str
    ) -> dict:
        payload = {
            "phrase": phrase,
            "period": period,
            "fromDate": fromDate,
            "toDate": toDate,
            "regions": region,
            "devices": ["all"]
        }

        self._validate_dates(fromDate=fromDate, toDate=toDate, period=period)
        resp_json, _ = self._post_json(self.URL_DYNAMICS, payload)
        return resp_json

    def get_region_id(self, city_name: str) -> int:
        if not city_name:
            return 1

        city_clean = city_name.lower().strip()
        return REGIONS_DICT.get(city_clean, 1)

REGIONS_DICT = {
# Москва и область
"москва": 1,
"москва и мо": 1,
"мо": 1,
"московская область": 1,
# Города-миллионники и крупные центры
"санкт-петербург": 2,
"спб": 2,
"питер": 2,
"ленинград": 2,
"краснодар": 35,
"екатеринбург": 54,
"екб": 54,
"новосибирск": 65,
"нск": 65,
"самара": 51,
"казань": 43,
"челябинск": 56,
"ростов-на-дону": 39,
"ростов": 39,
"омск": 66,
"воронеж": 193,
"уфа": 172,
"нижний новгород": 47,
"нн": 47,
"красноярск": 62,
"волгоград": 38,
"пермь": 50,
"ульяновск": 195,
"великий новгород": 24,
"псков": 25,
"вологда": 21,
"иркутск": 63,
"владивосток": 75,
"хабаровск": 76,
"калининград": 22
}
