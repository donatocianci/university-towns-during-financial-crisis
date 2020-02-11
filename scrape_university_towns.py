import requests
from bs4 import BeautifulSoup
import re

'''
This script generates a text file with a list of vetted college towns from the
list of college towns in the US in the Wikipedia article on College Towns:

https://en.wikipedia.org/wiki/List_of_college_towns#College_towns_in_the_United_States

Glancing at the list of towns in the Wikipedia article, some don't have
colleges associated with them and others don't actually appear to be college towns.
This script vets the potential towns to clean up the data. Specifically, this
script checks each possible college town against several criteria and stores them
 in a text file if they pass. If the town and associated colleges have an associated "good"
citation, then they are stored in the text file. If the town's Wikipedia entry contains
a link to Wikipedia's "University Towns in the United States" category, then the town
is stored in the text file. If the town's Wikipedia article contains two mentions of
a particular college in the introductory paragraph or economics section, then the
town is added to the text file. Otherwise, the candidate town is not deemed a college
town and is omitted from the text file.
'''




###############################################################################
#
# AUXILLARY FUNCTIONS
#
###############################################################################
def relevant_section(tag):

    '''
    Input parameter tag is a BeautifulSoup tag data type.

    This function returns a boolean variable. The variable is True if the tag
    corresponds to a paragraph or table and either does not have a section heading
    above it in the BeautifulSoup tree or the section heading above it in the tree
    contains the word "economy". Otherwise, the returned variable is False.
    '''


    if tag.name=='p' or tag.name=='table':
        previous_heading = tag.find_previous('h2')
        if previous_heading == None:
            return True
        elif 'economy' in previous_heading.find('span').text.lower():
            return True
        else:
            return False


def check_college_town_status(tag):

    '''
    Input parameter tag is a BeautifulSoup tag data type that should correspond
    to a tag containing a particular entry in a list of possible college towns.

    This function returns a boolean variable. The variable is True if the
    Wikipedia entry corresponding to the town in tag conatins a link to the
    "University Towns in the United States" category on Wikipedia or if a particular
    university is mentioned at least two times in the introductory section or
    economy section of the Wikipedia article. Otherwise, the variable returns False.
    '''

    base_url = 'https://en.wikipedia.org'

    #get city url from the tag:
    url = base_url+tag.find_next('a')['href']

    #get list of universities from the tag.
    universities = tag.find_all('a')[1:]
    universities = [uni.text.lower() for uni in universities if
                    (uni.text != 'citation needed' and '[' not in uni.text)]

    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    #do easier check first:
    #check whether there is a link to the University Towns category:
    uni_towns_link = '/wiki/Category:University_towns_in_the_United_States'
    category_links = soup.find('div', id = "catlinks")
    if category_links.find_all('a',href=uni_towns_link):
        return True

    #do harder check if there is no link to the University Towns category
    relevant_paras = soup.find_all(relevant_section)
    for uni in universities:
        ref_count = 0
        for para in relevant_paras:
            if uni in para.get_text().lower():
                ref_count = ref_count + 1
        if ref_count >= 2:
            return True

    return False


def get_towns_from_state(tag):

    '''
    Input parameter tag is a BeautifulSoup tag data type, which should be a tag
    that corresponds to a list of possible college towns in a particular state in
    the Wikipedia article about college towns.

    This function returns towns, a list of strings containing college towns that
    were listed in the tag. Each possible college town in the tag is vetted
    according to the following criteria. If there is a predetermined good source
    listed for this town (a source listed in the good_sources list), then the town
    and it's paranthetical list of colleges is appended to towns as a string.
    Otherwise, we look at that particular town's Wikipedia entry. If the entry
    contains a link to the "University Towns in the United States" Category on
    Wikipedia, then we'll append the town as a string to towns. Or if the entry
    mentions a particular university two times in the introductory
    paragraph and table or the economy section, then the town is added to towns
    as a string.
    '''

    good_sources = ['7','9','13','15','16','17','22','24','28','30','34','37',
                    '38','40','41','43','50','54']

    big_cities = ['Los Angeles', 'Sacramento', 'Atlanta', 'Chicago', 'Detroit',
    'Cleveland', 'Columbus', 'Johnstown', 'Lower Merion Township', 'Philadelphia',
    'Pittsburgh', 'State College', 'Providence']


    towns = []
    town_list = tag.find_next('ul').find_all('li')

    for item in town_list:
        #if the town is subdivided into neighborhoods just look at the neighborhoods
        if item.find_all('ul'):
            continue

        #check whether "town" is actually a neighborhood in a larger city:
        if item.parent.previous_sibling.previous_sibling.name != 'h3':
            #find the larger city name and append it to the name of the neighborhood.
            city = item.parent.parent.find_next('a').text
            if city in big_cities:
                item.find_next('a').string = item.find_next('a').string + ', '+city
        line = item.get_text()
        sources = re.findall('\[([0-9]{1,2})\]',line)
        #if there are sources and they are good, append the town
        if sources and sum(map(lambda x: x in good_sources, sources)):
                line = line+'\n'
                towns.append(line)
        #otherwise, check manually whether the town is a university town.
        else:
            status = check_college_town_status(item)
            if status:
                line = line+'\n'
                towns.append(line)

    return towns


def scrape_university_towns():

    '''
    Returns a list of strings where each element in the list is either a string
    containing the town, its associated college towns and any citation indices, e.g.

    Auburn (Auburn University, Edward Via College of Osteopathic Medicine)[7]

    or a string containing a state. Each town is associated to the nearest state
    that is indexed before it.
    '''

    data= []
    html = requests.get(url)

    soup = BeautifulSoup(html.text, 'html.parser')
    #find the tag for the heading with college towns in the US
    tag = soup.find('span',id = 'College_towns_in_the_United_States')
    tag = tag.find_next('h3')

    #loop over each state in the list
    while tag.find_previous_sibling('h2').find('span').text=='College towns in the United States':
        print('Checking college towns in '+tag.text.split('[')[0]+'...')
        data.append(tag.get_text()+'\n')
        towns = get_towns_from_state(tag)
        data = data+towns
        tag = tag.find_next('h3')

    return data

def write_to_txt(data):

    '''
    Parameter data is a list of strings. This function writes each string element
    in data to a new line in a text file titled university_towns.txt and then
    saves the text file to the local directory.
    '''

    file = open("university_towns.txt",'w')
    file.writelines(data)
    file.close()


###############################################################################
#
# MAIN SCRIPT
#
###############################################################################

url = 'https://en.wikipedia.org/wiki/List_of_college_towns#College_towns_in_the_United_States'
#scrape the data from relevant wikipedia website
data = scrape_university_towns()
write_to_txt(data)
