import pandas as pd
import numpy as np
from scipy.stats import ttest_ind

'''
This script uses housing data from the Zillow research data site, a list of
college towns in the United States obtained from Wikipedia and the Bureau of Economic analysis,
US Department of Commerce's historical GDP data to test the hypothesis:

"The mean housing prices of University towns is less effected by a recession."

We will test this hypothesis by running a t-test, and if the associated p-value is
<0.01, then we reject the null-hypothesis.
'''



# Use this dictionary to map state names to two letter acronyms
states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa',\
 'NV': 'Nevada', 'WY': 'Wyoming', 'NA': 'National', 'AL': 'Alabama', \
 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon', 'MT': 'Montana', \
 'IL': 'Illinois', 'TN': 'Tennessee', 'DC': 'District of Columbia', \
 'VT': 'Vermont','ID': 'Idaho', 'AR': 'Arkansas', 'ME': 'Maine', 'WA': 'Washington', \
 'HI': 'Hawaii', 'WI': 'Wisconsin', 'MI': 'Michigan', 'IN': 'Indiana', \
 'NJ': 'New Jersey', 'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi',\
  'PR': 'Puerto Rico', 'NC': 'North Carolina', 'TX': 'Texas', \
  'SD': 'South Dakota', 'MP': 'Northern Mariana Islands', 'IA': 'Iowa',\
   'MO': 'Missouri', 'CT': 'Connecticut', 'WV': 'West Virginia',\
    'SC': 'South Carolina', 'LA': 'Louisiana', 'KS': 'Kansas', 'NY': 'New York', \
    'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California', \
    'CO': 'Colorado', 'PA': 'Pennsylvania', 'DE': 'Delaware', 'NM': 'New Mexico', \
    'RI': 'Rhode Island', 'MN': 'Minnesota', 'VI': 'Virgin Islands', \
    'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia', \
    'ND': 'North Dakota', 'VA': 'Virginia'}


def get_list_of_university_towns():
    '''Returns a DataFrame of towns and the states they are in from the
    university_towns.txt list. The format of the DataFrame should be:
    DataFrame( [ ["Michigan", "Ann Arbor"], ["Michigan", "Yipsilanti"] ],
    columns=["State", "RegionName"]  )

    The following cleaning is done:

    1. For "State", removing characters from "[" to the end.
    2. For "RegionName", when applicable, removing every character from " (" to the end.
     '''

    uni_towns = open('university_towns.txt','r')
    unitowns = list(uni_towns)
    uni_towns.close()

    data = []
    state = ''

    for item in unitowns:
        if '[edit]' in item:
            state = item[:-7]
        else:
            data.append([ state, item.split(' (')[0].strip('\n') ])

    df = pd.DataFrame( data, columns = [ 'State', 'RegionName' ] )

    return df

def get_recession_start():
    '''Returns the year and quarter of the recession start time as a
    string value in a format such as 2005q3'''

    GDP = pd.read_excel('gdplev.xls',skiprows = 219, usecols = [4,6])
    GDP.columns = ['Quarter', 'GDP']
    GDP.set_index('Quarter',inplace = True)

    return GDP.where((GDP.diff()<0)&\
    (GDP.diff().shift(-1)<0)).dropna().iloc[0].name


def get_recession_end():
    '''Returns the year and quarter of the recession end time as a
    string value in a format such as 2005q3'''

    GDP = pd.read_excel('gdplev.xls',skiprows = 219, usecols = [4,6])
    GDP.columns = ['Quarter', 'GDP']
    GDP.set_index('Quarter',inplace = True)

    rec_start = get_recession_start()

    return GDP[rec_start:].where((GDP.diff()>0)&\
    (GDP.diff().shift(-1)>0)).dropna().iloc[1].name


def get_recession_bottom():
    '''Returns the year and quarter of the recession bottom time as a
    string value in a format such as 2005q3'''

    GDP = pd.read_excel('gdplev.xls',skiprows = 219, usecols = [4,6])
    GDP.columns = ['Quarter', 'GDP']
    GDP.set_index('Quarter',inplace = True)

    rec_start = get_recession_start()
    rec_end = get_recession_end()

    return GDP[rec_start:rec_end].sort_values(by = 'GDP').iloc[0].name

def convert_housing_data_to_quarters():
    '''Converts the housing data to quarters and returns it as mean
    values in a dataframe. This dataframe should be a dataframe with
    columns for 2000q1 through 2016q3, and should have a multi-index
    in the shape of ["State","RegionName"].
    '''
    df = pd.read_csv('City_Zhvi_AllHomes.csv')
    df['State'] = df['State'].map(states)
    df.set_index(['State','RegionName'],inplace = True)
    df = df.loc[:,'2001-01':]
    df.columns = pd.to_datetime(df.columns)
    df= df.resample('Q',axis = 1).mean()
    df = df.rename( columns = lambda x:str(x.to_period('Q')).lower() )
    return df

def run_ttest():
    '''First creates new data showing the decline or growth of housing prices
    between the recession start and the recession bottom. Then runs a ttest
    comparing the university town values to the non-university towns values,
    and returns whether the alternative hypothesis (that the two groups are the same)
    is true or not as well as the p-value of the confidence.

    Return the tuple (different, p, better) where different=True if the t-test is
    True at a p<0.01 (we reject the null hypothesis), or different=False if
    otherwise (we cannot reject the null hypothesis). The variable p should
    be equal to the exact p value returned from scipy.stats.ttest_ind(). The
    value for better should be either "university town" or "non-university town"
    depending on which has a lower mean price ratio (which is equivilent to a
    reduced market loss).'''
    rec_start = get_recession_start()
    rec_bottom = get_recession_bottom()
    uni_towns = get_list_of_university_towns()
    housing = convert_housing_data_to_quarters()

    before_rec_start = housing.columns.values[np.where(housing.columns.values==rec_start)[0][0]-1]
    housing['PriceRatio'] = housing[before_rec_start].div(housing[rec_bottom])
    list_uni_towns = uni_towns.to_records(index = False).tolist()
    uni_towns = housing.loc[housing.index.isin(list_uni_towns)]
    not_uni_towns = housing.loc[[not i for i in housing.index.isin(list_uni_towns)]]

    [stat,pval] = ttest_ind(not_uni_towns['PriceRatio'].dropna(),uni_towns['PriceRatio'].dropna())

    different = pval < 0.01
    if not_uni_towns['PriceRatio'].dropna().mean() < uni_towns['PriceRatio'].dropna().mean():
        better = 'non-university town'
    else:
        better = 'university town'

    return (different,pval,better)

(different, pval, better) = run_ttest()
print(different, pval, better)
