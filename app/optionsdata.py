# sudo pip install deribit-api
from deribit_api import RestClient
from scipy.optimize import fsolve
from scipy.stats import norm
from datetime import datetime
import pandas as pd
import math
import numpy as np


class option_data:
    """class 'option_data':
    The method 'download_option_price()' will automatically download the latest option prices
    and return the pandas data frame. The method 'generate_implied_vol()' will calculate the
    implied vol and output the data.

    But all these methods are called in __init__ of this class.
    So once you can create this class, implied vols will be calculated.
    Then you can use option_data.data['Implied_Vol'].

    If you don't know which column name to use, use method option_data.show_names()"""

    def __init__(self, interest_rate=0):
        # this is my account. Don't share it to others. But I don't have money in it :P
        self.client = RestClient('2SQfDzW1Kaf3F', 'HOG2A2HCYERM2YONRBTYEBMYRZ2ESN3K')
        self.client.index()
        self.client.account()
        self.rate = interest_rate
        # download option prices
        self.Options = self._download_option_price()
        self.Futures = self._download_future_price()
        # calculate implied vol
        self.Options['Implied_Vol'] = self.generate_implied_vol()

    def _download_option_price(self):
        data = self.client.getsummary('option')
        # convert this list of dictionaries into data frame
        data = pd.DataFrame.from_dict(data=data)
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        data['Strike'] = [int(data_tmp[i][2]) for i in range(len(data))]
        data['OptionType'] = [data_tmp[i][3] for i in range(len(data))]
        # get the time when the option is created
        data_tmp = data['created'].str.split(' ')
        data['InitialDate'] = [pd.to_datetime(data_tmp[i][0]) for i in range(len(data))]
        # convert Expiration Date
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        return data

    def _download_future_price(self):
        data = self.client.getsummary('future')
        data = pd.DataFrame.from_dict(data=data)
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        # convert Expiration Date
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        return data

    def generate_implied_vol(self):
        # Option Price, Expiration, Future price, Strike, interest rate, Option Type
        input_data = pd.Series([tuple([self.Options.loc[i, 'markPrice'],
                                (self.Options.loc[i, 'ExpirationDate'] - datetime.now()).days/365,
                                self.Options.loc[i, 'uPx'],
                                self.Options.loc[i, 'Strike'],
                                self.rate,
                                self.Options.loc[i, 'OptionType']]
                                ) for i in range(self.Options.shape[0])])

        return input_data.apply(self._calculate_implied_vol)

    def _calculate_implied_vol(self, input=(1.6, 1, 20, 20, 0.05, 'C')):
        """The input should be Option Price, Expiration, Future Price, Strike, interest rate, Option Type
        Pricing reference: https://quedex.net/edu/options """

        def Vol_fun(vol, *data_in):
            Price, ExpT, F, K, rate, Option_Type = data_in
            rate = np.float64(rate)

            d1 = (math.log(K / F) + (rate + vol ** 2 / 2) * ExpT) / vol / math.sqrt(ExpT)
            d2 = d1 - vol * math.sqrt(ExpT)
            if Option_Type == 'C':
                return K * (1 / K * norm.cdf(-d2) * math.exp(-rate * ExpT) - 1 / F * norm.cdf(-d1)) - Price
            elif Option_Type == 'P':
                return K * (1 / F * norm.cdf(d1) - 1 / K * math.exp(-rate * ExpT) * norm.cdf(d2)) - Price

        # give approximated implied vol as the initial guess
        # Price, ExpT, F, K, rate, Option_Type = input
        # approx = math.sqrt(2*math.pi/ExpT)*Price/F
        return fsolve(Vol_fun, np.array(1, dtype=float), args=input)[0]   # solve Implied Vol

    def _price_calculator(self, *data_in):
        ExpT, F, K, rate, vol, Option_Type = data_in
        rate = np.float64(rate)

        d1 = (math.log(K / F) + (rate + vol ** 2 / 2) * ExpT) / vol / math.sqrt(ExpT)
        d2 = d1 - vol * math.sqrt(ExpT)
        if Option_Type == 'C':
            return K * (1 / K * norm.cdf(-d2) * math.exp(-rate * ExpT) - 1 / F * norm.cdf(-d1))
        elif Option_Type == 'P':
            return K * (1 / F * norm.cdf(d1) - 1 / K * math.exp(-rate * ExpT) * norm.cdf(d2))