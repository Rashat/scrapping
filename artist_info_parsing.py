from bs4 import BeautifulSoup as BS
import requests
import csv
import multiprocessing
import platform
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


start_time = time.time()


def get_request(url, artist):
    try:
        response = requests.get(url).text
    except:
        print(f'No info about {artist}')
        return
    musicians_skills = [' (composer)', ' (musician)', ' (guitarist)', ' (saxophonist)', ' (bassist)']
    soup = BS(response, 'lxml')
    if soup.find('table', {'class': 'infobox vcard plainlist'}):
        block_artist_info = soup.find('table', {'class': 'infobox vcard plainlist'})
    elif soup.find('table', {'class': 'infobox biography vcard'}):
        block_artist_info = soup.find('table', {'infobox biography vcard'})

    try:
        response = requests.get(url).text
    except:
        print(f'No info about {artist}')
        return

    soup = BS(response, 'lxml')
    if soup.find('table', {'class': 'infobox vcard plainlist'}):
        block_artist_info = soup.find('table', {'class': 'infobox vcard plainlist'})
    elif soup.find('table', {'class': 'infobox biography vcard'}):
        block_artist_info = soup.find('table', {'infobox biography vcard'})
    else:
        block_artist_info = None

    return block_artist_info


def get_driver():
    if platform.system() == 'Windows':
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    elif platform.system() == 'Darwin':
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    elif platform.system() == 'Linux':
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'

    option = webdriver.ChromeOptions()
    option.add_argument("--lang=en")
    # options for headless
    #option.add_argument("--headless")
    #option.add_argument("--remote-debugging-port=9222")
    #option.add_argument("--disable-gpu")

    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option('useAutomationExtension', False)
    # option for not headless
    option.add_argument("window-size=1366")
    option.add_argument(f"user-agent={user_agent}")

    option.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=option)
    driver.set_page_load_timeout(60)

    return driver


def get_info_from_deezer(artist, wiki_info):
    print("dddone")
    try:
        url = f"https://www.deezer.com/search/{artist.replace(' ', '%20')}/artist"
        driver = get_driver()
        driver.get(url)
    except:
        print(f'{artist} no Deeze page')
        return wiki_info
    accept_cookie_button_xpath ='/html/body/div[1]/div/div[5]/div/button[1]'
    try:
        element = WebDriverWait(driver, 300, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'heading-4')))
    finally:
        print("hello")
    time.sleep(1)
    try:
        driver.find_element_by_xpath('/html/body/div[1]/div/div[5]/div/button[1]').click()
    except:
        print('No button for clicking on Deezer')
    page = driver.page_source
    soup = BS(page, 'lxml')
    try:
        artist_page_link = soup.find('div', class_='heading-4').find('a').get('href')
        artist_page_link = f"https://www.deezer.com{artist_page_link}"
        # writing deezer link
        wiki_info['Deezer'] = artist_page_link
        driver.get(artist_page_link)
    except:
        print(f'{artist} no Deeze link')
        driver.close()
        return wiki_info
    time.sleep(1)
    try:
        element = WebDriverWait(driver, 60, 1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/main/div[5]/div[1]/div[2]/div[1]/div/div[2]/div/div[2]')))
    except:
        print(f'Cant get Deezer info for {artist}')
        driver.close()
        return wiki_info
    finally:
        print("hi")
    time.sleep(1)
    artist_page = driver.page_source
    soup = BS(artist_page, 'lxml')
    try:
        artist_fans_number = soup.find('div', class_='_2kEwD ellipsis').text.replace(',', '')
        artist_fans_number = artist_fans_number.split(' ')[0]
        wiki_info['Deezer fans number'] = artist_fans_number
        print(f'Artist fans number is {artist_fans_number}')
        driver.close()
    except:
        print(f'{artist} no fans number info')
        driver.close()
    return wiki_info


def get_info_from_spotify(artist, wiki_info):
    url = f"https://open.spotify.com/search/{artist.replace(' ', '%20')}"
    driver = get_driver()
    driver.get(url)
    # waiting for our element loading
    try:
        element = WebDriverWait(driver, 200, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'c65f5ba184497ced74470e887c6a95c3-scss')))
    except:
        print(f'{artist} no spotify info')
        wiki_info = get_info_from_deezer(artist, wiki_info)
        driver.close()
        return wiki_info
    time.sleep(1)
    page = driver.page_source
    # going to artist page
    soup = BS(page, 'lxml')
    try:
        artist_page_url = soup.find('a', {'title': {artist}}).get('href')
        if artist_page_url:
            print('We got url')
        else:
            print('no url')
        spotify_link = f"https://open.spotify.com{artist_page_url}"
        wiki_info['Spotify'] = spotify_link
        driver.get(spotify_link)
        # waiting for our element loading
        time.sleep(1)
        try:
            element = WebDriverWait(driver, 90, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, "c6287512c50a737d01bd9db32b301fab-scss")))
        except TimeoutError:
            print(f'No spotify info')
            wiki_info = get_info_from_deezer(artist, wiki_info)
            return wiki_info
        time.sleep(1)
        artist_page = driver.page_source
        # Searching for month listeners
        soup = BS(artist_page, 'lxml')
        all_spans = soup.findAll('span')
        if all_spans:
            print('We got spans')
        else:
            print('no spans')
        if all_spans[9].text.strip() == 'Verified Artist':
            listeners_on_spotify = all_spans[11].text.replace(',', '').split(' ')[0]
        else:
            listeners_on_spotify = all_spans[9].text.replace(',', '').split(' ')[0]
        wiki_info['Listeners on spotify'] = listeners_on_spotify
        # Searching for most popular song
        most_popular_song_listening = soup.find('div', {"aria-colindex": "3"}).find('div').text
        wiki_info['Most popular song listenings on Spotify'] = most_popular_song_listening.replace(',', '')
        driver.close()
    except:
        print(f'{artist} no spotify info')
        #driver.close()
        wiki_info = get_info_from_deezer(artist, wiki_info)
        return wiki_info
    wiki_info = get_info_from_deezer(artist, wiki_info)

    return wiki_info

