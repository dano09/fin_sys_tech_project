import requests
import pandas as pd

class Dataservices:
    """ Used to pull data from cryptocurrency data from APIs"""

    # There is a limit on how many calls can be made with free API Token
    API_TOKEN = '72FBF785-4085-497B-9471-9E391860AD48'

    def get_bitcoin_data(self, start_date=None, end_date=None):
        """
        Retrieve historic bitcoin data from Coindesk. Assume USD CCY
        :param start_date: string in format YYYY-MM-DD
        :param end_date: string in format YYYY-MM-DD
        :return: timestamp of call and bitcoin data (dataframe)
        """
        if start_date < '2010-07-17':
            raise ValueError('Data for Bitcoin starts after July 17th 2010')

        # Call Rest API to get Historic Bitcoin Data based on start and end date
        url_base = 'https://api.coindesk.com/v1/bpi/historical/close.json'
        start_date = '?start={}'.format(start_date)
        end_date = '&end={}'.format(end_date)
        r = requests.get(url_base + start_date + end_date)

        # Convert data into dataframe
        data_in_json = r.json()
        bp = data_in_json['bpi']
        timestamp = data_in_json['time']
        s = pd.Series(bp, name='Close Price')
        s.index.name = 'Date'
        s.reset_index()
        bitcoin_df = s.to_frame()
        bitcoin_df = bitcoin_df.reset_index(level=['Date'])

        return timestamp, bitcoin_df

    def get_coinapi_symbols(self):
        """ Retrieves all symbols from the .csv file. If the file cannot be found it will call the API"""
        call_api_flag = False

        # Get Symbols from Saved .csv
        symbols = pd.read_csv('C:/Users/Justin/PycharmProjects/fin_sys_tech_project/data/coinAPI_symbols.csv')
        # symbols = pd.read_csv('/home/ben/PycharmProjects/fin_sys_tech_project/data/coinAPI_symbols.csv')

        if call_api_flag:
            # Get Symbols from Website (should only have to do once)
            url_symbols = 'https://rest.coinapi.io/v1/symbols'
            headers = {'X-CoinAPI-Key': '72FBF785-4085-497B-9471-9E391860AD48'}
            response = requests.get(url_symbols, headers=headers)
            symbol_data = response.json()

            # Convert list of dictonary objects into dataframe
            df = pd.DataFrame(symbol_data)

            df.to_csv('coinAPI_symbols.csv')

        return symbols

    def get_exchanges(self):
        """
        Get and return the list of exchanges from the API
        :return: Numpy Array
        """
        coin_api_symbols = self.get_coinapi_symbols()
        exchanges = coin_api_symbols.exchange_id.unique()
        return exchanges

    def get_symbols_by_exchange_and_fiat_currencies(self, exchange_id, fiat_ccy_id):
        """
        Return API Crypto Symbols for a specific Exchange and Fiat Currency.
        Simply look into data/coinAPI_symbols.csv for more info
        :param exchange_id: String (Example: COINBASE)
        :param fiat_ccy_id: String (Example: USD)
        :return: Dataframe containing symbol information on all cryptocurrencies filtered by exchange and fiat currency
        """
        coin_api_symbols = self.get_coinapi_symbols()
        return coin_api_symbols.loc[(coin_api_symbols['exchange_id'] == exchange_id)
                                    & (coin_api_symbols['asset_id_quote'] == fiat_ccy_id)]

    def get_symbols_by_exchange_and_fiat_and_crypto(self, exchange_id, fiat_ccy_id, crypto_ccy_id):
        """
        Return API Crypto Symbols for a specific Exchange, Fiat Currency and Crypto Currency.
        :param exchange_id: String (Example: COINBASE)
        :param fiat_ccy_id: String (Example: USD)
        :param crypto_ccy_id: String (Example: BTC)
        :return: Dataframe containing symbol information on all cryptocurrencies filtered by exchange, fiat currency
                 and cryptocurrency
        """
        coin_api_symbols = self.get_coinapi_symbols()
        return coin_api_symbols.loc[(coin_api_symbols['exchange_id'] == exchange_id)
                                    & (coin_api_symbols['asset_id_quote'] == fiat_ccy_id)
                                    & (coin_api_symbols['asset_id_base'] == crypto_ccy_id)]

    def get_historic_ohlcv_data(self, crypto_symbol_id, trade_start, trade_end):
        """
        Calls API to get price data based on the parameters
        :param crypto_symbol_id: String (EXAMPLE: COINBASE_SPOT_BTC_USD)
                Format: EXCHANGE_TRADETYPE_CRYPTO_FIAT
        :param trade_start: String (Example: 2018-04-09T00:00:00)
                Format: YYYY-MM-DDTHH:mm:ss
        :param trade_end:  Same as trade_start
        :return: Dataframe of Open, High, Low, Closed, and Volume Data based on parameters
        """
        url_symbols = 'https://rest.coinapi.io/v1/ohlcv/' + crypto_symbol_id + '/history?period_id=1DAY&time_start=' + trade_start + '&time_end=' + trade_end
        headers = {'X-CoinAPI-Key': '72FBF785-4085-497B-9471-9E391860AD48'}
        response = requests.get(url_symbols, headers=headers)
        return pd.DataFrame(response.json())

    def get_symbols_by_crypto_id(self, crypto_ccy_id):
        """
        Return API Crypto Symbols for all exchanges/currencies based on crypto id
        :param crypto_ccy_id: String (Example: BTC)
        :return: Dataframe containing symbol information on all cryptocurrencies of the crypto_id for each exchange/fiat
        """
        coin_api_symbols = self.get_coinapi_symbols()
        return coin_api_symbols.loc[coin_api_symbols['asset_id_base'] == crypto_ccy_id]

    def get_symbols_by_fiat_currency(self, fiat_ccy_id):
        """
        Return API Crypto Symbols for all exchanges/currencies based on crypto id
        :param fiat_ccy_id: String (Example: USD)
        :return: Dataframe containing symbol information on all crypto currencies filtered by exchange and fiat currency
        """
        coin_api_symbols = self.get_coinapi_symbols()
        return coin_api_symbols.loc[coin_api_symbols['asset_id_quote'] == fiat_ccy_id]

