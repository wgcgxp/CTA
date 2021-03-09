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
from vnpy.trader.constant import Interval, Offset, Direction, Exchange, Status
import numpy as np
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import time as time1
from datetime import datetime
import numpy as np
import pandas as pd
from vnpy.trader.constant import Status
import numpy as np
import talib


class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length = 3
    fixed_size = 10
    pricetick_multilplier1 = 1
    pricetick_multilplier2 = 2
    kdj_overbought_line = 80
    kdj_oversold_line = 20
    fastk_period = 9
    slowk_period = 5
    slowk_matype = 0
    slowd_period = 5
    slowd_matype = 0
    
    k1 = 0
    k2 = 0
    d1 = 0
    d2 = 0

    parameters = [
        "bar_window_length",
        "fixed_size",
        "pricetick_multilplier1",
        "pricetick_multilplier2",
        "kdj_overbought_line",
        "kdj_oversold_line",
        "fastk_period",
        "slowk_period",
        "slowk_matype",
        "slowd_period",
        "slowd_matype"
    ]

    variables = [
        "k1",
        "k2",
        "d1",
        "d2"
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

        self.cross_over = None
        self.cross_below = None

        self.vt_count: int = 0

        self.long_untraded = 0
        self.long_diff = 0
        self.long_diff_list = []

        self.short_untraded = 0
        self.short_diff = 0
        self.short_diff_list = []

        self.long_stop_orders = []
        self.short_stop_orders = []

        self.stoporder_count1 = 0
        self.stoporder_count2 = 0
        self.stoporder_count3 = 0
        self.stoporder_count4 = 0
        self.stoporder_count5 = 0
        self.stoporder_count6 = 0
        self.stoporder_count7 = 0
        self.stoporder_count8 = 0

        self.cancel_count1 = 0
        self.cancel_count2 = 0
        self.cancel_count3 = 0
        self.cancel_count4 = 0

        self.waiting_count = 0
        self.cancelled_count = 0
        self.triggered_count = 0

        self.bar = None

        self.ordercount = 0

        self.original = pd.DataFrame()

        self.k_weighted = []
        self.d_weighted = []
        self.j_weighted = []

        self.k_normal = []
        self.d_normal = []
        self.j_normal = []

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(1)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        self.write_log("策略停止")
        # print(f"self.ordercount:{self.ordercount}")
        # print(self.long_diff_list)
        # print(self.short_diff_list)

        # print(f"long_stop_orders:{self.long_stop_orders}\t长度{len(self.long_stop_orders)}")
        # print(f"short_stop_orders:{self.short_stop_orders}\t长度{len(self.short_stop_orders)}")

        # myset = set(self.short_stop_orders)
        # print(len(myset))
        # errorlist = []
        # for item in myset:
            # print(f"{item}出现了{self.short_stop_orders.count(item)}次")
            # if self.short_stop_orders.count(item) > 3:
            #     errorlist.append(str(item))
        # print(f"errorlist:{errorlist}")
           
        # print(f"在on_xmin_bar下的buy_stop_order:              {self.stoporder_count1}")
        # print(f"在on_xmin_bar下取消buy_stop_order的次数:       {self.cancel_count1}\n")
        # print(f"在on_xmin_bar下的short_stop_order:            {self.stoporder_count2}")
        # print(f"在on_xmin_bar下取消short_stop_order的次数:     {self.cancel_count2}\n")
        # print(f"在on_xmin_bar下的sell_stop_order:             {self.stoporder_count3}")
        # print(f"在on_xmin_bar下取消sell_stop_order的次数:      {self.cancel_count3}\n")
        # print(f"在on_xmin_bar下的cover_stop_order:            {self.stoporder_count4}")
        # print(f"在on_xmin_bar下取消cover_stop_order的次数:     {self.cancel_count4}\n")
        # print(f"在on_stop_order下的buy_stop_order:            {self.stoporder_count5}")
        # print(f"在on_stop_order下的short_stop_order:          {self.stoporder_count6}")
        # print(f"在on_stop_order下的sell_stop_order:           {self.stoporder_count7}")
        # print(f"在on_stop_order下的cover_stop_order:          {self.stoporder_count8}")

        # data = self.original

        # data["k_weighted"] = self.k_weighted[-100:]
        # data["d_weighted"] = self.d_weighted[-100:]
        # data["j_weighted"] = self.j_weighted[-100:]

        # data["k_normal"] = self.k_normal[-100:]
        # data["d_normal"] = self.d_normal[-100:]
        # data["j_normal"] = self.j_normal[-100:]

        # fig = plt.figure(figsize=(20, 8))
        # plt.subplot(2, 1, 1)
        # plt.plot(data["k_weighted"], color='r', label='k_weighted')
        # plt.plot(data["d_weighted"], color='b', label='d_weighted')
        # plt.plot(data["j_weighted"], color='y', label='j_weighted')
        # plt.subplot(2, 1, 2)
        # plt.plot(data["k_normal"], color='r', label='k_normal')
        # plt.plot(data["d_normal"], color='b', label='d_normal')
        # plt.plot(data["j_normal"], color='y', label='j_normal')
        # plt.legend()
        # plt.show()
        

        # print(f"self.waiting_count:{self.waiting_count}")
        # print(f"self.cancelled_count:{self.cancelled_count}")
        # print(f"self.triggered_count:{self.triggered_count}")

        # print(f"self.cta_engine.stop_orders:{self.cta_engine.stop_orders}\n\n长度为{len(self.cta_engine.stop_orders)}")
        # print(f"看多委托未成交次数为{self.long_untraded}")
        # print(f"stop_order.price - long_cross_price平均值：{np.mean(self.long_diff_list)}")
        # print(f"看空委托未成交次数为{self.short_untraded}")
        # print(f"short_cross_price - stop_order.price：{np.mean(self.short_diff_list)}")

        print("策略停止")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""

        self.bg.update_bar(bar)

        # print(f"active_stop_orders:{self.cta_engine.active_stop_orders}")
        active_stop_orders = self.cta_engine.active_stop_orders

        if active_stop_orders:    
            stop_orderid = list(active_stop_orders.keys())[0]
            stop_order = list(active_stop_orders.values())[0]

            if stop_order.direction == Direction.LONG and stop_order.offset == Offset.OPEN:
                self.cancel_order(stop_orderid)
                self.buy(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            elif stop_order.direction == Direction.SHORT and stop_order.offset == Offset.OPEN:
                self.cancel_order(stop_orderid)
                self.short(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            elif stop_order.direction == Direction.LONG and stop_order.offset == Offset.CLOSE:
                self.cancel_order(stop_orderid)
                self.sell(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

            elif stop_order.direction == Direction.SHORT and stop_order.offset == Offset.CLOSE:
                self.cancel_order(stop_orderid)
                self.cover(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

            # print(f"stop_ordersid:{stop_orderid}")
            # print(f"stop_orders:{stop_order}")
        
    def on_Xmin_bar(self, bar: BarData):
        """"""
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            # self.write_log(f"当前bar数量为：{str(self.am.count)}, 还差{str(self.am.size - self.am.count)}条")
            # print(f"当前bar数量为：{str(self.am.count)}, 还差{str(self.am.size - self.am.count)}条")
            return
        
        self.slowk, self.slowd, self.slowj = am.kdj(
            self.fastk_period,
            self.slowk_period,
            self.slowk_matype,
            self.slowd_period,
            self.slowd_matype,
            array=True
            )

        # self.k_normal.append(self.slowk[-1])
        # self.d_normal.append(self.slowd[-1])
        # self.j_normal.append(self.slowj[-1])

        # self.slowk, self.slowd, self.slowj = am.kdjs(
        #     9,
        #     array=True
        #     )
        
        self.k1 = self.slowk[-1]
        self.k2 = self.slowk[-2]
        self.d1 = self.slowd[-1]
        self.d2 = self.slowd[-2]

        self.cross_over = (self.k2 < self.d2 and self.k1 > self.d1)
        self.cross_below = (self.k2 > self.d2 and self.k1 < self.d1)
        
        if self.pos == 0:            
            self.buy_price = bar.close_price + self.pricetick * self.pricetick_multilplier1
            self.sell_price = 0
            self.short_price = bar.close_price - self.pricetick * self.pricetick_multilplier1
            self.cover_price = 0

        elif self.pos > 0:            
            self.buy_price = 0
            self.sell_price = bar.close_price - self.pricetick * self.pricetick_multilplier1
            self.short_price = 0
            self.cover_price = 0

        else:
            self.buy_price = 0
            self.sell_price = 0
            self.short_price = 0
            self.cover_price = bar.close_price + self.pricetick * self.pricetick_multilplier1

        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.cross_over:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    # self.stoporder_count1 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开多仓委托：{self.buy_vt_orderids}")
                    self.buy_price = 0               
            else:
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
                    # self.cancel_count1 += 1
                   
            if not self.short_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.cross_below:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    # self.stoporder_count2 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开空仓委托：{self.short_vt_orderids}")
                    self.short_price = 0       
            else:
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)
                    # self.cancel_count2 += 1

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.cross_below:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    # self.stoporder_count3 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平多仓委托：{self.sell_vt_orderids}")
                    self.sell_price = 0      
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
                    # self.cancel_count3 += 1
                    
        else:
            if not self.cover_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.cross_over:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    # self.stoporder_count4 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平空仓委托：{self.cover_vt_orderids}")
                    self.cover_price = 0                    
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)
                    # self.cancel_count4 += 1

        self.put_event()
                
    def on_stop_order(self, stop_order: StopOrder):
        """"""

        # if stop_order.status == StopOrderStatus.WAITING:
        #     self.waiting_count += 1
        # if stop_order.status == StopOrderStatus.CANCELLED:
        #     self.cancelled_count += 1
        # if stop_order.status == StopOrderStatus.TRIGGERED:
        #     print(f"triggered:{stop_order.offset}{stop_order.direction}")
        #     self.triggered_count += 1

        # 只处理撤销（CANCELLED）或者触发（TRIGGERED）的停止委托单 
        if stop_order.status == StopOrderStatus.WAITING:
            print(f"还在waiting状态的stop_order:{stop_order.stop_orderid}")
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

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # 发出新的委托
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.cross_over:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    # self.stoporder_count5 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开多仓委托：{self.buy_vt_orderids}")
                    self.buy_price = 0
                    
            if not self.short_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.cross_below:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    # self.stoporder_count6 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开空仓委托：{self.short_vt_orderids}")
                    self.short_price = 0
                    
        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.cross_below:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    # self.stoporder_count7 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平多仓委托：{self.sell_vt_orderids}")
                    self.sell_price = 0
                    
        else:
            if not self.cover_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.cross_over:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    # self.stoporder_count8 += 1
                    # self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平空仓委托：{self.cover_vt_orderids}")
                    self.cover_price = 0

    def on_order(self, order):
        """"""
        # if order.status == Status.CANCELLED:
        #     self.ordercount += 1


class NewArrayManager(ArrayManager):
    """"""
    def __init__(self, size=100):
        """"""
        super().__init__(size)

        # self.slowk = np.array([50.00, 50.00])
        # self.slowd = np.array([50.00, 50.00])
        # self.slowj = np.array([50.00, 50.00])

        # self.K: float = 50.00
        # self.D: float = 50.00
        # self.J: float = 50.00

        # self.H: float = 0
        # self.L: float = 0
        # self.C: float = 0
        # self.RSV: float = 0
        
    # def kdj_weighted(
    #     self,
    #     fastk_period, 
    #     array=False
    #     ):
    #     """"""
    #     high_array_kdj = self.high[-fastk_period:]
    #     low_array_kdj = self.low[-fastk_period:]
    #     close_array_kdj = self.close[-fastk_period:]

    #     volume_array_kdj = self.volume[-fastk_period:]
    #     total_volume = volume_array_kdj.sum()
    #     volume_array_kdj_wa = volume_array_kdj/total_volume

    #     high_array_kdj_wa = np.multiply(high_array_kdj, volume_array_kdj_wa)
    #     low_array_kdj_wa = np.multiply(low_array_kdj, volume_array_kdj_wa)
    #     close_array_kdj_wa = np.multiply(close_array_kdj, volume_array_kdj_wa)

    #     self.H = max(high_array_kdj_wa)
    #     self.L = min(low_array_kdj_wa)
    #     self.C = close_array_kdj_wa[-1]
    #     self.RSV = (self.C-self.L)*100/(self.H-self.L)

    #     # 无第1日K值，设为50
    #     self.K = self.K*2/3 + self.RSV*1/3
    #     self.D = self.D*2/3 + self.K*1/3
    #     self.J = 3 * self.K - 2 * self.D

    #     self.slowk[:-1] = self.slowk[1:]
    #     self.slowd[:-1] = self.slowd[1:]
    #     self.slowj[:-1] = self.slowj[1:]

    #     self.slowk[-1] = self.K
    #     self.slowd[-1] = self.D
    #     self.slowj[-1] = self.J

    #     if array:
    #         return self.slowk, self.slowd, self.slowj
    #     return self.slowk[-1], self.slowd[-1], self.slowj[-1]
        
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
        # and (bar.exchange in [Exchange.SHFE, Exchange.DCE, Exchange.CZCE])
        # print(f"bar.datetime.time:{bar.datetime.time()}")
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