import MetaTrader5 as mt5
from datetime import datetime
import math
import threading
import time
import numpy as np

# define global variables

isCrypto = False
isForex = False
isDerivatives = True

devTP = 4.0  # pips
devSL = 3.0  # pips


class TraderHFT:
    def __init__(self, login_, password_, lotSize, server_):
        self.prevCandles = []
        self.login = login_
        self.password = password_
        self.server = server_
        self.lotSize = lotSize
        self.balance = 0
        self.startingBalance = 0
        self.equity = 0
        self.positions = []
        self.crypto = []
        self.stocks = []
        self.forex = []
        self.indices = []
        self.energies = []
        self.minors = []
        if not mt5.initialize(login=int(login_), password=password_, server=server_):
            print("initialize() failed, error code =", mt5.last_error())
            quit()
        self.account = {
            'name': mt5.account_info().name,
            'balance': mt5.account_info().balance,
            'leverage': mt5.account_info().leverage,
            'equity': mt5.account_info().equity,
            'margin': mt5.account_info().margin,
            'currency': mt5.account_info().currency,

        }
        self.startingBalance = mt5.account_info().balance
        symbols = mt5.symbols_get()

        # 'AUDUSDm', 'USDCHFm' , 'GBPUSDm',

        # self.pairs = ['GBPUSDm', ]
        self.pairs = ['Volatility 100 (1s) Index', ]

        self.symbols = []
        self.getSymbolInfo()

    def getAvailableSymbols(self):
        return self.symbols

    def getAccountInfo(self):
        return self.account

    def getSymbolInfo(self):
        for symbol in self.pairs:
            selected = mt5.symbol_select(symbol, True)
            if not selected:
                print(f"Failed to select {symbol}")
                # mt5.shutdown()
                quit()
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                self.symbols.append({
                    'name': symbol,
                    'category': symbol_info.category,
                    'askPrice': math.floor(symbol_info.ask * 10000) / 10000,
                    'bidPrice': math.floor(symbol_info.bid * 10000) / 10000,
                    'volume': symbol_info.volume,
                    'spread': f'{abs(math.floor(symbol_info.bid * 10000) - math.floor(symbol_info.ask * 10000))}',

                })

    def getTrade(self):
        for symbol in self.symbols:
            # buy details
            print(mt5.symbol_info(symbol))

            if isCrypto:
                print('Working with CRYPTO market')
                pass
            elif isForex:
                print('Working with FOREX market')

                stop_loss_buy = symbol['askPrice'] - devSL / 10000
                take_profit_buy = devTP / 10000 + symbol['askPrice']
                entry_buy = symbol['askPrice']
                print(take_profit_buy, entry_buy, stop_loss_buy)
                print(symbol)

                # sell details
                stop_loss_sell = symbol['bidPrice'] + devSL / 10000
                take_profit_sell = symbol['bidPrice'] - devTP / 10000
                entry_sell = symbol['bidPrice']
                print(take_profit_sell, entry_sell, stop_loss_sell)
                print()

                # go long ,short using threads
                buy_args = {'sl': stop_loss_buy, 'tp': take_profit_buy, 'ask_price': entry_buy,
                            'symbol': symbol['name']}
                thread1 = threading.Thread(target=self.goLong, kwargs=buy_args)

                sell_args = {'sl': stop_loss_sell, 'tp': take_profit_sell, 'bid_price': entry_buy,
                             'symbol': symbol['name']}
                thread2 = threading.Thread(target=self.goShort, kwargs=sell_args)
                thread1.start()
                thread2.start()
            elif isDerivatives:
                # print()
                # print('Working with DERIVATIVE/BINARY market')

                stop_loss_buy = symbol['askPrice'] - devSL
                take_profit_buy = devTP + symbol['askPrice']
                entry_buy = symbol['askPrice']
                # print(take_profit_buy, entry_buy, stop_loss_buy)
                # print(symbol['name'])
                #
                # print('buy slprice', stop_loss_buy, 'entry', symbol['askPrice'], 'takeprofit', take_profit_buy)
                #
                # sell details
                stop_loss_sell = symbol['bidPrice'] + devSL
                take_profit_sell = symbol['bidPrice'] - devTP
                entry_sell = symbol['bidPrice']
                # print(take_profit_sell, entry_sell, stop_loss_sell)
                # print()
                # print('sell slprice', stop_loss_sell, 'entry', symbol['bidPrice'], 'takeprofit', take_profit_sell)

                # execute orders

                # go long ,short using threads
                buy_args = {'sl': stop_loss_buy, 'tp': take_profit_buy, 'ask_price': entry_buy,
                            'symbol': symbol['name']}
                thread1 = threading.Thread(target=self.goLong, kwargs=buy_args)

                sell_args = {'sl': stop_loss_sell, 'tp': take_profit_sell, 'bid_price': entry_buy,
                             'symbol': symbol['name']}
                thread2 = threading.Thread(target=self.goShort, kwargs=sell_args)
                thread1.start()
                thread2.start()

                pass
            else:
                print('No Market selected')

        pass

    def calculateProfit(self):
        self.equity = mt5.account_info().equity
        return mt5.account_info().equity - self.startingBalance
        # return self.equity - self.balance

    def goLong(self, sl, tp, ask_price, symbol):
        # send buy request
        print(symbol)
        deviation = 20
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": self.lotSize,
            "type": mt5.ORDER_TYPE_BUY,
            "price": ask_price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 134444,
            "comment": "order type buy sent",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        # print(request)
        # check the execution result
        # print(
        #     "1. BUY order_send(): by {} {} lots at {} with deviation={} points".format(symbol, self.lotSize, ask_price,
        #                                                                                deviation))
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.closePositions()
            print("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result._asdict()
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
            print("shutdown() and quit")
            mt5.shutdown()
            quit()

    def goShort(self, sl, tp, bid_price, symbol):
        deviation = 20
        # send sell request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": self.lotSize,
            "type": mt5.ORDER_TYPE_SELL,
            "price": bid_price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 234000,
            "comment": "order type buy sent",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        # check the execution result
        # print(
        #     "2.SELL order_send(): by {} {} lots at {} with deviation={} points".format(symbol, self.lotSize, bid_price,
        #                                                                                deviation))
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.closePositions()
            print("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result._asdict()
            for field in result_dict.keys():
                print("   {}={}".format(field, result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field == "request":
                    traderequest_dict = result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        print(" traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
            print("shutdown() and quit")
            mt5.shutdown()
            quit()

    def findOpenPositions(self):
        self.positions = mt5.positions_get()
        return self.positions

    def closePositions(self):
        if mt5.positions_total() > 0:
            for position in mt5.positions_get():
                mt5.Close(symbol=position.symbol, ticket=position.ticket)
            if mt5.positions_total() > 0:
                print('Failed to close all positions. retrying')
                self.closePositions()
            else:
                print('ALL positions closed with profit of', self.calculateProfit())
        else:
            print('No open positions')
        self.startingBalance = mt5.account_info().balance

    def getMarketStructure(self):
        timeframe = mt5.TIMEFRAME_M1
        count = 20
        rates = mt5.copy_rates_from_pos(self.pairs[0], timeframe, 0, count)
        arr = []
        for r in rates:
            opn = r[1]
            clss = r[4]
            md = (clss - opn) / 2 + opn
            arr.append(md)
        x = np.array(range(count))
        y = np.array(arr)
        coefficients = np.polyfit(x, y, 1)
        gradient = coefficients[0]
        return gradient

    def getTrend(self):
        timeframe = mt5.TIMEFRAME_M1
        rates = mt5.copy_rates_from_pos(self.pairs[0], timeframe, 0, 6)
        for r in rates:
            self.prevCandles.append({
                'open': r[1],
                'close': r[4],
                'high': r[2],
                'low': r[3]
            })

    def getTick(self):
        lasttick = mt5.symbol_info_tick(self.pairs[0])
        print(lasttick)
        pass

    def isBullish(self, candle):
        if candle['close'] > candle['open']:
            return True
        return False

    def getCandleGradient(self, candles):
        arr = []
        for c in candles:
            arr.append(self.candleMidpointPrice(c))
        x = np.array(range(len(candles)))
        y = np.array(arr)
        coefficients = np.polyfit(x, y, 1)
        gradient = coefficients[0]
        return gradient

    def isBearish(self, candle):
        if candle['open'] > candle['close']:
            return True
        return False

    def candleSize(self, candle):
        return abs(candle['open'] - candle['close'])

    def candleMidpointPrice(self, candle):
        return (candle['close'] - candle['open']) / 2 + candle['open']

    def candleWickUp(self, candle):
        if candle['close'] > candle['open']:  # bullish
            return candle['high'] - candle['close']
        else:  # bearish
            return candle['high'] - candle['open']

    def candleWickDown(self, candle):
        if candle['close'] > candle['open']:  # bullish
            return candle['open'] - candle['low']
        else:  # bearish
            return candle['close'] - candle['low']

    # CANDLE TREND IDENTIFICATION
    def trendRecognition(self):
        bullcount = 1
        bearcount = 1
        tradeReasons = []
        self.getTrend()
        c1 = self.prevCandles[0]
        c2 = self.prevCandles[1]
        c3 = self.prevCandles[2]
        c4 = self.prevCandles[3]
        c5 = self.prevCandles[4]

        # 1.  BULLISH/BEARISH GAP- CONTINUATION
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/526-gaps
        '''
            A bullish gap is defined as a Japanese candlestick with an opening price higher than the closing price of
            the previous candlestick. It generally occurs in a bullish trend.
            
            If the lowest point of the candlestick after the gap jumps higher than the next candlestick, 
            the structure can be considered invalidated
        '''
        if self.isBullish(c5) and self.isBullish(c4):
            # bullish market
            if self.getMarketStructure() > 0:  # uptrend
                if abs(int(c4['close'] - c5['open'])) > 0:
                    # trend continues upwards
                    bullcount += 1
                    tradeReasons.append('Japanese bull gap')

        '''
            A bearish gap is defined as a Japanese candlestick with an opening price lower than the closing price of the
            previous candlestick. It generally occurs in a bearish trend.
            
            If the highest point of the candlestick after the gap jumps higher than the next candlestick, 
            the structure can be considered invalidated
        '''
        if self.isBearish(c5) and self.isBearish(c4):
            # bearish markwet
            if self.getMarketStructure() < 0:  # downtrend
                if c4['close'] - c5['open'] > 0.5:
                    # trend continues upwards
                    bearcount += 1
                    tradeReasons.append('Japanese bear gap')

        # 2. JAPANESE IRIKUBI
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/528-irikubi
        ''' 
            A bullish irikubi (line in the neck) structure is comprised of two Japanese candlesticks.
            The first is a large bullish candlestick (green) followed by a small bearish candlestick (red) with a 
            closing just below the closing level of the previous candlestick. The second candlestick must be 
            significantly smaller than the first.
            
            For the structure to be validated, the next candlestick must be bullish and close above the opening 
            price of the small bearish candlestick (red).
        '''

        if self.isBullish(c5) and self.isBearish(c4) and self.isBullish(c3):
            if self.candleSize(c3) >= 2 * self.candleSize(c4):
                if self.getMarketStructure() > 0:
                    if c3['close'] > c4['close']:
                        if c5['close'] > c4['open']:
                            # valid bullish continuation
                            bullcount += 1
                            tradeReasons.append('Japanese bull Irikubi')

        '''
            A bearish irikubi (line in the neck) structure is comprised of two Japanese candlesticks. The first is a large 
            bearish candlestick (red) followed by a small bullish candlestick (green) with a closing just above the closing
            level of the previous candlestick. The second candlestick must be significantly smaller than the first.
            
            For the structure to be validated, the next candlestick must be bearish and close below the opening price of
            the small bullish candlestick (green).
        '''

        if self.isBearish(c5) and self.isBullish(c4) and self.isBearish(c3):
            if self.candleSize(c3) >= 2 * self.candleSize(c4):
                if self.getMarketStructure() < 0:
                    if c3['close'] < c4['close']:
                        if c5['close'] < c4['open']:
                            # valid bear continuation
                            bearcount += 1
                            tradeReasons.append('Japanese bear Irikubi')

        # 3. Japanese candlesticks - Mat hold
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/535-mat-hold

        '''
            A mat hold structure is comprised of five Japanese candlesticks.This is a variation of the three methods
            structure.The first is a large bullish candlestick (green) followed by three small bearish candlesticks (red).
            Each small candlestick must close lower than the previous one.The opening of the second candlestick must occur
            on a bullish gap.Finally, the last candlestick must also open on a bullish gap and close above the second 
            candlestick’s high point.The pattern is also called a rising three methods pattern.
        '''

        if self.isBullish(c1) and self.isBullish(c5) and self.isBearish(c2):
            if self.candleSize(c1) >= 2 * self.candleSize(c2) and self.candleSize(c1) >= 2 * self.candleSize(
                    c3) and self.candleSize(c1) >= 2 * self.candleSize(c4) and self.candleSize(c5) > self.candleSize(
                c4):
                if self.getCandleGradient([c2, c3, c4]) < 0:
                    if c2['open'] - c1['close'] > 0.5 and c5['close'] > c2['high']:
                        if (self.candleMidpointPrice(c1) > c2['low'] and self.candleMidpointPrice(c1) >
                                c3['low'] and self.candleMidpointPrice(c1) > c4['low']):
                            # valid bullish uptrend
                            bullcount += 1
                            tradeReasons.append('Japanese bull mat hold ')

        '''
            An inverted mat hold structure is comprised of five Japanese candlesticks.This is a variation of the three 
            methods structure.The first is a large bearish candlestick (red) followed by three small bullish candlesticks 
            (green).Each small candlestick must close higher than the previous one.The opening of the second candlestick 
            must occur on a bearish gap.Finally, the last candlestick must also open on a bearish gap and close below the 
            second candlestick’s lowest point. The pattern is also called an inverted saucer pattern.
        '''

        if self.isBearish(c1) and self.isBearish(c5) and self.isBullish(c2):
            if (self.candleSize(c1) >= 2 * self.candleSize(c2) and self.candleSize(c1) >= 2 * self.candleSize(c3)
                    and self.candleSize(c1) >= 2 * self.candleSize(c4) and self.candleSize(c5) > self.candleSize(c4)):
                if self.getCandleGradient([c2, c3, c4]) > 0:
                    if c2['open'] - c1['close'] > 0 and c2['low'] > c5['close']:
                        if (self.candleMidpointPrice(c1) > c2['high'] and self.candleMidpointPrice(c1) >
                                c3['high'] and self.candleMidpointPrice(c1) > c4['high']):
                            # valid bearish trend
                            bearcount += 1
                            tradeReasons.append('Japanese bear anti mat hold ')

        # 4 Japanese candlesticks - Thrusting line
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/531-thrusting-line

        '''
            A bullish thrusting line structure is comprised of two Japanese candlesticks.The first is a large bullish 
            candlestick (green) followed by a bearish candlestick (red) with a close occurring in the body of the first 
            candlestick without exceeding its midpoint.The opening must also occur above the first candlestick.The first 
            candlestick must be large and the second one smaller.
            
            If the mid-point of the large bullish candlestick is exceeded, the structure can be considered invalidated.
        '''

        if self.isBullish(c4) and self.isBearish(c5):
            if self.candleSize(c4) > self.candleSize(c5):
                if self.candleMidpointPrice(c4) < c5['low'] and c5['open'] > c4['close']:
                    if self.getMarketStructure() > 0:
                        # valid bullish trend
                        bullcount += 1
                        tradeReasons.append('Japanese bull thrusting line ')

        '''
            A bearish thrusting line structure is comprised of two Japanese candlesticks.The first is a large bearish 
            candlestick (red) followed by a bullish candlestick (green) with a close occurring in the body of the first 
            candlestick without it exceeding its midpoint.The opening must also occur under the first candlestick.The first 
            candlestick must be large and the second one smaller.
        '''

        if self.isBearish(c4) and self.isBullish(c5):
            if self.candleSize(c4) > self.candleSize(c5):
                if self.candleMidpointPrice(c4) > c5['high'] and c5['open'] < c4['close']:
                    if self.getMarketStructure() < 0:
                        # valid bullish trend
                        bearcount += 1
                        tradeReasons.append('Japanese bear thrusting line ')

        # 5. Japanese candlesticks - Three line break
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/536-three-line-break

        '''
            A bullish three line break structure is comprised of four Japanese candlesticks. The first three candlesticks
            are bullish (green) and small. The opening occurs at the closing price of the previous candlestick and the 
            closing occurs at the highest point of the candlestick. The fourth candlestick is a large bearish (red) and 
            encompass the three bullish candlesticks. It must close below the opening level of the first one.
            
            If the closing of the last candlestick does not occur below the opening level of the first candlestick or 
            if the closing does not occur at the low point, then the bullish three line break structure is invalidated.
        '''
        if self.isBullish(c2) and self.isBullish(c3) and self.isBullish(c4) and self.isBearish(c5):
            if (self.candleSize(c5) >= 2 * self.candleSize(c2) and self.candleSize(c5) >= 2 * self.candleSize(c3)
                    and self.candleSize(c5) >= 2 * self.candleSize(c4)):
                if self.candleWickDown(c2) < self.candleSize(c2):
                    if self.candleWickDown(c3) < self.candleSize(c3):
                        if self.candleWickDown(c4) < self.candleSize(c4):
                            if c2['close'] == c2['high'] and c3['close'] == c3['high'] and c4['close'] == c4['high']:
                                if (c4['open'] == c3['close'] and c3['open'] == c2['close']
                                        and c2['open'] == c1['close']):
                                    if c4['close'] > c3['close'] > c2['close']:
                                        if c5['close'] < c2['open']:
                                            # valid bullish trend
                                            bullcount += 1
                                            tradeReasons.append('Japanese bull Three line break ')

        '''
            A bearish three line break structure is comprised of four Japanese candlesticks. The first three candlesticks 
            are bearish (red) and small. The opening occurs at the closing price of the previous candlestick and the 
            closing occurs at the lowest point of the candlestick. The fourth candlestick is a large bullish (green) and 
            encompasses the three bearish candlesticks. It must close below the opening level of the first one.
            
            If the closing of the last candlestick does not occur below the closing level of the first candlestick or if
            the closing does not occur at the high point, then the bearish three line break structure is invalidated.
        '''

        if self.isBearish(c2) and self.isBearish(c3) and self.isBearish(c4) and self.isBullish(c5):
            if (self.candleSize(c5) >= 2 * self.candleSize(c2) and self.candleSize(c5) >= 2 * self.candleSize(c3)
                    and self.candleSize(c5) >= 2 * self.candleSize(c4)):
                if self.candleWickUp(c2) < self.candleSize(c2):
                    if self.candleWickUp(c3) < self.candleSize(c3):
                        if self.candleWickUp(c4) < self.candleSize(c4):
                            if c4['close'] < c3['close'] < c2['close']:
                                if (c4['open'] == c3['close'] and c3['open'] == c2['close']
                                        and c2['open'] == c1['close']):
                                    if c5['close'] > c2['open']:
                                        # valid bullish trend
                                        bearcount += 1
                                        tradeReasons.append('Japanese bear Three line break ')

        # 6. Japanese candlesticks - Atekubi
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/529-atekubi
        '''
            A bullish atekubi (line below the neckline) is a structure comprised of two Japanese candlesticks. The first 
            is a large bullish candlestick (green) followed by a small bearish candlestick (red) with a closing just above
            the closing level of the previous candlestick. The second candlestick must be significantly smaller than the 
            first.
            
            For the structure to be validated, the next candlestick must be bullish and close above the opening level of
            the small bearish candlestick (red).
            
            If the lowest point of the small bearish candlestick surmounts the next candlestick, the structure can be 
            considered invalidated.

        '''
        if self.isBullish(c3) and self.isBearish(c4) and self.isBullish(c5):
            if self.candleSize(c3) >= 2 * (self.candleSize(c4)):
                if c4['close'] > c3['close'] and c5['close'] > c4['open']:
                    if self.getMarketStructure() > 0:
                        # bullish confirmation
                        bullcount += 1
                        tradeReasons.append('Japanese bull Atekubi ')

        '''
            A bearish atekubi (line below the neck) is a structure comprised of two Japanese candlesticks. The first is a 
            large bearish candlestick (red) followed by a small bullish candlestick (green) with a closing just below the
            closing level of the previous candlestick. The second candlestick must be significantly smaller than the first.
            
            For the structure to be validated, the next candlestick must be bearish and close below the opening level of 
            the small bullish candlestick (green).
            
            If the highest point on the small bullish candlestick surmounts the next candlestick, the structure can be
            considered invalidated.
        '''

        if self.isBearish(c3) and self.isBullish(c4) and self.isBearish(c5):
            if self.candleSize(c3) >= 2 * (self.candleSize(c4)):
                if c4['close'] < c3['close'] and c5['close'] < c4['open']:
                    if self.getMarketStructure() < 0:  # downtrend
                        # bullish confirmation
                        bearcount += 1
                        tradeReasons.append('Japanese bear Atekubi ')

        # ##REVERSAL CANDLESTICK PATTERNS=------

        # 1. Japanese candlesticks - Engulfing lines
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/539-engulfing

        '''
            Bullish engulfing lines is a structure made up of two Japanese candlesticks. The first is a small bearish 
            candlestick (red) followed by a large bullish candlestick (green). The second candlestick opens in a bearish 
            gap but its closing is above the first candlestick’s opening level. Therefore, the large candlestick 
            incorporates the first, which is what forms the bullish engulfing lines.
            
            Note: Bullish engulfing lines have to occur with high volumes, this indicates a real desire for a reversal and
            not simply sellers taking profits.
            
            If the next candlestick is not bullish or a bullish gap has not occurred, the bullish engulfing lines 
            pattern is invalidated
        
        '''
        if self.isBearish(c3) and self.isBullish(c4) and self.isBullish(c5):
            if self.candleSize(c4) >= 2 and self.candleSize(c4) > self.candleSize(c3):
                if c3['low'] - c4['open'] > 0.1 and c4['close'] > c3['open']:
                    # bullish characteristics
                    if self.getMarketStructure() < 0:
                        bullcount += 1
                        tradeReasons.append('Japanese bull engulfing ')

        '''
            Bearish engulfing lines is a structure made up of two Japanese candlesticks. The first is a small bullish 
            candlestick (green) followed by a large bearish candlestick (red). The second candlestick opens in a bullish
            gap but its closing is below the first candlestick’s opening level. Therefore, the large candlestick 
            incorporates the first, which is what forms the bearish engulfing lines.
            
            Bearish engulfing lines have to occur with high volumes, this indicates a real desire for a reversal and not
            simply buyers taking profits.
            
            If the next candlestick is not bearish or a bearish gap has not occurred, the bearish engulfing lines
            pattern is invalidated.

        '''

        if self.isBullish(c3) and self.isBearish(c4) and self.isBearish(c5):
            if self.candleSize(c4) >= 2 and self.candleSize(c4) > self.candleSize(c3):
                if c3['low'] - c4['close'] > 0.1 and c4['open'] > c3['high']:
                    # bearish characteristics
                    if self.getMarketStructure() > 0:
                        bearcount += 1
                        tradeReasons.append('Japanese bear engulfing ')

        # 2. Japanese candlesticks - Tweezers top and bottom
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/542-tweezers-top-and-bottom

        '''
            A tweezer bottom structure is comprised of two Japanese candlesticks. The first is a large bearish candlestick
            (red) followed by a hammer doji. The second candlestick opens in a bullish gap and closes at the opening price
            of the first candlestick.
            
            If the next candlestick is not bullish or does not open onto a bullish gap, the tweezer bottom structure is 
            invalidated.
        '''

        if self.isBearish(c3) and self.isBullish(c4) and self.isBullish(c5):
            if self.candleSize(c3) >= 3 and self.candleSize(c4) <= 1:
                if self.candleWickDown(c4) >= 2 * self.candleSize(c4) and self.candleWickDown(
                        c4) >= 2 * self.candleWickUp(c4):
                    # bullish pattern
                    if self.getMarketStructure() < 0:
                        bullcount += 1
                        tradeReasons.append('Japanese bull tweezer ')

        '''
            A tweezer top structure is comprised of two Japanese candlesticks. The first is a large bullish candlestick 
            (green) followed by a gravestone doji. The second candlestick opens on a bearish gap and closes at the opening
            price of the first candlestick.
            
            If the next candlestick is not bearish or does not open onto a bearish gap, the tweezer top structure is 
            invalidated.
        '''

        if self.isBullish(c3) and self.isBearish(c4) and self.isBearish(c5):
            if self.candleSize(c3) >= 3 and self.candleSize(c4) <= 1:
                if self.candleWickUp(c4) >= 2 * self.candleSize(c4) and self.candleWickUp(
                        c4) >= 2 * self.candleWickDown(c4):
                    # bearish pattern
                    if self.getMarketStructure() > 0:
                        bearcount += 1
                        tradeReasons.append('Japanese bear tweezer ')

        # 3. Japanese candlesticks - Morning star
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/543-morning_star

        '''
            The morning star’s structure is made up of three Japanese candlesticks. The first is a large, solid, (red) 
            bearish candlestick followed by a small bullish or bearish candlestick which closes below the first candlestick.
            The third candlestick is a large full bullish candlestick (green).
            
            The morning star is a reversal pattern, it indicates a bullish trend reversal. The second candlestick reflects 
            the inability of sellers to support the bearish movement, there is a lock of momentum and buyers eventually 
            regain control.
            
            Note: There are many variations in the second candlestick with this pattern. It can be separated from the other 
            two (abandoned baby structure) or take the form of a doji (doji morning star). Regardless of the opening and
            closing levels, the important thing is that the candlestick’s body is small.
        '''
        if self.isBearish(c3) and self.isBullish(c5):
            if self.candleSize(c3) >= 2 > self.candleSize(c4) and self.candleSize(
                    c5) >= 2 > self.candleSize(c4):
                if self.getMarketStructure() < 0:  # downtrend
                    if c4['close'] < c3['close']:
                        # bullish reversal
                        bullcount += 1
                        tradeReasons.append('Japanese bull Morning star ')

        # 4. Japanese candlesticks - Evening star
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/544-evening-star

        '''
            The morning star’s structure is made up of three Japanese candlesticks. The first is a large, solid, (red) 
            bearish candlestick followed by a small bullish or bearish candlestick which closes below the first candlestick.
            The third candlestick is a large full bullish candlestick (green).
            The evening star is a reversal pattern, it indicates a downward trend reversal. The second candlestick reflects 
            the inability of buyers to support the bullish movement, there is a lack of momentum and sellers eventually 
            regain control.
        '''

        if self.isBullish(c3) and self.isBearish(c5):
            if self.candleSize(c3) >= 2 > self.candleSize(c4) and self.candleSize(
                    c5) >= 2 > self.candleSize(c4):
                if self.getMarketStructure() > 0:  # uptrend
                    if c4['close'] > c3['close']:
                        # bearish reversal
                        bearcount += 1
                        tradeReasons.append('Japanese bear Evening star ')

        # 5. Japanese candlesticks - Belt hold
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/547-belt-hold

        '''
            A bullish belt hold line is a structure comprised of a single Japanese candlestick. This is a long bullish
            candlestick (green) has an opening price that corresponds to the lowest point on the candlestick. The opening
            must occur in a bearish gap.
            
            The morning star is a reversal pattern, it indicates a bullish trend reversal. The second candlestick 
            reflects the inability of sellers to support the bearish movement, there is a lock of momentum and buyers 
            eventually regain control.

        '''
        if self.isBullish(c4) and self.isBullish(c5):
            if self.candleSize(c4) >= 2 and c4['open'] == c4['low']:
                if self.getMarketStructure() < 0:
                    # bullish reversal
                    bullcount += 1
                    tradeReasons.append('Japanese bull Belt hold ')

        '''
            A bearish belt hold line is a structure comprised of a single Japanese candlestick. This is a long bearish 
            candlestick (red) has an opening price that corresponds to the highest point on the candlestick. The opening 
            must be made in a bullish gap.
            
            A bearish belt hold line is a reversal pattern, it indicates a reversal of the bearish trend. This reflects a 
            massive profit taking following a bullish gap. Taking advantage of this opportunity, sellers rouse and fuel the
            trend reversal.
            
            If the next candlestick is not bearish or does not open on a bearish gap, the bearish belt hold line is invalidated.
        '''

        if self.isBearish(c4) and self.isBearish(c5):
            if self.candleSize(c4) >= 2 and c4['high'] == c4['open']:
                if self.getMarketStructure() > 0:
                    # bearish reversal
                    bearcount += 1
                    tradeReasons.append('Japanese bear Belt hold ')

        # 6. Japanese candlesticks - Dumpling top
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/550-dumpling-top

        '''
            A dumpling top structure is comprised of several Japanese candlesticks. The first candlesticks are bullish or
            bearish with a small body. This series of candlesticks should form a rounded top. Then, a last candlestick is 
            formed with a bearish gap opening. This is the opposite of the frying pan bottom.
            
            A dumpling top is a reversal pattern, it indicates reversal of the bearish trend. This reflects a gradual
            exhaustion of buyers before the sellers forcefully regain control.

        '''

        if self.getMarketStructure() > 0 and self.isBearish(c5):
            if c4['low'] > c5['high']:
                # bullish reversal
                bearcount += 1
                tradeReasons.append('Japanese bear Dumpling top ')

        # 7. Japanese candlestick - Frying pan bottom
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/551-frying-pan-bottom

        '''
            A frying pan bottom structure is comprised of several Japanese candlesticks. The first candlesticks are bullish 
            or bearish with small bodies. This series of candlesticks should form a rounded bottom. Then, a last candlestick
            is formed with a bullish gap opening. This is the opposite of a Dumpling top.
            
            A frying pan bottom structure is a reversal pattern, it indicates a reversal in the bullish trend. This 
            reflects a gradual exhaustion of sellers before buyers forcefully regain control.
            
            If the bullish gap is filled on the last candlestick, the frying pan bottom structure is invalidated.
        '''

        if self.getMarketStructure() < 0 and self.isBullish(c5):
            if c5['low'] > c4['high']:
                # bearish reversal
                bullcount += 1
                tradeReasons.append('Japanese bull Frying pan bottom')

        # 8.Japanese candlesticks - Tower top
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/553-tower-top

        '''
            A tower top structure is comprised of several Japanese candlesticks. The bullish phase of the pattern can be 
            formed by a succession of several small bullish (green) candlesticks or by a large candlestick. On the 
            following candlesticks, there is a slowdown which results in lateral evolution in the price with small 
            candlesticks (which form the top). Finally, one or more large bearish candlesticks (red) complete the 
            structure. This is the opposite of the tower bottom.
            
            A tower top is a reversal pattern, it indicates a reversal of the bearish trend. This reflects a gradual 
            exhaustion of buyers before the sellers forcefully regain control
                 
        '''
        if self.isBullish(c1) and self.isBullish(c2) and self.isBullish(c3) and self.isBearish(c4) and self.isBearish(
                c5):
            if self.candleSize(c1) > self.candleSize(c2) > self.candleSize(c3) and self.candleSize(
                    c5) >= 2 and self.candleSize(c5) > self.candleSize(c4):
                if self.getMarketStructure() > 0:  # uptrend
                    # bearish reversal bulls exhausted
                    bearcount += 1
                    tradeReasons.append('Japanese bear Tower top')

        # 9. Japanese candlesticks - Tower bottom
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/554-tower-bottom
        '''
            A tower bottom structure is comprised of several Japanese candlesticks. The bearish phase of the pattern can be
            formed by a succession of several small bearish candlesticks (red) or by a large candlestick. On the following 
            candlesticks, there is a slowdown which results in lateral evolution in the price with small candlesticks 
            (which form the bottom). Finally, one or more large bullish candlesticks (green) complete the structure. 
            This is the opposite of a Tower top.
            
            A tower bottom is a reversal pattern, it indicates a bullish trend reversal. This reflects a gradual 
            exhaustion of sellers before buyers forcefully regain control.
            If the bullish candlestick(s) are not long, the tower bottom structure is invalidated.

        '''
        if self.isBearish(c1) and self.isBearish(c2) and self.isBearish(c3) and self.isBullish(c4) and self.isBullish(
                c5):
            if self.candleSize(c1) > self.candleSize(c2) > self.candleSize(c3) and self.candleSize(
                    c5) >= 2 and self.candleSize(c5) > self.candleSize(c4):
                if self.getMarketStructure() < 0:  # downtrend
                    # bullish reversal bears exhausted
                    bullcount += 1
                    tradeReasons.append('Japanese bull Tower bottom')

        # 10. Japanese candlesticks - Hanging man
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/556-hanging-man

        '''
            A hanging man structure is comprised of a single Japanese candlestick. The candlestick has a small body, bullish
            or bearish, with a long low wick which is at least twice as long as the body. The closing price of the next 
            candlestick must be lower than the lowest point of the hanging man.
            
            A hanging man often forms after a significant increase characterized by several large green Japanese 
            candlesticks. If the pattern occurs after a bearish trend, it is called a hammer.
            
            A hanging man is a reversal pattern, it indicates a reversal of the bearish trend. This reflects increasing 
            selling pressure, with a temporary takeover during the candlestick’s life.
            
            It is preferable if the candlestick is bearish, this reinforces the relevance of the hammer but a bullish 
            candlestick does not invalidate the pattern. The ideal is a hanging man doji. The larger the shadow and the 
            smaller the body, the stronger the pattern.
            
            If the next candlestick is not bearish or does not open on a bearish gap, the hanging man is invalidated.

        '''

        if self.isBearish(c5):
            if self.getMarketStructure() > 0:  # uptrend
                if self.candleWickDown(c4) >= 2 * (self.candleSize(c4)) and self.candleWickDown(c4) >= 2 * (
                        self.candleWickUp(c4)):
                    # bearish reversal bulls exhausted
                    if c5['close'] < c4['low']:
                        bearcount += 1
                        tradeReasons.append('Japanese bear Hanging man')

        # 11. Japanese candlesticks - Hammer
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/557-hammer
        '''
            A hammer structure is comprised of a single Japanese candlestick. The candlestick has a small body, bullish or 
            bearish, with a long low wick which is at least twice as long as the body. The closing price of the next 
            candlestick must be higher than the top of the hammer.
            
            A hammer often forms after a significant drop characterized by several large red Japanese candlesticks. 
            If the pattern is formed after a bullish trend, it is called a hanging man.
            
            A hammer is a reversal pattern, it indicates a bullish trend reversal. This reflects an over-sold market 
            where buyers eventually gain the upper hand at the end of the period.
            
            It is better is the candlestick is bullish, this reinforces the hammer’s relevance but a bearish candlestick
            does not invalidate the pattern. A hammer doji is ideal. The larger the shadow and the smaller the body, 
            the stronger the pattern.
            
            If the next candlestick is not bullish or does not open on a bullish gap, the hammer is invalidated.
         
        '''
        if self.isBullish(c5):
            if self.getMarketStructure() < 0:  # downtrend
                if (self.candleWickDown(c4) >= 2 * (self.candleSize(c4)) and self.candleWickDown(c4) >= 2 *
                        (self.candleWickUp(c4))):
                    if c5['close'] > c4['high']:
                        # bearish reversal bulls exhausted
                        bullcount += 1
                        tradeReasons.append('Japanese bull Hammer')

        # 12. Japanese candlesticks - Shooting star
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/558-shooting-star

        '''
            A shooting star structure is comprised of a single Japanese candlestick. The candlestick has a small body, 
            bullish or bearish, with a large high wick which must be at least twice the length of the body. The closing 
            price of the next candlestick must be lower than the lowest point of the shooting star.
            
            A shooting star often forms after a significant rise characterized by several large green Japanese candlesticks.
            If the pattern is formed after a bearish trend, it is called an inverted hammer.
            
            A shooting star is a reversal pattern, it indicates a reversal of a bullish trend. This reflects an overbought 
            market where sellers end up taking over at the end of the period.
            
            It is preferable if the candlestick is bearish, this reinforces the relevance of the shooting star but a bullish
            candlestick does not invalidate the pattern. The ideal is a shooting star doji. The larger the shadow and the 
            smaller the body, the more powerful the pattern.
            
            If the next candlestick is not bearish or does not open on a bearish gap, the shooting star is invalidated.
        '''

        if self.isBearish(c5):
            if self.getMarketStructure() > 0:  # uptrend
                if (self.candleWickUp(c4) >= 2 * (self.candleSize(c4)) and self.candleWickUp(c4) >= 2 *
                        (self.candleWickDown(c4))):
                    if c5['close'] > c4['low']:
                        # bearish reversal bulls exhausted
                        bearcount += 1
                        tradeReasons.append('Japanese bear shooting star')

        # 13. Japanese candlesticks - Inverted hammer
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/559-inverted-hammer
        '''
            An inverted hammer structure is comprised a single Japanese candlestick. The candlestick has a small body, 
            bullish or bearish, with a long high wick which is at least twice as long as the body. The closing price of the
            next candlestick must be higher than the top of the hammer.
            
            An inverted hammer often forms after a significant drop characterized by several large red Japanese
            candlesticks. If the pattern is formed after a bullish trend, it is called a shooting star.
            
            An inverted hammer is a reversal pattern, it indicates a bullish trend reversal. This reflects increasing 
            buying pressure, with a temporary takeover during the candlestick’s life.
            
            It is preferable if the candlestick is bullish, this reinforces the hammer’s relevance but a bearish
            candlestick does not invalidate the pattern. The ideal is an inverted hammer doji. The larger the shadow and 
            the smaller the body, the stronger the pattern.
            
            If the next candlestick is not bullish or does not open on a bullish gap, the inverted hammer is invalidated.

        '''

        if self.isBullish(c5):
            if self.getMarketStructure() < 0:  # downtrend
                if (self.candleWickUp(c4) >= 2 * (self.candleSize(c4)) and self.candleWickUp(c4) >= 2 *
                        (self.candleWickDown(c4))):
                    if c5['close'] > c4['high']:
                        # bullish reversal, bears exhausted
                        bullcount += 1
                        tradeReasons.append('Japanese bull inverted Hammer')

        # 14. Japanese candlesticks - Advance block
        # https://www.centralcharts.com/en/gm/1-learn/7-technical-analysis/28-japanese-candlesticks/560-advance-block

        '''
            An advance block is a structure comprised of three Japanese candlesticks. All three are bullish (green). The
            first is a large candlestick followed by two others with high wicks and small bodies. The last candlestick 
            takes the form of an inverted hammer.
            
            An advance block often occurs after a significant increase characterized by several large green Japanese
            candlesticks.
            
            An advance block is a reversal pattern, it indicates a reversal of the bearish trend. This reflects depletion 
            of the buying power and upcoming profit taking.
            
            The third candlestick is not necessarily an inverted hammer. The important thing is that the bodies of the 
            candlesticks are getting smaller and smaller with large high wicks on the last two. The third candlestick can
            be an abandoned baby.
            
            If the next candlestick is not bearish or does not open on a bearish gap, the advance block structure is 
            invalidated
            
        '''
        if self.isBullish(c2) and self.isBullish(c3) and self.isBullish(c4) and self.isBearish(c5):
            if self.candleSize(c2) > self.candleSize(c3) > self.candleSize(c4):
                # Bearish reversal
                bearcount += 1
                tradeReasons.append('Japanese bear Advance block')

        # 15. Inverted advance block

        '''
            An inverted advance block structure is comprised of three Japanese candlesticks. All three are bearish (red). 
            The first is a large candlestick followed by two others with low wicks and small bodies. The last candlestick 
            takes the form of a hammer.
            
            An inverted advance block often occurs after a significant drop characterized by several large red Japanese 
            candlesticks.
            
            An inverted advance block is a reversal pattern, it indicates a bullish trend reversal. This reflects depletion
            of selling power and upcoming profit taking.
            
            The third candlestick is not necessarily a hammer. The important thing is that the bodies of the candlesticks
            are getting smaller and smaller with long low wicks on the last two. The third candlestick can be a abandoned
            baby bearish.
            
            If the next candlestick is not bullish or does not open on a bullish gap, the inverted blocked forward 
            structure is invalidated.
        '''
        if self.isBearish(c2) and self.isBearish(c3) and self.isBearish(c4) and self.isBullish(c5):
            if self.candleSize(c2) > self.candleSize(c3) > self.candleSize(c4):
                # bullish reversal
                bullcount += 1
                tradeReasons.append('Japanese bull Inverted Advance block')

        sellperc = 100 * (bearcount / sum([bearcount, bullcount]))
        buyperc = 100 - sellperc
        mark_trend = self.getMarketStructure()

        if sellperc > 60:
            return {'trade': 'SELL',
                    'percSell': f'{sellperc} %',
                    'percBuy': f'{buyperc} %',
                    'count': sum([bearcount, bullcount]),
                    'reasons': tradeReasons}
        elif buyperc > 60:
            return {'trade': 'BUY',
                    'percSell': f'{sellperc} %',
                    'percBuy': f'{buyperc} %',
                    'count': sum([bearcount, bullcount]),
                    'reasons': tradeReasons}
        else:
            # if mark_trend > 0.5:  # strong uptrend
            #     tradeReasons.append('Tie breaker STRONG BULL MARKET')
            #     return {'trade': 'BUY',
            #             'percSell': f'{sellperc} %',
            #             'percBuy': f'{buyperc} %',
            #             'count': sum([bearcount, bullcount]),
            #             'reasons': tradeReasons}
            # if mark_trend < -0.5:  # strong downtrend
            #     tradeReasons.append('Tie breaker STRONG BEAR MARKET')
            #     return {'trade': 'SELL',
            #             'percSell': f'{sellperc} %',
            #             'percBuy': f'{buyperc} %',
            #             'count': sum([bearcount, bullcount]),
            #             'reasons': tradeReasons}
            # else:
            return {'trade': 'NO TAKE',
                    'percSell': f'{sellperc} %',
                    'percBuy': f'{buyperc} %',
                    'count': sum([bearcount, bullcount]),
                    'reasons': tradeReasons}

    def modifySL(self, ticket, new_sl):
        pass

    def placeBuy(self):
        symbol = self.symbols[0]
        stop_loss_buy = symbol['askPrice'] - devSL
        take_profit_buy = devTP + symbol['askPrice']
        entry_buy = symbol['askPrice']
        print(take_profit_buy, entry_buy, stop_loss_buy)
        print(symbol)
        # go long ,short using threads
        buy_args = {'sl': stop_loss_buy, 'tp': take_profit_buy, 'ask_price': entry_buy,
                    'symbol': symbol['name']}
        self.goLong(sl=stop_loss_buy, tp=take_profit_buy, ask_price=entry_buy, symbol=symbol['name'])
        # self.goLong(ask_price=entry_buy, symbol=symbol['name'])
        # thread1 = threading.Thread(target=self.goLong, kwargs=buy_args)
        #
        # thread1.start()

    def placeSell(self):
        symbol = self.symbols[0]
        # sell details
        stop_loss_sell = symbol['bidPrice'] + devSL
        take_profit_sell = symbol['bidPrice'] - devTP
        entry_sell = symbol['bidPrice']
        print(take_profit_sell, entry_sell, stop_loss_sell)
        print()

        sell_args = {'sl': stop_loss_sell, 'tp': take_profit_sell, 'bid_price': entry_sell,
                     'symbol': symbol['name']}
        # thread2 = threading.Thread(target=self.goShort, kwargs=sell_args)
        # thread2.start()
        self.goShort(sl=stop_loss_sell, tp=take_profit_sell, bid_price=entry_sell, symbol=symbol['name'])


stage = 0
timerClose = False


def timerCount():
    global timerClose
    count = 0
    while True:
        if stage < 5:
            time.sleep(1)
            if count == 60:
                count = 0
            else:
                count += 1
        else:
            timerClose = True
            break

    pass


high = []
low = []
strttime = datetime.now()


def main():
    login = '31486496'
    server = "Deriv-Demo"
    password = "@Hezronbii04"
    # login = '153806097'
    # server = "Exness-MT5Trial9"
    # password = "@MT5_trial500"
    m = TraderHFT(login_=login, server_=server, password_=password, lotSize=0.55)
    m.getSymbolInfo()
    m.getTrend()
    m.closePositions()  # close all positions
    print(m.getAccountInfo())
    # m.getTrend()
    # # candles = m.prevCandles
    profit_made = 0.0
    print()
    tries = 0
    losses = 0
    wins = 0
    start_bal = m.startingBalance
    prev_bal = m.startingBalance
    print(start_bal)
    print(m.prevCandles)
    print(m.getMarketStructure())s
    for c in m.prevCandles:
        print(m.isBullish(c))
    print(m.trendRecognition())


bearishGap = [
    {'open': 1243.43, 'high': 1246.28, 'low': 1243.43, 'close': 1244.93},  # c2
    {'open': 1244.99, 'high': 1245.64, 'low': 1241.33, 'close': 1242.12},  # c3
    {'open': 1244.99, 'high': 1245.64, 'low': 1241.33, 'close': 1242.12},  # c4
    {'open': 1244.99, 'high': 1245.64, 'low': 1241.33, 'close': 1242.12},  # c5
    {'open': 1244.99, 'high': 1245.64, 'low': 1241.33, 'close': 1242.12},  # c6

]

if __name__ == '__main__':
    main()