def get_info_from_wiki(artist, wiki_info, die_born_flag):
    # getting  Instruments (Wiki), First Year Active (Wiki), Last Year Active (Wiki), Genres , Labels, Wiki
    url = f"https://en.wikipedia.org/wiki/{artist.replace(' ', '_')}"
    wiki_info['Artist'] = artist

    musicians_skills = [' (composer)', ' (musician)', ' (guitarist)', ' (saxophonist)', ' (bassist)']

    block_artist_info = get_request(url, artist)
    if block_artist_info:
        pass
    else:
        for skill in musicians_skills:
            url = f"https://en.wikipedia.org/wiki/{(artist + skill).replace(' ', '_')}"
            print(url)
            block_artist_info = get_request(url, artist)
            if block_artist_info:
                break

    try:
        info_lines = block_artist_info.findAll('tr')
        wiki_info['Wiki'] = url
    # est no tupit [The Bad Plus, Alboran Trio, Benedikt Jahnel, Allan Holdsworth, Mammal Hands
        for i in range(0, len(info_lines)):
            if info_lines[i].find('th'):
                if die_born_flag:
                    if info_lines[i].find('th').text == 'Born':
                        compiler = re.compile(r'([\w]+) (\d{2}) (\d{4})(.*)')
                        # info_lines[i].find('td').text.split(')')[1].split('(')[0].replace(',', '')
                        # December 15 1911Wichita Kansas U.S.
                        born = compiler.search(info_lines[i].find('td').text.replace(',', ''))
                        wiki_info['Born'] = f'{born.group(2)} {born.group(1)} {born.group(3)}'
                    elif info_lines[i].find('th').text == 'Died':
                        # info_lines[i].find('td').text
                        died = info_lines[i].find('td').text.replace(',', '')
                        died = died.split('(')[0]
                        died = died.split(' ')
                        wiki_info['Died'] = f'{died[1]} {died[0]} {died[2]}'
                if info_lines[i].find('th').text == 'Instruments':
                    if info_lines[i].find('li'):
                        length = len(info_lines[i].findAll('li'))
                        print(f'Instruments {length}')
                        instruments_list = [info_lines[i].findAll('li')[e].text for e in range(0, length)]
                        wiki_info['Instruments'] = str(instruments_list)[1:-1].replace("'", "")
                    else:
                        wiki_info['Instruments'] = info_lines[i].find('td').text.replace(',', '')

                elif info_lines[i].find('th').text == 'Genres':
                    length = len(info_lines[i].findAll('a'))
                    print(f'Genres {length}')
                    if length == 1:
                        wiki_info['Genres'] = info_lines[i].find('a').text
                    elif length > 1:
                        genres_list = [info_lines[i].findAll('a')[e].text for e in range(0, length)]
                        wiki_info['Genres'] = str(genres_list)[1:-1].replace("'", "")
                    else:
                        wiki_info['Genres'] = info_lines[i].find('td').text

                elif info_lines[i].find('th').text == 'Labels':
                    if info_lines[i].findAll('a'):
                        length = len(info_lines[i].findAll('a'))
                        print(f'Labels {length}')
                        labels_list = [info_lines[i].findAll('a')[e].text for e in range(0, length)]
                        print(labels_list)
                        wiki_info['Labels'] = str(labels_list)[1:-1].replace("'", "")
                    elif info_lines[i].findAll('li'):
                        length = len(info_lines[i].findAll('li'))
                        print(f'Labels {length}')
                        labels_list = [info_lines[i].findAll('a')[e].text for e in range(0, length)]
                        wiki_info['Labels'] = str(labels_list)[1:-1].replace("'", "")
                    else:
                        wiki_info['Labels'] = info_lines[i].find('span').text
            if info_lines[i].find('span'):
                if info_lines[i].find('span').text == 'Years active':
                    years_active = info_lines[i].find('td').text.replace('–', ' ')
                    print(years_active)
                    wiki_info['First Year Active'] = years_active.split(' ')[0].split('(')[0]
                    if years_active.split(' ')[1][-1] == ']':
                        wiki_info['Last Year Active'] = years_active.split(' ')[1][:-3]
                    else:
                        wiki_info['Last Year Active'] = years_active.split(' ')[1].split('(')[0]
    except:
        print(f'{artist} no wiki info')

    wiki_info = get_info_from_spotify(artist, wiki_info)

    return wiki_info


