import numpy as np
import pandas as pd
import scipy.stats as stats
import random
import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.rcParams.update({'font.size': 16})
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['grid.color'] = 'lightgrey'

class HypTest():
    def __init__(self, col_list, name_list, alpha=.95, alternative='two-sided'):

        self.col_list = col_list
        self.name_list = name_list
        self.alpha = alpha
        self.alpha_2 = (1-self.alpha)/2
        self.alternative = alternative

        self.A = col_list[0]
        self.B = col_list[1]
        self.nA = len(col_list[0])
        self.nB = len(col_list[1])
        self.xbarA = np.mean(col_list[0])
        self.xbarB = np.mean(col_list[1])
        self.sdA = np.std(col_list[0])
        self.sdB = np.std(col_list[1])
        
        self.seA = self.sdA/np.sqrt(self.nA)
        self.seB = self.sdB/np.sqrt(self.nB)
        self.pooled_sd = np.sqrt(self.sdA**2/self.nA + self.sdB**2/self.nB)
        self.cohens_sd = np.sqrt((self.sdA**2 + self.sdB**2)/2)
        self.glass_sd = self.pooled_sd
        self.hedges_sd = np.sqrt( ((self.nA-1)*self.sdA**2 + (self.nB-1)*self.sdB**2)/(self.nB+self.nA-2))

        self.diff = self.xbarA-self.xbarB
        self.test_stat = self.diff/self.pooled_sd
        self.z = self.diff/self.pooled_sd

        self.effect_cohens_d = self.diff/self.cohens_sd
        self.effect_glass_delta = self.diff/self.pooled_sd
        self.effect_hedges_g = self.diff/self.hedges_sd
        
        self.rr_l = stats.norm(0, self.pooled_sd).ppf(self.alpha_2)
        self.rr_h = stats.norm(0, self.pooled_sd).ppf(self.alpha+self.alpha_2)
        self.rr_lt = stats.norm(0, self.pooled_sd).ppf(1-self.alpha)
        self.rr_gt = stats.norm(0, self.pooled_sd).ppf(self.alpha)

        if self.alternative=='two_sided':
            self.power = 1 - stats.norm(self.diff, self.pooled_sd).cdf(abs(self.rr_l))
        else:
            self.power = 1 - stats.norm(self.diff, self.pooled_sd).cdf(abs(self.rr_gt))
 
        self.colA = 'red'
        self.colB = 'dodgerblue'
        self.col_null = 'green'
        self.col_alt = 'purple'
        self.col_rr = 'k'
        self.col_power = 'plum'

        self.pval_1sided = (1 - stats.norm(0, self.pooled_sd).cdf(abs(self.diff)))
        self.pval_2sided = (1 - stats.norm(0, self.pooled_sd).cdf(abs(self.diff)))*2
        self.pval_z_1sided = 1-stats.norm().cdf(abs(self.z))

    def p_value(self, equal_var=False):
        return stats.ttest_ind(self.col_list[0], 
                               self.col_list[1], 
                               equal_var=equal_var, 
                               alternative=self.alternative)[1]
    
    def p_value_by_hand(self):
        pv = 1 - stats.norm(0, self.pooled_sd).cdf(abs(self.diff))
        if self.alternative=='two-sided':
            return pv*2
        else:
            return pv

    def descriptive_stats(self, num_list, perc = .95):
        '''input: list of numeric data
        output: dictionary of descriptive statistics'''
        d = {}
        
        d['size'] = len(num_list)
        
        d['mean'] = np.mean(num_list)
        d['sd'] = np.std(num_list)
        
        d['min'] = np.mean(num_list)
        d['1Q'] = np.percentile(num_list, 25)
        d['median'] = np.median(num_list)
        d['3Q'] = np.percentile(num_list, 75)
        d['max'] = np.max(num_list)
        
        d['min_mode'] = stats.mode(num_list)[0][0]
        
        d[f'{int(perc*100)}% quantile low'] = np.percentile(num_list, 100*(1-perc)/2) 
        d[f'{int(perc*100)}% quantile high'] = np.percentile(num_list, 100*(1-((1-perc)/2)))
        
        d['IQR'] = np.percentile(num_list, 75) - np.percentile(num_list, 25)
        d['1Q - 1.5*IQR'] = np.percentile(num_list, 25) - 1.5*(np.percentile(num_list, 75) - np.percentile(num_list, 25))
        d['3Q + 1.5*IQR'] = np.percentile(num_list, 75) + 1.5*(np.percentile(num_list, 75) - np.percentile(num_list, 25))
        num_arr = np.array(num_list)
        d['n_outliers_low?'] = len(num_arr[num_arr<d['1Q - 1.5*IQR']])
        d['n_outliers_high?'] = len(num_arr[num_arr>d['3Q + 1.5*IQR']])
        d['%_outiers_low'] = len(num_arr[num_arr<d['1Q - 1.5*IQR']])/len(num_list)
        d['%_outiers_high'] = len(num_arr[num_arr>d['3Q + 1.5*IQR']])/len(num_list)
    #     d['outliers?'] = list(num_arr[num_arr<d['1Q - 1.5*IQR']])+list(num_arr[num_arr>d['3Q + 1.5*IQR']])
        return d

    def descriptive_stats_df(self, perc=.95):
        '''input: list of numeric lists, names of numeric lists
        output: dataframe of descriptive statistics, stats for each list = column'''
        arrs = self.col_list
        cols = self.name_list
        d = self.descriptive_stats(arrs[0], perc=perc)
        df = pd.DataFrame(index = d.keys(), data = d.values(), columns=[cols[0]])
        for i, arr in enumerate(arrs[1:]):
            temp = self.descriptive_stats(arr)
            df_temp = pd.DataFrame(index = temp.keys(), data = temp.values(), columns=[cols[i+1]])
            df=df.join(df_temp)
        return df

    def inferential_stats(self, num_list, ci=.95):
        '''input: list of numeric data
        output: dictionary of inferential statistics'''
        d = {}
        n = len(num_list)
        d['size'] = n

        xbar = np.mean(num_list)
        d['mean'] = xbar

        se = np.std(num_list)/np.sqrt(len(num_list))
        d['se'] = se
        
        d[f'{int(ci*100)}% CI low'] = stats.norm(xbar, se).ppf(1-ci) 
        d[f'{int(ci*100)}% CI high'] = stats.norm(xbar,se).ppf(ci) 
        return d

    def inferential_stats_df(self, ci=.95):
        '''input: list of numeric lists, names of numeric lists
        output: dataframe of inferential statistics, stats for each list = column'''
        arrs = self.col_list
        cols = self.name_list
        d = self.inferential_stats(arrs[0], ci=ci)
        df = pd.DataFrame(index = d.keys(), data = d.values(), columns=[cols[0]])
        for i, arr in enumerate(arrs[1:]):
            temp = self.inferential_stats(arr)
            df_temp = pd.DataFrame(index = temp.keys(), data = temp.values(), columns=[cols[i+1]])
            df=df.join(df_temp)
        return df

    def plot_mean_sd(self, ax):
        ax.bar([0,1], 
               [self.xbarA, self.xbarB], 
               yerr=[self.sdA, self.sdB], 
               color=[self.colA, self.colB])
        ax.set_xticks([0,1])
        ax.set_xticklabels(['true', 'false'], fontsize=20)
        ax.set_ylabel('avg number of retweets', fontsize=20)
        ax.set_title('Descriptive Statistics: Mean and Standard Deviation by Possibly Sensitive Label', fontsize=25)
        ax.text(0+.05,self.xbarA/2-250, f'mean = {self.xbarA:2.2f}', fontsize=15)
        ax.text(1+.05,self.xbarB/2-250 , f'mean = {self.xbarB:2.2f}', fontsize=15)
        ax.text(0-.05,self.xbarA+250, f' sd = {self.sdA:2.2f}', fontsize=15, rotation=90)
        ax.text(1-.05,self.xbarB+250, f' sd = {self.sdB:2.2f}', fontsize=15, rotation=90)

    def plot_hists(self, ax):
        binA = int(np.sqrt(len(self.A)))
        binB = int(np.sqrt(len(self.B)))
        ax.hist(self.A, color = self.colA, alpha=.75,bins=binA,density=True, label='True')
        ax.hist(self.B, color = self.colB, alpha=.75, bins=binB, density=True, label='False')
        ax.set_xlabel('number of retweets')
        ax.set_ylabel('frequency')
        ax.set_title('Distribution by by Possibly Sensitive Label')
        ax.legend()

    def plot_sorted(self, ax):
        l = min(len(self.A), len(self.B))
        x = np.arange(l)
        yA = sorted(random.sample(list(self.A), k=l))
        yB = sorted(random.sample(list(self.B), k=l))
        ax.scatter(x, yA, color=self.colA, label = 'True')
        ax.scatter(x, yB, color=self.colB, label = 'False')
        ax.set_title('Sorted Values by Possibly Sensitive Label')
        ax.set_xlabel('index')
        ax.set_ylabel('sorted random sample')
        ax.legend()

    def plot_sampling_distributions(self, ax):
        start = min(self.xbarA-self.seA*3, self.xbarB-self.seB*3)
        stop = max(self.xbarA+self.seA*3, self.xbarB+self.seB*3)
        x = np.linspace(start, stop, 1000)
        yA = stats.norm(self.xbarA, self.seA).pdf(x)
        yB = stats.norm(self.xbarB, self.seB).pdf(x)
        ax.plot(x, yA, color = self.colA, label = 'true')
        ax.axvline(x=self.xbarA, color=self.colA, linestyle='--', lw=3, label=f'mean:true={self.xbarA:2.2f}')
        ax.plot(x, yB, color = self.colB, label = 'false')
        ax.axvline(x=self.xbarB, color=self.colB, linestyle='--', lw=3, label=f'mean:false={self.xbarB:2.2f}')
        ax.set_xlabel('average number of retweets')
        ax.set_ylabel('pdf')
        ax.set_title('Means Sampling Distributions for Possibly Sensitive Labels')
        ax.legend()

    def plot_diff_of_means(self, ax):
        start = min(0-self.pooled_sd*3, self.diff-self.pooled_sd*3)
        stop = max(self.pooled_sd*3, self.diff+self.pooled_sd*3)
        x = np.linspace(start, stop, 1000)
        ynull = stats.norm(0, self.pooled_sd).pdf(x)
        yalt = stats.norm(self.diff, self.pooled_sd).pdf(x)
        ax.plot(x, ynull, color = self.col_null, label = 'null',  lw=3)
        ax.axvline(x=0, color=self.col_null, linestyle='--', lw=3, label=f'mean-null: 0')
        ax.plot(x, yalt, color = self.col_alt, label = 'alternative', lw=3)
        ax.axvline(x=self.diff, color=self.col_alt, linestyle='--', lw=3, label=f'mean-alt: {self.diff:2.2f}')
        if self.alternative == 'two-sided':
            ax.axvline(x = self.rr_l, color=self.col_rr, 
                    linestyle =':', lw=3 , label=f'critical value: +/-{abs(self.rr_l):2.2f}')
            ax.axvline(x = self.rr_h, color=self.col_rr, linestyle =':', lw=3)
            ax.fill_between(x, ynull, 0, where=(x<=self.rr_l), 
                            color=self.col_rr, alpha=.5, label='rejection region')
            ax.fill_between(x, yalt, 0, where=(x<=self.rr_l), color=self.col_power, alpha=.5)
            ax.fill_between(x, ynull, 0, where=(x>=self.rr_h), 
                            color=self.col_rr, alpha=.5)
            ax.fill_between(x, yalt, 0, where=(x>=self.rr_h), color=self.col_power, alpha=.5, 
                            label=f'power: {self.power:2.5f}')
        elif self.alternative == 'less':
            ax.axvline(x = self.rr_lt, color=self.col_rr, 
                       linestyle =':', lw=3 , label=f'critical value: {self.rr_lt:2.2f}')
            ax.fill_between(x, ynull, 0, where=(x<=self.rr_lt), 
                            color=self.col_rr, alpha=.5, label='rejection region')
            ax.fill_between(x, yalt, 0, where=(x<=self.rr_lt), color=self.col_power, 
                            alpha=.5, label = f'power: {self.power:2.5f}')
        else:
            ax.axvline(x = self.rr_gt, color=self.col_rr, 
                       linestyle =':', lw=3 , label=f'critical value: {self.rr_gt:2.2f}')
            ax.fill_between(x, ynull, 0, where=(x>=self.rr_gt), 
                            color=self.col_rr, alpha=.5, label='rejection region')
            ax.fill_between(x, yalt, 0, where=(x>=self.rr_gt), color=self.col_power, alpha=.5, 
                            label=f'power: {self.power:2.5f}')
        ax.set_xlabel('average number of retweets')
        ax.set_ylabel('pdf')
        ax.set_title('Null and Alternative Distributions')
        ax.legend(facecolor='lightgrey')

