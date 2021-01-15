#%%
from datetime import time
from typing import Any
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager
)
from vnpy.trader.object import (BarData, TickData)
#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"
    # 定义类的参数，只能是int、float、str、bool这4种数据类型
    cci_window = 5
    fixed_size = 1
    sell_multiplier = 0.96
    cover_multiplier = 1.02

    # 定义类的变量，只能是int、float、str、bool这4种数据类型
    cci1 = 0.0
    cci2 = 0.0
    cci3 = 0.0

    intra_trade_high = 0.0
    intra_trade_low = 0.0
    long_entry = 0.0
    short_entry = 0.0

    parameters = [
        "cci_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier"
    ]
    variables = [
        "cci1",
        "cci2",
        "cci3",
        "intra_trade_high",
        "intra_trade_low",
        "long_entry",
        "short_entry"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_init(self):
        """日志输出：策略初始化"""
        self.write_log("策略初始化")
        # 加载10天的历史数据用于初始化回放
        self.load_bar(10)

    def on_start(self):
        """
        当策略被启动时候调用该函数
        """
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """tick回调函数"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """K线更新"""
        self.cancel_all()
        
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算CCI指标
        cci = am.cci(self.cci_window, array=True)
        self.cci1 = cci[-1]
        self.cci2 = cci[-2]
        self.cci3 = cci[-3]

        # 最低点判断条件，即生成买多开仓信号
        over_sold = (self.cci1 <= -100)
        low_turning_cond1 = (self.cci1 > self.cci2)
        low_turning_cond2 = (self.cci3 > self.cci2)

        # 最高点判断条件，即生成卖空开仓信号
        over_bought = (self.cci1 >= 100)
        high_turning_cond1 = (self.cci1 < self.cci2)
        high_turning_cond2 = (self.cci3 < self.cci2)

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            # 执行买多开仓
            if over_sold & low_turning_cond1 & low_turning_cond2:
                self.buy(bar.close_price, self.fixed_size, True)

            # 执行卖空开仓
            elif over_bought & high_turning_cond1 & high_turning_cond2:
                self.short(bar.close_price, self.fixed_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.short_entry = self.intra_trade_high * self.sell_multiplier

            self.sell(self.short_entry, abs(self.pos), True)

        else:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            self.long_entry = self.intra_trade_low * self.cover_multiplier

            self.cover(self.long_entry, abs(self.pos), True)

        # 更新图形界面
        self.put_event()