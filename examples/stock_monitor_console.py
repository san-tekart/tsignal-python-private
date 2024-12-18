# examples/06_stock_monitor_console.py

"""
Stock monitor console example.
"""

import asyncio
from typing import Dict
import logging
from utils import logger_setup
from stock_core import StockPrice, StockService, StockProcessor, StockViewModel
from tsignal import t_with_signals, t_slot

logger_setup("tsignal", level=logging.NOTSET)
logger_setup("stock_core", level=logging.NOTSET)
logger = logger_setup(__name__, level=logging.NOTSET)


@t_with_signals
class StockMonitorCLI:
    """Stock monitoring CLI interface"""

    def __init__(
        self,
        service: StockService,
        processor: StockProcessor,
        view_model: StockViewModel,
    ):
        logger.debug("[StockMonitorCLI][__init__] started")
        self.service = service
        self.processor = processor
        self.view_model = view_model
        self.current_input = ""
        self.running = True
        self.showing_prices = False

    def print_menu(self):
        """Print the menu"""

        print("\n===== MENU =====")
        print("stocks            - List available stocks and prices")
        print("alert <code> <l> <u> - Set price alert")
        print("remove <code>     - Remove price alert")
        print("list              - List alert settings")
        print("showprices        - Start showing price updates (press Enter to stop)")
        print("quit              - Exit")
        print("================\n")

    async def get_line_input(self, prompt="Command> "):
        """Get line input"""

        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: input(prompt)
        )

    @t_slot
    def on_prices_updated(self, prices: Dict[str, StockPrice]):
        """Process price updates"""

        # If we are in showprices mode, display current prices:
        if self.showing_prices:
            print("Showing price updates (Press Enter to return to menu):")
            print("\nCurrent Prices:")

            for code, data in sorted(self.view_model.current_prices.items()):
                print(f"{code} ${data.price:.2f} ({data.change:+.2f}%)")

            print("\n(Press Enter to return to menu)")

            alerts = []
            for code, data in prices.items():
                if code in self.view_model.alert_settings:
                    lower, upper = self.view_model.alert_settings[code]
                    if lower and data.price <= lower:
                        alerts.append(
                            f"{code} price (${data.price:.2f}) below ${lower:.2f}"
                        )
                    if upper and data.price >= upper:
                        alerts.append(
                            f"{code} price (${data.price:.2f}) above ${upper:.2f}"
                        )

            if alerts:
                print("\nAlerts:")
                for alert in alerts:
                    print(alert)

    async def process_command(self, command: str):
        """Process command"""
        parts = command.strip().split()

        if not parts:
            return

        if parts[0] == "stocks":
            print("\nAvailable Stocks:")
            print(f"{'Code':<6} {'Price':>10} {'Change':>8}  {'Company Name':<30}")
            print("-" * 60)

            desc = self.service.descriptions

            for code in desc:
                if code in self.view_model.current_prices:
                    price_data = self.view_model.current_prices[code]
                    print(
                        f"{code:<6} ${price_data.price:>9.2f} {price_data.change:>+7.2f}%  {desc[code]:<30}"
                    )

        elif parts[0] == "alert" and len(parts) == 4:
            try:
                code = parts[1].upper()
                lower = float(parts[2])
                upper = float(parts[3])

                if code not in self.view_model.current_prices:
                    print(f"Unknown stock code: {code}")
                    return

                self.view_model.set_alert.emit(code, lower, upper)
                print(f"Alert set for {code}: lower={lower} upper={upper}")
            except ValueError:
                print("Invalid price values")

        elif parts[0] == "remove" and len(parts) == 2:
            code = parts[1].upper()
            if code in self.view_model.alert_settings:
                self.view_model.remove_alert.emit(code)
                print(f"Alert removed for {code}")

        elif parts[0] == "showprices":
            self.showing_prices = True
            print("Now showing price updates. Press Enter to return to menu.")

        elif parts[0] == "quit":
            self.running = False
            print("Exiting...")

        else:
            print(f"Unknown command: {command}")

    async def run(self):
        """CLI execution"""
        logger.debug(
            "[StockMonitorCLI][run] started current loop: %s %s",
            id(asyncio.get_running_loop()),
            asyncio.get_running_loop(),
        )

        # Future for receiving started signal
        main_loop = asyncio.get_running_loop()
        processor_started = asyncio.Future()

        # Connect service.start to processor's started signal
        def on_processor_started():
            logger.debug("[StockMonitorCLI][run] processor started, starting service")
            self.service.start()

            # Set processor_started future to True in the main loop
            def set_processor_started_true():
                logger.debug(
                    "[StockMonitorCLI][run] set_processor_started_true current loop: %s %s",
                    id(asyncio.get_running_loop()),
                    asyncio.get_running_loop(),
                )
                processor_started.set_result(True)

            main_loop.call_soon_threadsafe(set_processor_started_true)

        self.service.price_updated.connect(
            self.processor, self.processor.on_price_updated
        )
        self.processor.price_processed.connect(
            self.view_model, self.view_model.on_price_processed
        )
        self.view_model.prices_updated.connect(self, self.on_prices_updated)

        self.processor.alert_triggered.connect(
            self.view_model, self.view_model.on_alert_triggered
        )
        self.processor.alert_settings_changed.connect(
            self.view_model, self.view_model.on_alert_settings_changed
        )

        self.processor.started.connect(on_processor_started)
        self.processor.start()

        # Wait until processor is started and service is started
        await processor_started

        while self.running:
            if not self.showing_prices:
                self.print_menu()
                command = await self.get_line_input()
                await self.process_command(command)
            else:
                await self.get_line_input("")
                self.showing_prices = False

        self.service.stop()
        self.processor.stop()


async def main():
    """Main function"""
    service = StockService()
    view_model = StockViewModel()
    processor = StockProcessor()

    cli = StockMonitorCLI(service, processor, view_model)

    await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass