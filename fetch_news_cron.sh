#!/bin/bash
# Cron script to fetch news automatically
# Add to crontab with: */10 * * * * /Users/macbook/zenithedge_trading_hub/fetch_news_cron.sh

cd /Users/macbook/zenithedge_trading_hub
/Library/Developer/CommandLineTools/usr/bin/python3 manage.py fetch_news >> /tmp/zennews_fetch.log 2>&1
