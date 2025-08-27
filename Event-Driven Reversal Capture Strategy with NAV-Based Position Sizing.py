

from AlgoAPI import AlgoAPIUtil, AlgoAPI_Backtest
from datetime import datetime
import uuid

class AlgoEvent:
    def __init__(self):
        self.today_open = {}
        self.today_close = {}
        self.prev_open = {}
        self.prev_close = {}
        self.prev_nav = {}
        self.last_eod_day = None
        self.has_open_position = {}
        self.has_pending_order = {}
        self.current_prices = {}
        self.total_commitment = 0.0
        self.first_tick_processed = {}  # NEW: track first tick per day

    def start(self, mEvt):
        self.evt = AlgoAPI_Backtest.AlgoEvtHandler(self, mEvt)
        self.myinstrument = mEvt['subscribeList']
        for instrument in self.myinstrument:
            self.today_open[instrument] = None
            self.today_close[instrument] = None
            self.prev_open[instrument] = None
            self.prev_close[instrument] = None
            self.prev_nav[instrument] = 0
            self.has_open_position[instrument] = False
            self.has_pending_order[instrument] = False
            self.current_prices[instrument] = 0.0
            self.first_tick_processed[instrument] = False  # Initialize
        self.evt.start()

    def _simulate_end_of_day(self):
        for instrument in self.myinstrument:
            if self.today_open[instrument] is not None and self.today_close[instrument] is not None:
                self.prev_open[instrument] = self.today_open[instrument]
                self.prev_close[instrument] = self.today_close[instrument]
            self.today_open[instrument] = None
            self.today_close[instrument] = None

    def on_openPositionfeed(self, op, oo, uo):
        for instrument in self.myinstrument:
            self.has_open_position[instrument] = False
            self.has_pending_order[instrument] = False
        self.total_commitment = 0.0

        for tradeID, record in oo.items():
            instrument = record.get('instrument')
            volume = record.get('Volume', 0)
            if instrument in self.myinstrument:
                self.has_open_position[instrument] = True
                price = self.current_prices.get(instrument, 0)
                self.total_commitment += price * volume

        for tradeID, record in uo.items():
            instrument = record.get('instrument')
            if instrument in self.myinstrument:
                self.has_pending_order[instrument] = True

    def on_orderfeed(self, of): 
        pass
    def on_newsdatafeed(self, nd): 
        pass
    def on_weatherdatafeed(self, wd): 
        pass
    def on_econsdatafeed(self, ed): 
        pass
    def on_corpAnnouncement(self, ca): 
        pass
    def on_dailyPLfeed(self, pl): 
        pass
    def on_bulkdatafeed(self, isSync, bd, ab):
        pass  # Now handled by on_marketdatafeed

    def on_marketdatafeed(self, md, ab):
        instrument = md.instrument
        if instrument not in self.myinstrument:
            return

        current_time = md.timestamp
        current_date = current_time.date()
        price = md.lastPrice
        nav = ab["availableBalance"]
        self.current_prices[instrument] = price

        # Handle EOD reset
        if self.last_eod_day is None:
            self.last_eod_day = current_date
        elif current_date != self.last_eod_day:
            self._simulate_end_of_day()
            self.last_eod_day = current_date
            for inst in self.myinstrument:
                self.first_tick_processed[inst] = False

        # Track open/close
        if self.today_open[instrument] is None:
            self.today_open[instrument] = price
        self.today_close[instrument] = price

        if self.first_tick_processed[instrument]:
            return
        self.first_tick_processed[instrument] = True

        prev_open = self.prev_open[instrument]
        prev_close = self.prev_close[instrument]

        if prev_open is not None and prev_close is not None:
            change_pct = ((prev_close - prev_open) / prev_open) * 100

            trigger = False
            buy_trigger_price = price

            if change_pct < -3:
                drop_amt = prev_open - prev_close
                buy_trigger_price = prev_close + 0.52 * drop_amt
                if price > buy_trigger_price and price < prev_open:
                    trigger = True
            elif change_pct > 3:
                rise_amt = prev_close - prev_open
                buy_trigger_price = prev_open + 0.52 * rise_amt
                if price > buy_trigger_price and price < prev_close:
                    trigger = True

            if trigger:
                order = AlgoAPIUtil.OrderObject()
                order.instrument = instrument
                order.openclose = 'open'
                order.buysell = 1
                order.ordertype = 1
                position_size_value = 0.10 * nav
                order.volume = int(position_size_value // price)
                order.price = price

                if change_pct < -3:
                    order.takeProfitLevel = prev_open * 1.0005
                elif change_pct > 3:
                    order.takeProfitLevel = prev_close * 1.0005

                order.trailingstop = 0.0003
                order.timeinforce = 3600

                if order.volume > 0:
                    self.evt.sendOrder(order)
                    self.prev_nav[instrument] = nav
                    self.evt.consoleLog(
                        f"BUY {instrument} at {price} (vol={order.volume}), "
                        f"TP={order.takeProfitLevel:.2f}, Trailing stop={order.trailingstop:.2f}, "
                        f"NAV={nav:.2f}, Commitment={self.total_commitment:.2f}, ChangePct={change_pct:.2f}%, "
                        f"TriggerPrice={buy_trigger_price:.2f}"
                    )



