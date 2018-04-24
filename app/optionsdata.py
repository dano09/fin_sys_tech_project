# sudo pip install deribit-api
from deribit_api import RestClient
from scipy.optimize import fsolve
import scipy.interpolate as it
from scipy.optimize import curve_fit
from scipy.stats import norm
from datetime import datetime
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
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

    def __init__(self, interest_rate=0, K_range=(0, math.inf)):
        # this is my account. Don't share it to others. But I don't have money in it :P
        self.client = RestClient('2SQfDzW1Kaf3F', 'HOG2A2HCYERM2YONRBTYEBMYRZ2ESN3K')
        self.client.index()
        self.client.account()
        self.rate = interest_rate
        # download option prices
        min_K, max_K = K_range
        self.data = self._download_option_price(min_K, max_K)
        # calculate implied vol
        self.data['Implied_Vol'] = self.generate_implied_vol()

    def _download_option_price(self, min_K, max_K):
        data = self.client.getsummary('option')
        # convert this list of dictionaries into data frame
        data = pd.DataFrame.from_dict(data=data)
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        data['Strike'] = [int(data_tmp[i][2]) for i in range(len(data))]
        data['OptionType'] = [data_tmp[i][3] for i in range(len(data))]
        # moneyness
        data['Moneyness'] = np.log(data['uPx']/data['Strike'])
        # get the time when the option is created
        data_tmp = data['created'].str.split(' ')
        data['InitialDate'] = [pd.to_datetime(data_tmp[i][0]) for i in range(len(data))]
        # convert Expiration Date
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        now = datetime.now()
        data['Texp'] = [(data.loc[i, 'ExpirationDate'] - now).total_seconds()/365/24/60/60 \
                        for i in range(data.shape[0])]
        # filter the strike with proper range
        condition = np.array([min_K <= data.loc[i, 'Strike'] <= max_K for i in range(data.shape[0])])
        data = data.loc[np.where(condition)[0],:]
        data = data.reindex(index=range(data.shape[0]))
        return data

    def generate_implied_vol(self):
        # Option Price, Expiration, Future price, Strike, interest rate, Option Type
        input_data = pd.Series([tuple([self.data.loc[i, 'markPrice'],
                                self.data.loc[i, 'Texp'],
                                self.data.loc[i, 'uPx'],
                                self.data.loc[i, 'Strike'],
                                self.rate,
                                self.data.loc[i, 'OptionType']]
                                ) for i in range(self.data.shape[0])])

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

        result = fsolve(Vol_fun, np.array(1, dtype=float), args=input,
                        full_output=True)   # solve Implied Vol

        # output NA is the solution was not found
        if result[2]==0:
            return None
        else:
            return result[0][0]

    def _price_calculator(self, *data_in):
        """This is a calculator only for external use; won't be called in the class"""
        ExpT, F, K, rate, vol, Option_Type = data_in
        rate = np.float64(rate)
        d1 = (math.log(K / F) + (rate + vol ** 2 / 2) * ExpT) / vol / math.sqrt(ExpT)
        d2 = d1 - vol * math.sqrt(ExpT)
        if Option_Type == 'C':
            return K * (1 / K * norm.cdf(-d2) * math.exp(-rate * ExpT) - 1 / F * norm.cdf(-d1))
        elif Option_Type == 'P':
            return K * (1 / F * norm.cdf(d1) - 1 / K * math.exp(-rate * ExpT) * norm.cdf(d2))

    def plot_iv(self, option_type='A'):
        """Plot the implied vol surface"""
        subset = self.data
        subset1 = subset.loc[subset['OptionType'] == 'C', :]
        subset2 = subset.loc[subset['OptionType'] == 'P', :]
        ax = plt.axes(projection='3d')
        ax.scatter(subset1['Strike'], subset1['Texp'], subset1['Implied_Vol'], c='r')
        ax.scatter(subset2['Strike'], subset2['Texp'], subset2['Implied_Vol'], c='b')
        ax.set_zlim(np.min(subset['Implied_Vol']) - 0.1, np.max(subset['Implied_Vol']) + 0.1)
        ax.set_title('Implied Vol of Call and Put')
        ax.set_xlabel('Strike')
        ax.set_ylabel('Maturity')
        ax.set_zlabel('Implied Vol')
        plt.show()

    def output_iv_matrix(self, option_type='A', size=(50,50)):
        """Output the fitted implied vol matrix"""
        # get subset
        # consider specified option type
        if option_type == 'C' or option_type=='P':
            subset = self.data.loc[self.data['OptionType'] == option_type, :]
        # consider subset with moneyness >= 0 for call and moneyness <0 for put
        else:
            condition = [(self.data.loc[i, 'Moneyness'] >= 0 and self.data.loc[i, 'OptionType'] == 'C') or
                         (self.data.loc[i, 'Moneyness'] < 0 and self.data.loc[i, 'OptionType'] == 'P')
                         for i in range(self.data.shape[0])]
            subset = self.data.loc[np.where(condition)[0], :]

        # interpolate the implied vol for every maturity====================
        # interpolation function:
        def iv_curve(k, a, b, rho, m, sigma):
            return a+b*(rho*(k-m)+np.sqrt((k-m)**2+sigma**2))
        # how many maturities
        time = np.unique(subset['Texp'])
        N_time = time.shape[0]

        # initiate solution
        fitted_x = np.array([])
        fitted_y = np.array([])
        fitted_z = np.array([])
        size_x, size_y = size   # size of the matrix
        strikeline = np.linspace(np.min(subset['Moneyness']), np.max(subset['Moneyness']), size_x)
        timeline = np.linspace(np.min(subset['Texp']), np.max(subset['Texp']), size_y)

        # interpolate every maturity
        for i in range(N_time):
            subset_sub = subset.loc[subset['Texp'] == time[i],:]
            popt, pcov = curve_fit(iv_curve, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values)
            fitted_x = np.append(fitted_x, strikeline)
            fitted_y = np.append(fitted_y, np.ones(size_y)*time[i])
            fitted_z = np.append(fitted_z, iv_curve(strikeline, *popt))

        # use spline to get the full surface matrix
        tck = it.bisplrep(fitted_x, fitted_y, fitted_z)
        Z = it.bisplev(strikeline, timeline, tck)
        return strikeline, timeline, Z

    def plot_iv_surface(self,  option_type='A', size=(50,50)):
        # get subset
        # consider specified option type
        if option_type == 'C' or option_type == 'P':
            subset = self.data.loc[self.data['OptionType'] == option_type, :]
        # consider subset with moneyness >= 0 for call and moneyness <0 for put
        else:
            condition = [(self.data.loc[i, 'Moneyness'] >= 0 and self.data.loc[i, 'OptionType'] == 'C') or
                         (self.data.loc[i, 'Moneyness'] < 0 and self.data.loc[i, 'OptionType'] == 'P')
                         for i in range(self.data.shape[0])]
            subset = self.data.loc[np.where(condition)[0], :]

        # plot result
        x, y, Z = self.output_iv_matrix(option_type, size)
        X, Y = np.meshgrid(x, y)
        ax = plt.axes(projection='3d')
        ax.plot_surface(X, Y, Z, rstride=1, cstride=1,
                        cmap='viridis', edgecolor='none')
        ax.scatter(subset['Moneyness'], subset['Texp'], subset['Implied_Vol'])
        ax.set_zlim(np.min(subset['Implied_Vol']) - 0.1, np.max(subset['Implied_Vol']) + 0.1)
        ax.set_title('Estimated Implied Vol Surface')
        ax.set_xlabel('Moneyness')
        ax.set_ylabel('Maturity')
        ax.set_zlabel('Implied Vol')
        plt.show()

    def plot_fitted(self, option_type='A', size=(50,50)):
        """Plot the implied vol surface"""
        # get subset
        # consider specified option type
        if option_type == 'C' or option_type=='P':
            subset = self.data.loc[self.data['OptionType'] == option_type, :]
        # consider subset with moneyness >= 0 for call and moneyness <0 for put
        else:
            condition = [(self.data.loc[i, 'Moneyness'] >= 0 and self.data.loc[i, 'OptionType'] == 'C') or
                         (self.data.loc[i, 'Moneyness'] < 0 and self.data.loc[i, 'OptionType'] == 'P')
                         for i in range(self.data.shape[0])]
            subset = self.data.loc[np.where(condition)[0], :]

        # interpolate the implied vol for every maturity====================
        # interpolation function:
        def iv_curve(k, a, b, rho, m, sigma):
            return a+b*(rho*(k-m)+np.sqrt((k-m)**2+sigma**2))
        # how many maturities
        time = np.unique(subset['Texp'])
        N_time = time.shape[0]

        # initiate solution
        size_x, size_y = size
        strikeline = np.linspace(np.min(subset['Moneyness']), np.max(subset['Moneyness']), size_x)
        timeline = np.linspace(np.min(subset['Texp']), np.max(subset['Texp']), size_y)

        # interpolate every maturity
        ax = plt.axes(projection='3d')
        for i in range(N_time):
            subset_sub = subset.loc[subset['Texp'] == time[i],:]
            popt, pcov = curve_fit(iv_curve, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values)
            fitted_x = strikeline
            fitted_y = np.ones(size_y)*time[i]
            fitted_z = iv_curve(strikeline, *popt)

            ax.plot(xs=fitted_x, ys=fitted_y, zs=fitted_z)
        ax.scatter(subset['Moneyness'], subset['Texp'], subset['Implied_Vol'])
        ax.set_zlim(np.min(subset['Implied_Vol']) - 0.1, np.max(subset['Implied_Vol']) + 0.1)
        ax.set_title('Fitted Implied Vol')
        ax.set_xlabel('Moneyness')
        ax.set_ylabel('Maturity')
        ax.set_zlabel('Implied Vol')
        plt.show()


