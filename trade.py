__author__ = 'guoqing,cai'
import ccxt
from pprint import pprint
import time
from numpy import NaN

counterCurrency = 'GAS'
baseCurrency = 'BTC'
tradePair = counterCurrency + '/' + baseCurrency
limit = 10  # 有些交易所需要，值的要求还有些不同，具体看交易所api比如币安默认值100
slippage = 0.001  # 滑点
ORDER_STATE_PENDING = 0
ORDER_STATE_CLOSED = 1
ORDER_STATE_CANCELED = 2
maxLoss = 0   # 利润低于0停止运行
minProfit = 0.01
minVolume = 10


def execute():
    robot = Robot()
    i = 1
    while True:
        print('第'+i+'轮对冲,已经成功'+robot.success_quantity+'%')
        robot.run()
        status = robot.stop()
        if not status:
            break
        i = i + 1


class Robot():

    def run(self):
        """运行搬砖"""
        exchanges = self.get_exchanges()
        bids = [NaN for i in exchanges]
        bidsVolum = [NaN for i in exchanges]
        asks = [NaN for i in exchanges]
        asksVolum = [NaN for i in exchanges]
        for i in range(len(exchanges)):
            try:
                mes = exchanges.__getitem__(i).fetch_order_book(tradePair, limit)
                bidPrice = mes['bids'][0][0]
                askPrice = mes['asks'][0][0]
                bids[i] = bidPrice
                bidsVolum[i] = mes['bids'][0][1]
                asks[i] = askPrice
                asksVolum[i] = mes['asks'][0][1]
            except:
                bids[i] = NaN
                asks[i] = NaN
                print('第' + (i+1) + '个交易所有错误出现')

        for m in range(len(exchanges)):
            for n in range(len(exchanges)):
                profit = bids.__getitem__(m) / asks.__getitem__(n) - 1. - self.get_fee()['sell'] - self.get_fee()['buy']
                if profit > minProfit:
                    tradeVolum = min([bidsVolum[m], asksVolum[n]])
                    if tradeVolum > minVolume:
                        self.cancel_pending_orders()  # 取消未完成的挂单
                        print("timeStamp:", time.asctime(time.localtime(time.time())))
                        print('buy ' + str(tradeVolum) + tradePair + ' at ' + m + ' 交易所and sell at ' + n + '交易所 profit: ' + str(profit))
                        exchanges.__getitem__(m).create_order(symbol=tradePair, side='buy', type='limit',amount=tradeVolum, price=bids.__getitem__(m))
                        exchanges.__getitem__(n).create_order(symbol=tradePair, side='sell', type='limit',amount=tradeVolum, price=asks.__getitem__(n))



        # highestBid = max(bids)
        # lowestAsk = min(asks)
        # sellIndex = bids.index(highestBid)
        # buyIndex = asks.index(lowestAsk)
        # profit = highestBid / lowestAsk - 1. - self.get_fee()['sell'] - self.get_fee()['buy']
        # tradeVolum = min([bidsVolum[sellIndex], asksVolum[buyIndex]])
        # # 利润大于手续费就成交，容量大于交易所最小交易量，目前没有接口，只有看看做那个交易对，然后手动创建一个小订单看看提示的最小量
        # if profit > minProfit and tradeVolum > minVolume:
        #     self.cancel_pending_orders()  # 取消未完成的挂单
        #     print("timeStamp:", time.asctime(time.localtime(time.time())))
        #     print('buy ' + str(tradeVolum) + tradePair + ' at ' + buyIndex + ' 交易所and sell at ' + sellIndex + '交易所 profit: ' + str(profit))
        #     exchanges.__getitem__(buyIndex).create_order(symbol=tradePair, side='buy', type='limit',amount=tradeVolum, price=lowestAsk)
        #     exchanges.__getitem__(sellIndex).create_order(symbol=tradePair, side='sell', type='limit',amount=tradeVolum, price=highestBid)





    def stop(self, init_ststus):
        """检测是否停止搬砖"""
        account_info = self.getAccountInfo()
        self.printAccountInfo(account_info)
        profit = account_info['total_balance'] - init_ststus['total_balance']
        if profit < self.maxLoss:
            return False
        for data in account_info['details']:
            if data['account_info']['Balance'] < self.minBlance:
                Log('基础货币小于最低值,停止搬运')
                return False
            if data['account_info']['Stocks'] < self.minSell:
                Log('要搬砖的货币小于最低值,停止搬运')
                return False
            if data['account_info']['FrozenBalance'] > 0 or data['account_info']['FrozenStocks'] > 0:
                Log('%s有货币被冻结' % (data['exchange_name']))
        self.balanceCurrency(account_info, init_ststus)

        return True

    def get_exchanges(self):
        exchange1 = ccxt.huobipro({'apiKey': 'xxxxx', 'secret': 'xxxxx'})
        exchange2 = ccxt.binance({'apiKey': 'xxxxx', 'secret': 'xxxxx'})
        exchange3 = ccxt.okex({'apiKey': 'xxxxx', 'secret': 'xxxxx'})
        exchanges = [exchange1, exchange2, exchange3]
        return exchanges

    def get_fee(self):
        return {'sell': 0.2 / 100, 'buy': 0.2 / 100}

    def cancel_pending_orders(self):
        """取消所有未完成挂单"""
        for exchange in self.get_exchanges():
            orders = exchange.fetch_open_orders(symbol=tradePair)
            if len(orders) == 0:
                continue
            for order in orders:
                while True:
                    exchange.cancel_order(order.Id)
                    status = exchange.fetch_order_status(order.Id)
                    if status == ORDER_STATE_CLOSED:
                        break
                    if status == ORDER_STATE_CANCELED:
                        break


