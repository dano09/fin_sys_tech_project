# sudo pip install deribit-api
from deribit_api import RestClient
from scipy.optimize import fsolve
from scipy.optimize import OptimizeWarning
import itertools
from scipy.optimize import curve_fit
from scipy.stats import norm
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import math
import numpy as np
import warnings
import plotly.offline as py
import plotly.graph_objs as go
from os import getcwd


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
        self.rate = interest_rate
        self.index = self.client.index()['btc']
        # download option prices
        min_K, max_K = K_range
        data_tmp = self._download_option_price(min_K, max_K)
        data_on_index = data_tmp.loc[data_tmp['uIx'] == 'index_price', :]
        data = data_tmp.loc[data_tmp['uIx'] != 'index_price', :]
        # reindex
        data = data.dropna(axis=0)
        data_on_index = data_on_index.dropna(axis=0)
        data = data.reset_index()
        data_on_index = data_on_index.reset_index()
        # save data
        self.data = data
        self.data_on_index = data_on_index
        # calculate implied vol
        self.data['Implied_Vol'] = self.generate_implied_vol()
        self.future_data = self._download_future_price()

    def _download_option_price(self, min_K, max_K):
        data = self.client.getsummary('option')
        # convert this list of dictionaries into data frame
        data = pd.DataFrame.from_dict(data=data)
        data = data.iloc[range(len(data)-1),]
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        data['Strike'] = [int(data_tmp[i][2]) for i in range(len(data))]
        data['OptionType'] = [data_tmp[i][3] for i in range(len(data))]
        # moneyness
        data['Moneyness'] = -np.log(data['uPx']/data['Strike'])   # the moneyness should be reversed to normal option
        # get the time when the option is created
        data_tmp = data['created'].str.split(' ')
        data['InitialDate'] = [pd.to_datetime(data_tmp[i][0]) for i in range(len(data))]
        # convert Expiration Date
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        now = datetime.now()
        self.now = now
        data['Texp'] = [(data.loc[i, 'ExpirationDate'] - now).total_seconds()/365/24/60/60 \
                        for i in range(data.shape[0])]
        # filter the strike with proper range
        condition = np.array([min_K*(1 - np.sqrt(data.loc[i, 'Texp']))
                              <= data.loc[i, 'Strike'] <=
                              max_K*( 1+ np.sqrt(data.loc[i, 'Texp']))
                              for i in range(data.shape[0])])
        data = data.loc[np.where(condition)[0],:]
        data = data.reindex(index=range(data.shape[0]))
        return data

    def _download_future_price(self):
        data = self.client.getsummary('future')
        # convert this list of dictionaries into data frame
        data = pd.DataFrame.from_dict(data=data)
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        data['Texp'] = [(data.loc[i, 'ExpirationDate'] - self.now).total_seconds() / 365 / 24 / 60 / 60 \
                        for i in range(data.shape[0])]
        return data

    # ======================================================================Calculator methods

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
        """This is a calculator only for external use; won't be called in the class
        output is number of bitcoins as expected payoff"""
        ExpT, F, K, rate, vol, Option_Type = data_in
        rate = np.float64(rate)
        d1 = (np.log(K / F) + (rate + vol ** 2 / 2) * ExpT) / vol / np.sqrt(ExpT)
        d2 = d1 - vol * np.sqrt(ExpT)
        if Option_Type == 'C':
            return K * (1 / K * norm.cdf(-d2) * math.exp(-rate * ExpT) - 1 / F * norm.cdf(-d1))
        elif Option_Type == 'P':
            return K * (1 / F * norm.cdf(d1) - 1 / K * math.exp(-rate * ExpT) * norm.cdf(d2))

    def fitting(self, x_in, option_type='A', ):
        """Fit the implied vol for each maturity date and output the fitting in vector form"""
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

        # interpolate the implied vol for every maturity====================
        # interpolation function:
        # This function do not work well
        def iv_curve(k, a, b, rho, m, sigma):
            return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))
        def iv_curve2(k, a, b, m):
            return np.abs(a*(k-b))+m
        # how many maturities
        time = np.unique(subset['Texp'])
        N_time = time.shape[0]

        # initiate solution
        fitted_x = np.array([])
        fitted_y = np.array([])
        fitted_z = np.array([])

        # interpolate every maturity
        # using correct equation:
        # for i in range(N_time):
        #     subset_sub = subset.loc[subset['Texp'] == time[i],:]
        #     popt, pcov = curve_fit(iv_curve, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values)
        #     fitted_x = np.append(fitted_x, x_in)
        #     fitted_y = np.append(fitted_y, np.ones(len(x_in))*time[i])
        #     fitted_z = np.append(fitted_z, iv_curve(x_in, *popt))

        subset_sub = subset.loc[subset['Texp'] == time[0],:]
        method = 'lm'
        # change the optimization warning to exception
        warnings.simplefilter("error", OptimizeWarning)
        try:   # try normal fitting
            popt, pcov = curve_fit(iv_curve, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values,
                                   method=method)
            value = iv_curve(x_in, *popt)
        except (RuntimeError, OptimizeWarning) as error:   # if no optimal parameters found:
            popt, pcov = curve_fit(iv_curve2, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values,
                                   method=method)
            value = iv_curve2(x_in, *popt)
        #     popt = np.polyfit(subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values, 2)
        #     foo = np.poly1d(popt)
        #     value = foo(x_in)
        try:
            length = len(x_in)
        except TypeError:
            length = 1
        fitted_x = np.append(fitted_x, x_in)
        fitted_y = np.append(fitted_y, np.ones(length)*time[0])
        fitted_z = np.append(fitted_z, value)
        # using polynomial
        for i in range(1, N_time):
            subset_sub = subset.loc[subset['Texp'] == time[i], :]
            try:
                popt, pcov = curve_fit(iv_curve, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values,
                                       method=method)
                value = iv_curve(x_in, *popt)
            except (RuntimeError, OptimizeWarning) as error:
                popt, pcov = curve_fit(iv_curve2, subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values,
                                       method=method)
                value = iv_curve2(x_in, *popt)
                # popt = np.polyfit(subset_sub['Moneyness'].values, subset_sub['Implied_Vol'].values, 2)
                # foo = np.poly1d(popt)
                # value = foo(x_in)
            fitted_x = np.append(fitted_x, x_in)
            fitted_y = np.append(fitted_y, np.ones(length) * time[i])
            fitted_z = np.append(fitted_z, value)
        return fitted_x, fitted_y, fitted_z

    def iv_interpolation(self, ExpDate, strike, ExpT, option_type='A'):
        """Output the linear interpolated implied vol by selection"""
        # moneyness of this strike
        F = self.future_data.loc[self.future_data['ExpirationDate']==ExpDate, 'markPrice'].values[0]
        moneyness =  np.array(-np.log(F/strike))
        _, fitted_y, fitted_z = self.fitting(moneyness, option_type)
        return fitted_z[fitted_y == ExpT][0]

    def PnL(self, strike, ExpT_id, option_size = 1, option_type='C'):
        """output the PnL vector at the maturity using hedge ratio
        strike: any user defined strike price. must be integers
        ExpT_id: which expiration date to use. e.g. 0 means the first future expiration
        option_size: the size of the contract
        option_type
        price_range: used for the plotting purpose"""
        ExpT = self.get_date_annual()[ExpT_id]
        ExpDate = self.get_date()[ExpT_id]
        imp_vol = self.iv_interpolation(ExpDate, strike, ExpT)
        # get the future price on this date
        F = self.future_data.loc[self.future_data['Texp'] == ExpT, 'markPrice'].values[0]
        FT = np.linspace(100, F*2, 20000)
        # calculate the price of the option in dollars
        price =  self.index* self._price_calculator(ExpT, F, strike, self.rate, imp_vol, option_type)
        #calculate PnL
        if option_type == 'C':
            PnL_position = F - FT       # short position
            PnL_option = option_size * (np.array([np.max([0, 1 / strike - 1 / i]) for i in FT]) * strike * FT - price)
        elif option_type == 'P':
            PnL_position = FT - F      # long position
            PnL_option = option_size * (np.array([np.max([0, 1 / i - 1 / strike]) for i in FT]) * strike * FT - price)
        PnL = PnL_position + PnL_option
        return pd.DataFrame(np.column_stack((FT, PnL, PnL_option, PnL_position)),
                            columns=['FT', 'PnL', 'PnL_option', 'PnL_position'])

    def prob_of_make_money_option(self, strike, ExpT_id, option_type='C'):
        """calculate the probability of making money at maturity according to the implied vol
        strike: any user defined strike price. must be integers
        ExpT_id: which expiration date to use. e.g. 0 means the first future expiration
        """
        ExpT = self.get_date_annual()[ExpT_id]
        ExpDate = self.get_date()[ExpT_id]
        imp_vol = self.iv_interpolation(ExpDate, strike, ExpT, option_type)
        # get the future price on this date
        F = self.future_data.loc[self.future_data['Texp']==ExpT, 'markPrice']
        # if there is no data, raise exception
        if len(F) == 0:
            print('This Date Has No Future Data.')
            return 0
        F = F.values[0]
        # calculate the price of the option in dollars
        price = self.index * self._price_calculator(ExpT, F, strike, self.rate, imp_vol, option_type)

        if option_type == 'C':
            d2 = (math.log(F/ (strike+ price)) +(self.rate - imp_vol ** 2 / 2) * ExpT) / imp_vol / math.sqrt(ExpT)
            return norm.cdf(d2)
        elif option_type == 'P':
            d2 = (math.log(F / (strike - price)) + (self.rate - imp_vol ** 2 / 2) * ExpT) / imp_vol / math.sqrt(ExpT)
            return norm.cdf(-d2)

    def prob_of_make_money(self, strike, ExpT_id, option_size = 1, option_type='C'):
        """calculate the probability of making money at maturity according to the implied vol
        strike: any user defined strike price. must be integers
        ExpT_id: which expiration date to use. e.g. 0 means the first future expiration
        """
        ExpT = self.get_date_annual()[ExpT_id]
        ExpDate = self.get_date()[ExpT_id]
        # get the future price on this date
        F = self.future_data.loc[self.future_data['Texp']==ExpT, 'markPrice']
        # if there is no data, raise exception
        if len(F) == 0:
            print('This Date Has No Future Data.')
            return 0
        F = F.values[0]
        # calculate PnL and take the positive integration
        result = self.PnL(strike, ExpT_id, option_size, option_type)
        condition_u = [result.loc[i, 'PnL']>=0 for i in range(result.shape[0])]
        condition_index = np.where(condition_u)[0]

        # integrate the probability
        PDF_s = self._generate_prob_distribution(ExpT_id)
        Prob = np.sum(PDF_s.loc[condition_index, 'PDF'])

        return Prob

    def _generate_prob_distribution(self, ExpT_id):
        """Calculate the probability distribution using the implied vol
        reference:
        https://quant.stackexchange.com/questions/1621/how-to-derive-the-implied-probability-distribution-from-b-s-volatilities"""
        ExpT = self.get_date_annual()[ExpT_id]
        ExpDate = self.get_date()[ExpT_id]
        # get the future price on this date
        F = self.future_data.loc[self.future_data['Texp'] == ExpT, 'markPrice'].values[0]
        strike = np.linspace(100, F*2, 20000)
        imp_vol = self.iv_interpolation(ExpDate, strike, ExpT)
        price_data = self._price_calculator(ExpT, F, strike, self.rate, imp_vol, 'C')
        # calculate the second order derivative partial2 C/ partial K2
        dK2 = np.min(np.diff(strike))**2
        distribution = np.exp(self.rate*ExpT)*np.diff(price_data, n=2)/dK2
        # normalize the distribution
        distribution = distribution/sum(distribution)
        return pd.DataFrame(np.column_stack((strike[1:-1], distribution)),columns=['Strike', 'PDF'])


    # =====================================================================data output methods

    def get_date(self, option_type='C'):
        """Get the calendar dates of maturity"""
        # get subset
        # consider specified option type
        if option_type == 'C' or option_type == 'P':
            subset = self.data.loc[self.data['OptionType'] == option_type, :]
        # consider subset with moneyness >= 0 for call and moneyness <0 for put
        else:
            condition = [(self.data.loc[i, 'Moneyness'] >= 0 and self.data.loc[i, 'OptionType'] == 'C')
                         or
                         (self.data.loc[i, 'Moneyness'] < 0 and self.data.loc[i, 'OptionType'] == 'P')
                         for i in range(self.data.shape[0])]
            subset = self.data.loc[np.where(condition)[0], :]

        return np.unique(subset['ExpirationDate'])

    def get_date_annual(self, option_type='C'):
        """get the annualized time"""
        # get subset
        # consider specified option type
        if option_type == 'C' or option_type == 'P':
            subset = self.data.loc[self.data['OptionType'] == option_type, :]
        # consider subset with moneyness >= 0 for call and moneyness <0 for put
        else:
            condition = [(self.data.loc[i, 'Moneyness'] >= 0 and self.data.loc[i, 'OptionType'] == 'C')
                         or
                         (self.data.loc[i, 'Moneyness'] < 0 and self.data.loc[i, 'OptionType'] == 'P')
                         for i in range(self.data.shape[0])]
            subset = self.data.loc[np.where(condition)[0], :]

        return np.unique(subset['Texp'])

    def get_strike(self, option_type='C'):
        """return the strike prices of an option type"""
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

        return np.unique(subset['Strike'])

    def output_iv_matrix(self, option_type='A', size=(50,50)):
        """Output the fitted implied vol matrix"""
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
        # initiate x y axis
        size_x, size_y = size
        moneyness = np.linspace(np.min(subset['Moneyness']), np.max(subset['Moneyness']), size_x)
        timeline = np.linspace(np.min(subset['Texp']), np.max(subset['Texp']), size_y)

        fitted_x, fitted_y, fitted_z= self.fitting(moneyness, option_type)

        def polyfit2d(x, y, z, order=4):
            ncols = (order + 1) ** 2
            G = np.zeros((x.size, ncols))
            ij = itertools.product(range(order + 1), range(order + 1))
            for k, (i, j) in enumerate(ij):
                G[:, k] = x ** i * y ** j
            m, _, _, _ = np.linalg.lstsq(G, z)
            return m

        def polyval2d(x, y, m):
            order = int(np.sqrt(len(m))) - 1
            ij = itertools.product(range(order + 1), range(order + 1))
            z = np.zeros_like(x)
            for a, (i, j) in zip(m, ij):
                z += a * x ** i * y ** j
            return z

        # use spline to get the full surface matrix
        # tck = it.bisplrep(fitted_x, fitted_y, fitted_z)
        # Z = it.bisplev(moneyness, timeline, tck)

        # use polynomial to get the full surface matrix
        m = polyfit2d(fitted_x, fitted_y, fitted_z)
        xx, yy = np.meshgrid(moneyness, timeline)
        Z = polyval2d(xx, yy, m)
        return moneyness, timeline, Z

    # =====================================================================data viz methods
    def plot_iv(self):
        """Plot the implied vol scatter"""
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

    def plot_iv_surface(self,  option_type='A', size=(50,50)):
        """Plot the implied vol surface"""
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
        """Plot the implied vol scatter with fitted curve"""
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
        # initialize x axis
        moneyness = np.linspace(np.min(subset['Moneyness']), np.max(subset['Moneyness']), size[0])
        # fit using this axis
        fitted_x, fitted_y, fitted_z = self.fitting(moneyness, option_type)
        # interpolate every maturity
        ax = plt.axes(projection='3d')
        for Texp in np.unique(subset['Texp']):
            ax.plot(xs=fitted_x[np.where(fitted_y==Texp)],
                    ys=fitted_y[np.where(fitted_y==Texp)],
                    zs=fitted_z[np.where(fitted_y==Texp)])
        ax.scatter(subset['Moneyness'], subset['Texp'], subset['Implied_Vol'])
        ax.set_zlim(np.min(subset['Implied_Vol']) - 0.1, np.max(subset['Implied_Vol']) + 0.1)
        ax.set_title('Fitted Implied Vol')
        ax.set_xlabel('Moneyness')
        ax.set_ylabel('Maturity')
        ax.set_zlabel('Implied Vol')
        plt.show()

    # ================================================================================plotly functions
    def plotly_iv(self):
        # get subset
        subset = self.data
        subset1 = subset.loc[subset['OptionType'] == 'C', :]
        subset2 = subset.loc[subset['OptionType'] == 'P', :]
        CallOption = go.Scatter3d(
            x=subset1['Strike'],
            y= subset1['Texp'],
            z= subset1['Implied_Vol'],
            opacity=0.89,
            name='Call Option',
            mode="markers"
        )
        PutOption = go.Scatter3d(
            x= subset2['Strike'],
            y= subset2['Texp'],
            z= subset2['Implied_Vol'],
            opacity=0.89,
            name='Put Option',
            mode="markers"
        )
        layout = go.Layout(title='Implied Volatility Scatterplot',
            scene = dict(
                xaxis = dict(
                    title='Strike'),
                yaxis = dict(
                    title='Maturity'),
                zaxis = dict(
                    title='Implied Volatility'),)
        )
        fig = go.Figure(data=[CallOption, PutOption], layout=layout)
        py.plot(fig,
                filename=getcwd()+'/app/static/ivsurf_show.html',
                auto_open=False)

    def plotly_fitted(self, option_type='A', size=(50, 50)):
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
        # initialize x axis
        moneyness = np.linspace(np.min(subset['Moneyness']), np.max(subset['Moneyness']), size[0])
        # fit using this axis
        fitted_x, fitted_y, fitted_z = self.fitting(moneyness, option_type)

        unique_Texp = np.unique(fitted_y)

        trace1 = go.Scatter3d(
            x=subset['Moneyness'],
            y=subset['Texp'],
            z=subset['Implied_Vol'],
            opacity=0.89,
            mode="markers"
        )

        d = [trace1]

        for i in range(len(unique_Texp)):
            trace1 = go.Scatter3d(
                x=fitted_x[fitted_y==unique_Texp[i]],
                y=fitted_y[fitted_y==unique_Texp[i]],
                z=fitted_z[fitted_y==unique_Texp[i]],
                mode='lines'
            )

            d.append(trace1)
        layout = go.Layout(title='Implied Volatility Fitted Line',
            scene = dict(
                xaxis = dict(
                    title='Moneyness'),
                yaxis = dict(
                    title='Maturity'),
                zaxis = dict(
                    title='Implied Volatility'),)
        )
        fig = go.Figure(data=d, layout=layout)
        py.plot(fig,
                filename=getcwd()+'/app/static/ivsurf_show.html',
                auto_open=False)

    def plotly_iv_surface(self, option_type='A', size=(50, 50)):
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
            X, Y, Z = self.output_iv_matrix(option_type, size)
            trace1 = go.Surface(
                colorscale='Viridis',
                opacity=0.89,
                x=X,
                y=Y,
                z=Z
            )
            trace2 = go.Scatter3d(
                x=subset['Moneyness'],
                y=subset['Texp'],
                z=subset['Implied_Vol'],
                opacity=0.89,
                mode="markers"
            )
            layout = go.Layout(title='Implied Volatility Surface',
                scene = dict(
                    xaxis = dict(
                        title='Moneyness'),
                    yaxis = dict(
                        title='Maturity'),
                    zaxis = dict(
                        title='Implied Volatility'),)
            )
            fig = go.Figure(data=[trace1, trace2], layout=layout)
            py.plot(fig,
                    filename=getcwd()+'/app/static/ivsurf_show.html',
                    auto_open=False)

