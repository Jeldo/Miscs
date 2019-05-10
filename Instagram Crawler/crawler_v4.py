import selenium.webdriver as wd
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup as bs
from time import sleep
import dateutil.parser
import pytz
import json
import re
import sys
import os
import time

SLEEP_TIME_SHORT = 0.3
SLEEP_TIME_MID = 1.5
SLEEP_TIME_LONG = 4


def get_path():
    if os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '/chromedriver.exe'):
        return os.path.dirname(os.path.realpath(__file__)) + '/chromedriver.exe'
    elif os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '/chromedriver'):
        return os.path.dirname(os.path.realpath(__file__)) + '/chromedriver'


def set_browser():
    ### define chrome options
    chrome_option = wd.ChromeOptions()
    chrome_option.add_argument("--incognito")
    chrome_option.add_argument('--start-maximized')
    # chrome_option.add_argument('window-size=1920x1080')
    # chrome_option.add_argument('disable-gpu')
    chrome_option.add_argument("lang=ko_KR")  # ko_KR or en
    chrome_option.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36")
    # undo the below comment to open chrome
    # chrome_option.add_argument('headless')
    # service_args = ['--ignore-ssl-errors=true']
    # driver = wd.Chrome(get_path(), service_args=service_args, chrome_options=chrome_option)
    driver = wd.Chrome(get_path(), chrome_options=chrome_option)
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
    driver.execute_script(
        "const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};")
    return driver


def scroll_down(driver, count):
    for i in range(count):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')


def scroll_up(driver, count):
    for i in range(count):
        driver.execute_script('window.scrollBy(0, -200)')


def get_post_content(driver):
    content = driver.find_element_by_class_name('eo2As')
    return content


def get_location_data(driver):
    try:
        location_data = driver.find_element_by_class_name('O4GlU')
    except Exception as e:
        # print(e)
        location_name = 'LOCATION NOT FOUND'
    else:
        location_name = location_data.text
    return location_name


def get_link(driver):
    return driver.current_url


def get_captions(article):
    # multiple images may be delivered
    caption_html = article.find_all('img', class_='FFVAD')
    captions = set()
    for image in caption_html:
        if ':' in image['alt']:  # if caption exists
            all_captions = image['alt'].split(':')[1].split(',')
            for caption in all_captions:
                captions.add(caption)
    captions = list(captions)
    return captions


def get_hashtags(content):
    pattern = re.compile(r'#[^ |^#|^\n]+')
    hashtags = re.findall(pattern, content.text)
    for i in range(0, len(hashtags)):
        hashtags[i] = hashtags[i][1:]
    return hashtags


def get_timestamp(article):
    time_html = article.find('time')
    zulu_time = time_html['datetime']
    date = dateutil.parser.parse(zulu_time)
    local_timezone = pytz.timezone('Asia/Seoul')
    local_date = date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    local_timestamp = local_date.isoformat()
    return local_timestamp


def get_place(driver, tries, max_retries):
    ### fetching the post may take time
    try:
        content = get_post_content(driver)
    except NoSuchElementException:  # Failed to get content including image class 'eo2As'
        print("Failed to fetch the post\nRetrying...")
        sleep(SLEEP_TIME_SHORT)
        if tries < max_retries:
            return get_place(driver, tries + 1, max_retries)
    else:
        html = bs(driver.page_source, 'html.parser')
        body = html.find('body')
        article = body.find(class_='M9sTE')  # class of each clicked image

        location_name = get_location_data(driver)
        link = driver.current_url
        captions = get_captions(article)
        hashtags = get_hashtags(content)
        timestamp = get_timestamp(article)
        place_info = {'location': location_name, 'link': link, 'timestamp': timestamp, 'captions': captions,
                      'hashtags': hashtags}
        return place_info


def crawler(max_search_iteration=10):
    start_time = time.time()
    driver = set_browser()
    TAG = '먹스타그램'
    URL = 'https://www.instagram.com/explore/tags/' + TAG
    driver.get(URL)
    driver.execute_script('window.scrollTo(0, 0)')
    sleep(SLEEP_TIME_LONG)

    ### find first article
    fetched_article = 0
    article_pool = set()
    links = []
    timeout = 1
    while fetched_article < max_search_iteration:
        # get links
        article_html = driver.find_element_by_xpath("//article ")
        html = bs(driver.page_source, 'html.parser')
        body = html.find('body')
        articles = body.find_all(class_='v1Nh3')
        for idx in range(0, len(articles)):
            article_html = articles[idx].find('a')
            article_link = 'https://www.instagram.com' + article_html['href']
            if article_link in article_pool:
                timeout += 1
                continue
            else:
                timeout = 1
                print('fetching links {} / {}'.format(fetched_article, max_search_iteration))
                article_pool.add(article_link)
                links.append(article_link)
                fetched_article += 1
            if fetched_article == max_search_iteration:  # inner condition to terminate for loop
                break
        scroll_down(driver, count=4)
        if timeout > 20:
            scroll_up(driver, count=3)
        sleep(SLEEP_TIME_MID)

    end_time = time.time()
    link_file = open(os.path.dirname(os.path.abspath(__file__)) + '/places_link.json', 'w', encoding='utf-8')
    link_file.write(json.dumps(links, indent=4, sort_keys=False, ensure_ascii=False))
    link_file.close()
    driver.close()

    print(
        "All process complete. Fetched {} posts. Execution time : {:.2f}sec".format(fetched_article,
                                                                                    end_time - start_time))

    driver_fetch = set_browser()
    f_links = open(os.path.dirname(os.path.abspath(__file__)) + '/places_link.json', 'r', encoding='utf-8')
    links = json.load(f_links)
    places = []
    links = list(set(links))
    for i in range(0, len(links)):
        driver_fetch.get(links[i])
        print('fetching {} / {}'.format(i, max_search_iteration))
        sleep(SLEEP_TIME_SHORT)
        place = get_place(driver_fetch, tries=0, max_retries=1)
        if place is not None:
            places.append(place)
    f_places = open(os.path.dirname(os.path.abspath(__file__)) + '/places_out.json', 'w', encoding='utf-8')
    f_places.write(json.dumps(places, indent=4, sort_keys=False, ensure_ascii=False))

    f_links.close()
    f_places.close()


if __name__ == '__main__':
    print('Start Instagram Crawler')
    # crawler(int(sys.argv[1]))
    crawler(50000)
