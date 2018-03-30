# sudo pip install deribit-api
from deribit_api import RestClient
from scipy.optimize import fsolve
from scipy.stats import norm
import pandas as pd
import math
import numpy as np


class option_data:
    def __init__(self, interest_rate=0.005):
        # this is my account. Don't share it to others. But I don't have money in it :P
        self.client = RestClient('2SQfDzW1Kaf3F', 'HOG2A2HCYERM2YONRBTYEBMYRZ2ESN3K')
        self.client.index()
        self.client.account()
        self.rate = interest_rate

    def download_option_price(self):
        data = self.client.getsummary('option')
        # convert this list of dictionaries into data frame
        data = pd.DataFrame.from_dict(data=data)
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        data['Strike'] = [data_tmp[i][2] for i in range(len(data))]
        data['OptionType'] = [data_tmp[i][3] for i in range(len(data))]
        # get the time when the option is created
        data_tmp = data['created'].str.split(' ')
        data['InitialDate'] = [pd.to_datetime(data_tmp[i][0]) for i in range(len(data))]
        # convert Expiration Date
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        self.data = data

    def generate_implied_vol(self):
        # Option Price, Expiration, Price at that time, Strike, interest rate, Option Type
        input_data = pd.Series([(self.data.loc[:, 'markPrice'],
                                (self.data.loc[i, 'ExpirationDate'] - self.data.loc[i, 'InitialDate']).days / 365,
                                self.data.loc[i, 'uPx'],
                                self.data.loc[i, 'Strike'],
                                self.rate,
                                self.data.loc[i, 'OptionType']
                                ) for i in range(self.data.shape[0])])

        return input_data.apply(self._calculate_implied_vol)



    def _calculate_implied_vol(self, input=(1.6, 1, 20, 20, 0.05, 'C')):
        """The input should be Option Price, Expiration, Current Price, Strike, interest rate, Option Type"""
        def Vol_fun(vol, *data_in):
            Price, ExpT, S, K, rate, Option_Type = data_in
            d1 = (math.log(S / K) + (rate + vol ** 2 / 2) * ExpT) / vol / math.sqrt(ExpT)
            d2 = d1 - vol * math.sqrt(ExpT)
            if Option_Type == 'C':
                return S * norm.cdf(d1) - K * math.exp(-rate * ExpT) * norm.cdf(d2) - Price
            elif Option_Type == 'P':
                return K * math.exp(-rate * ExpT) * norm.cdf(-d2) - S * norm.cdf(-d1) - Price

        return fsolve(Vol_fun, np.array([0.2]), args=input)[0]   # initial guess is 0.2




