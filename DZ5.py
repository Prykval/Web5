import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta

async def fetch_currency_rates(days: int, additional_currencies: list = None):
    if days > 10:
        print("Можна запитувати курс валют максимум за останні 10 днів.")
        return

    if additional_currencies is None:
        additional_currencies = []

    currencies = ['USD', 'EUR'] + additional_currencies
    base_url = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    async with aiohttp.ClientSession() as session:
        for day in range(days):
            date = (datetime.now() - timedelta(days=day)).strftime('%d.%m.%Y')
            url = base_url + date

            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Курси валют за {date}:")
                        for currency in currencies:
                            rates = [rate for rate in data['exchangeRate'] if rate.get('currency') == currency]
                            if rates:
                                rate = rates[0]
                                print(f"{currency}: купівля - {rate.get('purchaseRate', 'недоступно')}, продаж - {rate.get('saleRate', 'недоступно')}")
                            else:
                                print(f"{currency}: інформація недоступна")
                    else:
                        print(f"Не вдалося отримати дані за {date}")
            except aiohttp.ClientError as e:
                print(f"Помилка при запиті до API: {e}")

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    additional_currencies = sys.argv[2:] if len(sys.argv) > 2 else None
    asyncio.run(fetch_currency_rates(days, additional_currencies))