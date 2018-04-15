import requests
import pandas as pd

class Dataservices:

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


ds = Dataservices()

data = ds.get_bitcoin_data('2010-07-18', '2018-04-15')