if __name__=="__main__":
    
    lst1 = stats.norm(3036.85,7837.89).rvs(512)
    lst2 = stats.norm(1278.48, 5908.88).rvs(14582)

    ht = HypTest([lst1, lst2], ['lst1', 'lst2'], alternative='greater')

    print(ht.descriptive_stats_df())
    print(ht.inferential_stats_df())

    print(ht.pooled_sd)
    print(f'cohens-d for similar variance: {ht.effect_cohens_d}')
    print(f'glass-delta for different sizes: {ht.effect_glass_delta}') 
    print(f'hedges-g for different sizes and variances: {ht.effect_hedges_g}')

    print(f'p-value-scipy = {ht.p_value()}')
    print(f' pval-byhand = {ht.p_value_by_hand()}')
    print(f'pval-1sided = {ht.pval_1sided}')
    print(f'pval-2sided = {ht.pval_2sided}')
    print(f'pval-z-2sided = {ht.pval_z_1sided}')

    fig, ax = plt.subplots(figsize=(20,5))
    ht.plot_mean_sd(ax)
    fig, ax = plt.subplots(figsize=(20,5))
    ht.plot_hists(ax)
    fig, ax = plt.subplots(figsize=(20,5))
    ht.plot_sorted(ax)
    fig, ax = plt.subplots(figsize=(20,5))
    ht.plot_sampling_distributions(ax)
    fig, ax = plt.subplots(figsize=(20,5))
    ht.plot_diff_of_means(ax)
    plt.show()

    