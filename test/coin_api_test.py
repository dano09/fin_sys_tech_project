from app.dataservices import Dataservices


def get_crypto_price_data_demo(ds):
    coin_api_symbols = ds.get_coinapi_symbols()
    COINBASE_INDEX = 5  # known by looking at the data

    # Pick an Exchange
    exchanges = ds.get_exchanges()

    # Sample, choose coinbase exchange
    coinbase_data = exchanges[COINBASE_INDEX]

    # Gets all symbols based on exchange COINBASE
    coinbase_data = coin_api_symbols.loc[coin_api_symbols['exchange_id'] == 'COINBASE']

    # Gets all symbols based on exchange COINBASE and currency USD
    coinbase_usd_crypto_symbols = ds.get_symbols_by_exchange_and_fiat_currencies('COINBASE', 'USD')

    coinbase_usd_eth_symbols = ds.get_symbols_by_exchange_and_fiat_and_crypto('COINBASE', 'USD', 'ETH')

    coinbase_usd_eth_id = coinbase_usd_eth_symbols['symbol_id'].values[0]
    coinbase_usd_eth_start_date = coinbase_usd_eth_symbols['data_start'].values[0] + 'T00:00:00'
    coinbase_usd_eth_end_date = coinbase_usd_eth_symbols['data_end'].values[0] + 'T00:00:00'

    # Get price data for USD / Ethereum from Coinbase using coinapi
    eth_ohlcv_data = ds.get_historic_ohlcv_data(coinbase_usd_eth_id, coinbase_usd_eth_start_date, coinbase_usd_eth_end_date)


ds = Dataservices()
test = get_crypto_price_data_demo(ds)

