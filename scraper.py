import requests
import logging
import time
from bs4 import BeautifulSoup

RATE_LIMITING = 0


def connectedToInternet():
    """
    :return: True if connected otherwise false
    """
    status_code = 0
    try:
        status_code = requests.get("http://www.google.com").status_code
    except requests.exceptions.ConnectTimeout:
        logging.warning("Connection timed out [ConnectionTimeOut]")
    except requests.exceptions.ConnectionError:
        logging.warning("Cannot connect to internet [ConnectionError]")

    return status_code == 200


def query(url, params=None, headers_param=None):
    """
    queries the given url and places in the params and headers into the request if present.
    :param url: string
    :param params: dict
    :param headers_param: dict
    :return: string of body of the request result
    """
    if params is None:
        params = {}
    logging.info("url={0}\tparams={1}".format(url, params))
    headers = {
        'Referer': url,
        "Content-Type": "text/xml; charset=UTF-8",  # implement after checking if this doesn't kill the other scripts
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    }
    if headers_param is not None:
        # mergers the headers into one so that the basic headers don't have to duplicated
        for k in headers_param.keys():
            headers[k] = headers_param[k]

    session = requests.session()
    result = session.get(
        url,
        cookies=requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies)),
        headers=headers,
        params=params
    ).text

    time.sleep(RATE_LIMITING)
    return result

def getPlaces():
    places = {}
    results = query("https://www.kent.ac.uk/timetabling/rooms/")
    soup = BeautifulSoup(results, "html.parser")
    content = soup.find("div", {"class":"tab-content"})
    if content is not None:
        for table in content.find_all("table"):
            data = table.find_all("td")
            if len(data) == 2:
                name = data[0].find("a").getText()
                if name in places.keys():
                    print("error")
                else:
                    print(name)
                    places[name] = ["https://www.kent.ac.uk/timetabling/rooms/{0}".format(room.get("href")) for room in data[1].find_all("a")]
            else:
                print("error")

    return places

def getRoom(url):
    soup = BeautifulSoup(query(url), "html.parser")
    content = soup.find("div", {"id": "content"})
    if content is not None:
        table = content.find("table")
        if table is not None:
            tds = table.find_all("td")


            image_td = table.find("td", {"align":"center"})
            if image_td is not None:
                img = image_td.find("img").get("src")
            else:
                print("could not find image")

            tds = table.find("td", {"valign":"top"})
            if tds is not None:
                for row in tds.find_all("tr"):
                    line = row.find_all("td")
                    if len(line) >= 2:
                        print(" ".join([v.getText() for v in line]))
            else:
                print("error length")
        else:
            print("error table")

    else:
        print("error parsing")

def main():
    getRoom("https://www.kent.ac.uk/timetabling/rooms/room.html?room=JAR1711")
    # places = getPlaces()
    # for placeName in places.keys():
    #     if len(places[placeName]) != 0:
    #         print(places[placeName])
if __name__ == '__main__':
    main()