class date_selection:
    """This class only output the future maturity dates.
    It is used as a light weight and fast data output"""
    def __init__(self, interest_rate=0, K_range=(0, math.inf)):
        # this is my account. Don't share it to others. But I don't have money in it :P
        self.client = RestClient('2SQfDzW1Kaf3F', 'HOG2A2HCYERM2YONRBTYEBMYRZ2ESN3K')
        data = self.client.getsummary('future')
        # convert this list of dictionaries into data frame
        data = pd.DataFrame.from_dict(data=data)
        # split strings to get date and type
        data_tmp = data['instrumentName'].str.split('-')
        data['ExpirationDate'] = [data_tmp[i][1] for i in range(len(data))]
        data['ExpirationDate'] = pd.to_datetime(data['ExpirationDate'], format='%d%b%y')
        self.data = data

    def get_date(self):
        dates = pd.Series.sort_values(self.data['ExpirationDate'])
        dates = dates.reset_index(drop=True)
        return dates

class current_index:
    """This class is used only for the main page to download the current index automatically"""
    def __init__(self, interest_rate=0, K_range=(0, math.inf)):
        # this is my account. Don't share it to others. But I don't have money in it :P
        self.client = RestClient('2SQfDzW1Kaf3F', 'HOG2A2HCYERM2YONRBTYEBMYRZ2ESN3K')

    def get_index(self):
        return self.client.index()['btc']
