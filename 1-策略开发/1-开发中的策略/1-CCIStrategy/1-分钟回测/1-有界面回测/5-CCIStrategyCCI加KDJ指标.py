from typing import Any, Callable
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TradeData,
    StopOrder,
    OrderData
)
from vnpy.app.cta_strategy.base import EngineType, StopOrderStatus
from vnpy.trader.object import (BarData, TickData)
from vnpy.trader.constant import Interval, Offset, Direction
import numpy as np
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import datetime
import numpy as np
import pandas as pd
from vnpy.trader.constant import Status
import numpy as np
import talib


class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length = 20
    cci_window = 3
    fixed_size = 1
    sell_multiplier = 0.96
    cover_multiplier = 1.01
    pricetick_multilplier = 2
    
    cci1 = 0
    cci2 = 0
    
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = [
        "bar_window_length",
        "cci_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier",
        "pricetick_multilplier"
    ]

    variables = [
        "cci1",
        "cci2",
        "cci_intra_trade"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = XminBarGenerator(self.on_bar, self.bar_window_length, self.on_Xmin_bar)
        self.am = NewArrayManager()

        self.pricetick = self.get_pricetick()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

        self.cross_over_100 = None
        self.cross_below_100 = None
        self.cross_over_min100 = None
        self.cross_below_min100 = None

        self.long_entry = 0
        self.short_entry = 0

        self.fastk_period = 9
        self.slowk_period = 3
        self.slowk_matype = 0
        self.slowd_period = 3
        self.slowd_matype = 0

        self.slowk = []
        self.slowd = []
        self.slowj = []

        self.bar = None

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(10)

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
        self.bg.update_bar(bar)
    
    def on_Xmin_bar(self, bar: BarData):
        """"""        
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            self.write_log(f"当前bar数量为：{str(self.am.count)}, 还差{str(self.am.size - self.am.count)}条")
            return
        
        cci = am.cci(self.cci_window, True)
        self.cci1 = cci[-1]
        self.cci2 = cci[-2]

        self.cross_over_100 = (self.cci2 <= 100 and self.cci1 >= 100)
        self.cross_below_100 = (self.cci2 >= 100 and self.cci1 <= 100)
        self.cross_over_min100 = (self.cci2 <= -100 and self.cci1 >= -100)
        self.cross_below_min100 = (self.cci2 >= -100 and self.cci1 <= -100)

        self.slowk, self.slowd, self.slowj = am.kdj(
            am.high, 
            am.low, 
            am.close, 
            self.fastk_period,
            self.slowk_period,
            self.slowk_matype,
            self.slowd_period,
            self.slowd_matype,
            array=True
            )

        self.bar = bar

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price           
            
            self.buy_price = bar.close_price + self.pricetick * self.pricetick_multilplier
            self.sell_price = 0
            self.short_price = bar.close_price - self.pricetick * self.pricetick_multilplier
            self.cover_price = 0

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            
            self.buy_price = 0
            self.sell_price = self.short_entry
            self.short_price = 0
            self.cover_price = 0

        else:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            self.buy_price = 0
            self.sell_price = 0
            self.short_price = 0
            self.cover_price = self.long_entry
        
        
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.cross_over_100 or self.cross_over_min100:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0
                else:
                    for vt_orderid in self.buy_vt_orderids:
                        self.cancel_order(vt_orderid)

            if not self.short_vt_orderids:
                if self.cross_below_100 or self.cross_below_min100:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0
                else:
                    for vt_orderid in self.short_vt_orderids:
                        self.cancel_order(vt_orderid)

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.bar.close_price < self.intra_trade_high * self.sell_multiplier:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)

        else:
            if not self.cover_vt_orderids:
                if self.bar.close_price > self.intra_trade_low * self.cover_multiplier:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)

        self.put_event()
                

    def on_stop_order(self, stop_order: StopOrder):
        """"""
        # 只处理撤销（CANCELLED）或者触发（TRIGGERED）的停止委托单
        if stop_order.status == StopOrderStatus.WAITING:
            return

        # 移除已经结束的停止单委托号
        for buf_orderids in [
            self.buy_vt_orderids,
            self.sell_vt_orderids,
            self.short_vt_orderids,
            self.cover_vt_orderids
        ]:
            if stop_order.stop_orderid in buf_orderids:
                buf_orderids.remove(stop_order.stop_orderid)

        # 发出新的委托
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.cross_over_100 or self.cross_over_min100:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0

            if not self.short_vt_orderids:
                if self.cross_below_100 or self.cross_below_min100:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.bar.close_price < self.intra_trade_high * self.sell_multiplier:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0
        
        else:
            if not self.cover_vt_orderids:
                if self.bar.close_price > self.intra_trade_low * self.cover_multiplier:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0

    # def on_trade(self, trade: TradeData):
    #     print(trade.direction)
    #     print(trade.offset)


class NewArrayManager(ArrayManager):
    """"""
    def __init__(self, size=100):
        """"""
        super().__init__(size)

    def kdj(
        self, 
        fastk_period, 
        slowk_period, 
        slowk_matype, 
        slowd_period,
        slowd_matype, 
        array=False
        ):
        """"""
        slowk, slowd, = talib.STOCH(self.high, self.low, self.close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
        # 求出J值，J = (3 * D) - (2 * K)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowk[-1], slow[-1], slow[-1]

    def kdjs(self, n, array=False):
        """"""
        slowk, slowd = talib.STOCH(self.high, self.low, self.close, n, 3, 0, 3, 0)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowd[-1], slow[-1], slow[-1]


class XminBarGenerator(BarGenerator):
    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        super().__init__(on_bar, window, on_window_bar, interval)
    
    def update_bar(self, bar: BarData) ->None:
        """
        Update 1 minute bar into generator
        """
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest

        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            # if not (bar.datetime.minute + 1) % self.window:
            #     finished = True
            self.interval_count += 1

            if not self.interval_count % self.window:
                finished = True
                self.interval_count = 0
        elif self.interval == Interval.HOUR:
            if self.last_bar:
                new_hour = bar.datetime.hour != self.last_bar.datetime.hour
                last_minute = bar.datetime.minute == 59
                not_first = self.window_bar.datetime != bar.datetime

                # To filter duplicate hour bar finished condition
                if (new_hour or last_minute) and not_first:
                    # 1-hour bar
                    if self.window == 1:
                        finished = True
                    # x-hour bar
                    else:
                        self.interval_count += 1

                        if not self.interval_count % self.window:
                            finished = True
                            self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar