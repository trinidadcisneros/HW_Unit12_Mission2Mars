# Scrapping task to gather information from various sources, aggregate informaiton in a new website.
# Dependencies
from bs4 import BeautifulSoup
import requests
# Dependencies for 
from splinter import Browser
from splinter.exceptions import ElementDoesNotExist
# Dependencies for pandas table scrapping
import pandas as pd
# Import our pymongo library, which lets us connect our Flask app to our Mongo database.
import pymongo
import json
import pprint

# Step 1 url
news_url = 'https://mars.nasa.gov/news/'
featured_img_url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
weather_url = 'https://twitter.com/marswxreport?lang=en'
table_url = 'https://space-facts.com/mars/'
hemisphere_index_url_page = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'

def init_browser():
    # @NOTE: Replace the path with your actual path to the chromedriver
    executable_path = {"executable_path": "/usr/local/bin/chromedriver"}
    return Browser("chrome", **executable_path, headless=False)

def scrape():

    # Retrieve page with the requests module
    response = requests.get(news_url)

    # Create BeautifulSoup object; parse with 'html.parser'
    soup = BeautifulSoup(response.text, 'html.parser')

    # we needs news title and the paragraph
    results = soup.find_all(class_= "slide")

    # Loop through returned results and grab title and description
    for result in results:
        # Error handling
        try:
            # Obtain the article title
            news_title = (result.find('div', class_="content_title").text).strip("\n")
            news_p = (result.find('div', class_= "rollover_description_inner").text).strip("\n")
        except:
            pass    

    ### JPL Mars Space Images - Scrape Featured Picture
    # https://splinter.readthedocs.io/en/latest/drivers/chrome.html
    # !which chromedriver

    browser = init_browser()
    browser.visit(featured_img_url)

    xpath = '//*[@id="page"]/section[3]/div/ul/li[1]/a/div/div[2]/img'
    html = browser.html
    soup = BeautifulSoup(html, 'html.parser')
    imagebar = browser.find_by_xpath(xpath)
    featured_image_url = []
    for image in imagebar:
        featured_image_url.append(image._element.get_attribute('src'))

    ### Scrape Mars Current Weather
    
    # Retrieve page with the requests module
    response = requests.get(weather_url)

    # Create BeautifulSoup object; parse with 'html.parser'
    soup = BeautifulSoup(response.text, 'html.parser')

    # Examine the results, then determine element that contains sought info
    # print(soup.prettify())

    # results are returned as an iterable list (get the latest tweet from the page)
    twitter_results = soup.find_all('div', class_="content")

    # Loop through returned results and grab the text for all tweets in the content section
    mars_weather_data = []
    for result in twitter_results:
        # Error handling
        try:
            # Obtain the article title
            tweet = result.find('p', class_="TweetTextSize TweetTextSize--normal js-tweet-text tweet-text").text
            mars_weather_data.append(tweet)
        except:
            pass


    ### Mars Facts - Table scrapping
    tables = pd.read_html(table_url, header = None)
    mars_table = (tables[0][:][:].values[:]).tolist()
    # html_table = tables.to_html()


    ### Dictonary that contains Mars Hemispheres information and high resolution image
    # https://splinter.readthedocs.io/en/latest/drivers/chrome.html
    # !which chromedriver

    ### This step will prepare a list of URL for the 4 hemispheres
    browser = init_browser()

    # Opens url in browser
    browser.visit(hemisphere_index_url_page)

    html = browser.html
    soup = BeautifulSoup(html, 'html.parser')
    xpath = '//*[@id="product-section"]/div[2]'
    high_res_locator = []
    elems = browser.find_by_xpath(xpath).find_by_tag("a")
    for e in elems:
        if e["href"] not in high_res_locator:
            high_res_locator.append(e["href"])

    ### Initialize browswer
    browser = init_browser()

    # Initialized empty list for high resolution urls (hrefs)
    high_def_urls = []

    # Iterate through the all the link in high resolution url list
    for i in high_res_locator:
        browser.visit(i)
        html = browser.html
        soup = BeautifulSoup(html, 'html.parser')
        xpath = '//*[@id="wide-image"]/div/ul/li[1]/a'
        elems = browser.find_by_xpath(xpath)
        for e in elems:
            if e["href"] not in high_def_urls:
                high_def_urls.append(e["href"])

    cer_hem = high_def_urls[0]
    sch_hem = high_def_urls[1]
    syr_m_hem = high_def_urls[2]
    valles_m_hem = high_def_urls[3]

    # Loop through list and store title (key) : url (img)
    hemisphere_image_urls = [
        {"title": "Valles Marineris Hemisphere", "img_url": valles_m_hem},
        {"title": "Cerberus Hemisphere", "img_url": cer_hem},
        {"title": "Schiaparelli Hemisphere", "img_url": sch_hem},
        {"title": "Syrtis Major Hemisphere", "img_url": syr_m_hem},]
    
    # All Scrapped Data into dictionary
    mars_dict = {"news_title" : news_title, "news_description" : news_p, "latest_image" : featured_image_url, "mars_current_weather" : mars_weather_data[0], "mars_stats" : mars_table, "mars_hem_images" : hemisphere_image_urls}

    return mars_dict

def save_data_to_database(mars_dict):
    conn = 'mongodb://localhost:27017'
    # Pass connection to the pymongo instance.
    client = pymongo.MongoClient(conn)
    # Connect to a database. Will create one if not already available.
    db = client.mars_db
    # Drops collection if available to remove duplicates
    db.mars_facts.drop()
    # db.mars_facts.insert_many(mars_dict)
    db.mars_facts.insert_one(mars_dict)

if __name__ == '__main__':
    output = scrape()
    # print(output)
    pp = pprint.PrettyPrinter(depth = 10)
    pp.pprint(output)
    # json.dumps(output, indent=4)
    # save_data_to_database(output)