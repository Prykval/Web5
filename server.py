import asyncio
import logging

import httpx
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
import aiohttp

import sys
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)


async def request(url: str) -> dict | str:
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            result = r.json()
            return result
        else:
            return "Не вийшло. Приват не відповідає :)"


#async def get_exchange():
    response = await request(f'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5')
    # переробить на більш придатний результат
    return str(response)

async def get_exchange(days: int, additional_currencies: list = None):
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


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                exchange = await get_exchange()
                await self.send_to_clients(exchange)
            elif message == 'Hello server':
                await self.send_to_clients("Привіт мої карапузи!")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    additional_currencies = sys.argv[2:] if len(sys.argv) > 2 else None
    asyncio.run(get_exchange(days, additional_currencies))
    asyncio.run(main())
