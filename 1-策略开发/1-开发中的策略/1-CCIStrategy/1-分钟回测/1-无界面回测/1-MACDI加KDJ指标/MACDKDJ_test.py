#%%
from typing import Any, Callable
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TradeData,
    StopOrder,
    OrderData
)
from vnpy.app.cta_strategy.base import StopOrderStatus, BacktestingMode
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.trader.object import BarData, TickData
from vnpy.trader.constant import Interval, Offset, Direction, Exchange, Status
import numpy as np
import pandas as pd
from datetime import time as time1
from datetime import datetime
import time
import talib

from vnpy.trader.ui import create_qapp, QtCore
from vnpy.chart import ChartWidget, VolumeItem, CandleItem

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()

#%%
class KdjMacdStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length = 10
    fixed_size = 10
    pricetick_multilplier1 = 1
    pricetick_multilplier2 = 0
    kdj_overbought_line = 80
    kdj_oversold_line = 20
    kdj_fastk_period = 9
    kdj_slowk_period = 5
    kdj_slowk_matype = 0
    kdj_slowd_period = 5
    kdj_slowd_matype = 0
    macd_fastk_period = 7
    macd_slowk_period = 27
    macd_signal_period = 5

    k1 = 0
    k2 = 0
    d1 = 0
    d2 = 0

    macd = 0 
    signal = 0 
    hist = 0

    parameters = [
        "bar_window_length",
        "fixed_size",
        "pricetick_multilplier1",
        "pricetick_multilplier2",
        "kdj_overbought_line",
        "kdj_oversold_line",
        "kdj_fastk_period",
        "kdj_slowk_period",
        "kdj_slowk_matype",
        "kdj_slowd_period",
        "kdj_slowd_matype",
        "macd_fastk_period",
        "macd_slowk_period",
        "macd_signal_period"
    ]

    variables = [
        "k1",
        "k2",
        "d1",
        "d2",
        "macd",
        "signal",
        "hist"
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

        self.kdj_cross_over = False
        self.kdj_cross_below = False

        self.macd_cross_over = False
        self.macd_cross_below = False

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
        print("策略停止")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.bg.update_bar(bar)

    def on_Xmin_bar(self, bar: BarData):
        """"""
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return

        self.macd, self.signal, self.hist = am.macd(self.macd_fastk_period, self.macd_signal_period, self.macd_slowk_period, True)



        # self.macd_cross_over = (self.hist[-2] < 0 and self.hist[-1] > 0)
        # self.macd_cross_below = (self.hist[-2] > 0 and self.hist[-1] < 0)
        
        # self.slowk, self.slowd, self.slowj = am.kdj(
        #     self.kdj_fastk_period,
        #     self.kdj_slowk_period,
        #     self.kdj_slowk_matype,
        #     self.kdj_slowd_period,
        #     self.kdj_slowd_matype,
        #     array=True
        #     )
        
        # self.k1 = self.slowk[-1]
        # self.k2 = self.slowk[-2]
        # self.d1 = self.slowd[-1]
        # self.d2 = self.slowd[-2]
                
    def on_stop_order(self, stop_order: StopOrder):
        """"""

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """

    def on_order(self, order):
        """"""


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
        return slowk[-1], slowd[-1], slowj[-1]

    def kdjs(self, n, array=False):
        """"""
        slowk, slowd = talib.STOCH(self.high, self.low, self.close, n, 3, 0, 3, 0)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowk[-1], slowd[-1], slowj[-1]

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

            elif bar.datetime.time() in [time1(10, 14), time1(11, 29), time1(14, 59), time1(22, 59)]:
                if bar.exchange in [Exchange.SHFE, Exchange.DCE, Exchange.CZCE]:
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
  
#%%
start1 = time.time()
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2020, 3, 9),
    end=datetime(2021, 3, 8),
    rate=0.0001,
    slippage=2.0,
    size=10,
    pricetick=1.0,
    capital=1_000_000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(KdjMacdStrategy, {})
#%%
start2 = time.time()
engine.load_data()
end2 = time.time()
print(f"加载数据所需时长: {(end2-start2)} Seconds")
#%%
engine.run_backtesting()
#%%
engine.calculate_result()
engine.calculate_statistics()
# 待测试的代码
end1 = time.time()
print(f"单次回测运行时长: {(end1-start1)} Seconds")
engine.show_chart()
#%%
# setting = OptimizationSetting()
# setting.set_target("end_balance")
# setting.add_parameter("bar_window_length", 1, 15, 1)
# setting.add_parameter("pricetick_multilplier1", 1, 10, 1)
# setting.add_parameter("macd_fastk_period", 4, 20, 2)
# setting.add_parameter("macd_slowk_period", 21, 30, 1)
# setting.add_parameter("macd_signal_period", 4, 12, 2)
#%%
# engine.run_optimization(setting, output=True)
# %%
