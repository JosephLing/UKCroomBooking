import requests
import logging
import time
import csv
from bs4 import BeautifulSoup
from jinja2 import Template

RATE_LIMITING = 2

DEFAULTS = {
    "Campus": "Canterbury"
}
KEY = [
    "name",
    "Campus",
    "Building",
    "Organised by",
    "Type",
    "Capacity",
    "Equipment",
    "Disabled Access",
    "Directions",
    "image",
    "url"
]

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
    content = soup.find("div", {"class": "tab-content"})
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
    room_data = dict([(k, "") for k in KEY])
    soup = BeautifulSoup(query(url), "html.parser")
    content = soup.find("div", {"id": "content"})
    if content is not None:
        table = content.find("table")
        name = content.find("h1")
        if name is not None:
            room_data["name"] = name.g`etText()
        else:
            print("could not find name")
        if table is not None:
            image_td = table.find("td", {"align":"center"})
            if image_td is not None:
                image = image_td.find("img")
                if image is not None:
                    room_data["image"] = "https://www.kent.ac.uk/timetabling/rooms/photos/{0}".format(image.get("src"))
                else:
                    print("no image found")
            else:
                print("could not find image")

            tds = table.find("td", {"valign": "top"})
            if tds is not None:
                for row in tds.find_all("tr"):
                    line = row.find_all("td")
                    if len(line) >= 2:
                        room_data[line[0].getText()] = line[1].getText()
                room_data["url"] = url
                if DEFAULTS["Campus"] != room_data["Campus"]:
                    print("fail")
            else:
                print("error length")
        else:
            print("error table")

    else:
        print("error parsing")

    return room_data


def loadInTemplate():
    data = ""
    with open("index.jina", "r") as f:
        data = f.read()
    return Template(data)

def createCSVFile():
    file = "rooms.csv"
    with open(file, "wb") as f:
        f.write("")

    places = getPlaces()
    for placeName in places.keys():
        if len(places[placeName]) != 0:
            for site in places[placeName]:
                room = getRoom(site)
                # print("creating rooms")
                with open("rooms.csv", "ab") as f:
                    csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL).writerow([room[k] for k in KEY])

def outputAsHtml(data):
    with open("index.html", "wb") as f:
        csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL).writerow(KEY)


def main():
    s = time.time()
    createCSVFile()
    print("finished")
    print(time.time() - s)
    data = loadInTemplate().render(name="hi")
    outputAsHtml(data)

                # rooms.append(getRoom(site))



if __name__ == '__main__':
    main()