def get_info_form_last_fm(artist):
    # getting Listeners, Scrobbles, Latest Release, Born, Died, Last fm
    wiki_info = {}
    die_born_flag = None
    url = f"https://www.last.fm/music/{artist.replace(' ', '+')}"
    wiki_info['Last FM'] = url
    try:
        response = requests.get(url).text
    except:
        print(f'No info about {artist}')
        return
    try:
        soup = BS(response, 'lxml')
        block_artist_info = soup.find('div', {'class': 'header-new-content'})

        listeners_on_last = block_artist_info.findAll('abbr')[0].text.replace(',', '')
        print(listeners_on_last)
        if listeners_on_last[-1] == 'K':
            listeners_on_last = float(listeners_on_last[:-1]) * 1000
            listeners_on_last = int(listeners_on_last)
        elif listeners_on_last[-1] == 'M':
            listeners_on_last = float(listeners_on_last[:-1]) * 1000000
            listeners_on_last = int(listeners_on_last)

        wiki_info['Listeners on LastFM'] = listeners_on_last

        scrobbles = block_artist_info.findAll('abbr')[1].text.replace(',', '')
        print(scrobbles)
        if scrobbles[-1] == 'K':
            scrobbles = float(scrobbles[:-1]) * 1000
            scrobbles = int(scrobbles)
        elif scrobbles[-1] == 'M':
            scrobbles = float(scrobbles[:-1]) * 1000000
            scrobbles = int(scrobbles)

        wiki_info['Scrobbles'] = scrobbles
        latest_info = block_artist_info.find('h3', {'class': 'artist-header-featured-items-item-name'})
        wiki_info['Latest Release'] = latest_info.find('a').text
    except:
        print('No Listeners Scrobbles Latest Release info')

    try:
        born_died_block = soup.find('dl', {'class': 'catalogue-metadata'})
        born_died_info = born_died_block.findAll('dd')
        if len(born_died_info) == 2:
            if re.search('present', born_died_info[0].text.split('(')[0]):
                pass
            else:
                wiki_info['Born'] = born_died_info[0].text.split('(')[0]
        elif len(born_died_info) == 3:
            wiki_info['Born'] = born_died_info[0].text
            compiler = re.compile(r'([\w ]+) ([(])*')
            died = compiler.search(born_died_info[2].text)
            wiki_info['Died'] = died.group(1)
    except:
        print(f'{artist} no born, died info')
        die_born_flag = True

    full_info = get_info_from_wiki(artist, wiki_info, die_born_flag)

    return full_info


"""def info_searching(artists_list):
    full_info = []
    a = 0
    for artist in artists_list:
        print(a)
        wiki_info = get_info_form_last_fm(artist)
        full_info.append(wiki_info)
        a += 1
    print(full_info)
    return full_info"""


def main():
    with open('Artist-Search.csv', encoding='utf8') as csv_f:
        file_reader = csv.reader(csv_f)
        artists_list = [row[0] for row in file_reader]
        artists_list.pop(0)

    """with open('Artist1.csv', 'w', encoding='utf8', newline='') as csv_f:
        file_writer = csv.writer(csv_f, delimiter=',')
        i = 0
        for e in range(0, len(artists_list)):
            file_writer.writerow(artists_list[e])

            i += 1
            if i == 100:
                break"""
    full_info = []
    # multiprocessing.cpu_count()
    with multiprocessing.Pool(6) as process:
        full_info = process.map(get_info_form_last_fm, artists_list)
    print(full_info)
    #full_info = info_searching(artists_list)

    with open('result.csv', 'w', encoding='utf8', newline='') as csv_file:
        fieldnames = ['Artist', 'Instruments', 'First Year Active', 'Last Year Active', 'Genres', 'Labels',
                      'Listeners on LastFM', 'Listeners on spotify',
                      'Most popular song listenings on Spotify',
                     'Scrobbles', 'Deezer fans number', 'Latest Release', 'Born', 'Died', 'Last FM', 'Wiki', 'Deezer',
                      'Spotify']

        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for row in full_info:
            writer.writerow(row)

    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':
    main()

# Artist,Instruments,First Year Active,Last Year Active,Genres,Labels,Listeners on LastFM, Listeners on spotify for month, Most popular song listenings on Spotify,Scrobbles,Latest Release,Born,Died,External Links,Website