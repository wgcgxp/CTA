from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    Direction,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class TurtleSignalStrategyHNTest(CtaTemplate):
    """"""
    author = "Huang Ning"

    entry_window = 20
    exit_window = 10
    atr_window = 20
    fixed_size = 1

    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0

    parameters = [
        "entry_window", 
        "exit_window", 
        "atr_window", 
        "fixed_size"
    ]

    variables = [
        "entry_up", 
        "entry_down", 
        "exit_up", 
        "exit_down", 
        "atr_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(20)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # Only calculates new entry channel when no position holding
        if not self.pos:
            self.entry_up, self.entry_down = self.am.donchian(
                self.entry_window
            )

        self.exit_up, self.exit_down = self.am.donchian(self.exit_window)

        if not self.pos:
            self.atr_value = self.am.atr(self.atr_window)

            self.long_entry = 0
            self.short_entry = 0
            self.long_stop = 0
            self.short_stop = 0

            self.send_buy_orders(self.entry_up)
            self.send_short_orders(self.entry_down)
        elif self.pos > 0:
            self.send_buy_orders(self.entry_up)

            sell_price = max(self.long_stop, self.exit_down)
            self.sell(sell_price, abs(self.pos), True)

        elif self.pos < 0:
            self.send_short_orders(self.entry_down)

            cover_price = min(self.short_stop, self.exit_up)
            self.cover(cover_price, abs(self.pos), True)

        self.put_event()

    def on_trade(self, trade: TradeData):
        """"""
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price
            self.long_stop = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + 2 * self.atr_value

    def on_order(self, order: OrderData):
        """"""


    def on_stop_order(self, stop_order: StopOrder):
        """"""


    def send_buy_orders(self, price):
        """"""
        t = self.pos / self.fixed_size

        if t < 1:
            self.buy(price, self.fixed_size, True)

        if t < 2:
            self.buy(price + self.atr_value * 0.5, self.fixed_size, True)

        if t < 3:
            self.buy(price + self.atr_value, self.fixed_size, True)

        if t < 4:
            self.buy(price + self.atr_value * 1.5, self.fixed_size, True)

    def send_short_orders(self, price):
        """"""
        t = self.pos / self.fixed_size

        if t > -1:
            self.short(price, self.fixed_size, True)

        if t > -2:
            self.short(price - self.atr_value * 0.5, self.fixed_size, True)

        if t > -3:
            self.short(price - self.atr_value, self.fixed_size, True)

        if t > -4:
            self.short(price - self.atr_value * 1.5, self.fixed_size, True)
