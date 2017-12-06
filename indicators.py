#
# indicators.py
# Mike Cardillo
#
# System for containing all technical indicators and processing associated data

import talib
import logging
from decimal import Decimal


class IndicatorSubsystem:
    def __init__(self, period_list, indicator_config):
        self.logger = logging.getLogger('trader-logger')
        self.current_indicators = {}
        for period in period_list:
            self.current_indicators[period.name] = {}
            for indicator in indicator_config:
                self.current_indicators[period.name][indicator['name']] = {}
        self.indicators_list = []
        for indicator in indicator_config:
            calculate = getattr(self, indicator['calculate_fn'])
            if calculate:
                self.indicators_list.append({'name': indicator['name'],
                                             'calculate': calculate,
                                             'kwargs': indicator})

    def recalculate_indicators(self, cur_period):
        total_periods = len(cur_period.candlesticks)
        if total_periods > 0:
            self.closing_prices = cur_period.get_closing_prices()

            for indicator in self.indicators_list:
                indicator['calculate'](cur_period.name, indicator['kwargs'])

            self.current_indicators[cur_period.name]['close'] = cur_period.cur_candlestick.close
            self.current_indicators[cur_period.name]['total_periods'] = total_periods

    def calculate_avg_volume(self, period_name, volumes):
        avg_vol = talib.SMA(volumes, timeperiod=15)

        self.current_indicators[period_name]['avg_volume'] = avg_vol[-1]

    def calculate_bbands(self, period_name, kwargs):
        indicator_name = kwargs['name']
        timeperiod = kwargs['timeperiod']
        nbdevup = kwargs['nbdevup']
        nbdevdown = kwargs['nbdevdown']

        upperband, middleband, lowerband = talib.BBANDS(self.closing_prices, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdown, matype=0)

        self.current_indicators[period_name][indicator_name]['bband_upper'] = upperband[-1]
        self.current_indicators[period_name][indicator_name]['bband_middle'] = middleband[-1]
        self.current_indicators[period_name][indicator_name]['bband_lower'] = lowerband[-1]

        self.logger.debug("[INDICATORS %s:%s]: BBAND_UPPER: %f BBAND_LOWER: %f" %
                          (period_name, indicator_name,
                           self.current_indicators[period_name][indicator_name]['bband_upper'],
                           self.current_indicators[period_name][indicator_name]['bband_lower']))

    def calculate_ema(self, period_name, kwargs):
        indicator_name = kwargs['name']
        timeperiod = kwargs['timeperiod']
        ema = talib.EMA(self.closing_prices, timeperiod=timeperiod)
        self.current_indicators[period_name][indicator_name]['ema'] = ema[-1]

        self.logger.debug("[INDICATORS %s:%s]: EMA: %f" %
                          (period_name, indicator_name,
                           self.current_indicators[period_name][indicator_name]['ema']))

    def calculate_macd(self, period_name, kwargs):
        indicator_name = kwargs['name']
        fastperiod = kwargs['fastperiod']
        slowperiod = kwargs['slowperiod']
        signalperiod = kwargs['signalperiod']
        macd, macd_sig, macd_hist = talib.MACD(self.closing_prices, fastperiod=fastperiod,
                                               slowperiod=slowperiod, signalperiod=signalperiod)
        self.current_indicators[period_name][indicator_name]['macd'] = macd[-1]
        self.current_indicators[period_name][indicator_name]['macd_sig'] = macd_sig[-1]
        self.current_indicators[period_name][indicator_name]['macd_hist'] = macd_hist[-1]
        self.current_indicators[period_name][indicator_name]['macd_hist_diff'] = Decimal(macd_hist[-1]) - Decimal(macd_hist[-2])

        self.logger.debug("[INDICATORS %s:%s]: MACD: %f MACD_HIST: %f MACD_HIST_DIFF: %f" %
                          (period_name, indicator_name,
                           self.current_indicators[period_name][indicator_name]['macd'],
                           self.current_indicators[period_name][indicator_name]['macd_hist'],
                           self.current_indicators[period_name][indicator_name]['macd_hist_diff']))

    def calculate_mfi(self, period_name, highs, lows, closing_prices, volumes):
        mfi = talib.MFI(highs, lows, closing_prices, volumes)

        self.current_indicators[period_name]['mfi'] = mfi[-1]

    def calculate_obv(self, period_name, closing_prices, volumes, bid_or_ask):
        # cryptowat.ch does not include the first value in their OBV
        # calculation, we we won't either to provide parity
        obv = talib.OBV(closing_prices[1:], volumes[1:])
        obv_ema = talib.EMA(obv, timeperiod=21)

        self.current_indicators[period_name][bid_or_ask]['obv_ema'] = obv_ema[-1]
        self.current_indicators[period_name][bid_or_ask]['obv'] = obv[-1]

    def calculate_sar(self, period_name, highs, lows):
        sar = talib.SAR(highs, lows)

        self.current_indicators[period_name]['sar'] = sar[-1]

    def calculate_sma(self, period_name, kwargs):
        indicator_name = kwargs['name']
        timeperiod = kwargs['timeperiod']
        sma = talib.SMA(self.closing_prices, timeperiod=timeperiod)

        self.current_indicators[period_name][indicator_name]['sma'] = sma[-1]

        self.logger.debug("[INDICATORS %s:%s]: SMA: %f" %
                          (period_name, indicator_name,
                           self.current_indicators[period_name][indicator_name]['sma']))
