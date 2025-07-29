#!/bin/sh
# 统计套利策略(配对交易)
#nohup python3 -u Pairs_trading_strategy.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u store_binance_swap.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u balance_position_warning.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u store_redis.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u store_redis.py >/dev/null 2>error.log  2>&1 &
# 币安资金费率套利策略
#nohup python3 -u store_binance_spot.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u store_binance_swap.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u store_kline_sign.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u MARTIN_trend_strategy.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u FUNDING_strategy.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u balance_position_warning.py >/dev/null 2>error.log  2>&1 &
#nohup python3 -u update_strategy.py >/dev/null 2>error.log  2>&1 &
# 趋势马丁策略
nohup python3 -u store_binance_swap.py >/dev/null 2>error.log  2>&1 &
nohup python3 -u BUXI_MARTIN_MAIN.py >/dev/null 2>error.log  2>&1 &

