import csv
import logging
import time

import requests
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

ROOM_FILE = "rooms.csv"


def error(msg, url):
    logging.error("{0}\tsource: {1}".format(msg, url))


def warning(msg, url):
    logging.warning("{0}\tsource: {1}".format(msg, url))


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
    places = []
    results = query("https://www.kent.ac.uk/timetabling/rooms/roomhint.html", params={"q": ""})
    soup = BeautifulSoup(results, "html.parser")
    for room in soup.find_all("a"):
        places.append("https://www.kent.ac.uk/timetabling/rooms/{0}".format(room.get("href")))

    return places


def getRoom(url):
    room_data = dict([(k, "") for k in KEY])
    soup = BeautifulSoup(query(url), "html.parser")
    content = soup.find("div", {"id": "content"})
    if content is not None:
        table = content.find("table")
        name = content.find("h1")
        if name is not None:
            room_data["name"] = name.getText()
            logging.info(room_data["name"])
        else:
            print("could not find name")
        if table is not None:
            image_td = table.find("td", {"align": "center"})
            if image_td is not None:
                image = image_td.find("img")
                if image is not None:
                    room_data["image"] = "https://www.kent.ac.uk/timetabling/rooms/photos/{0}".format(image.get("src"))
                else:
                    warning("no image found", image_td)
            else:
                error("could not find image", table)

            tds = table.find("td", {"valign": "top"})
            if tds is not None:
                for row in tds.find_all("tr"):
                    line = row.find_all("td")
                    if len(line) >= 2:
                        room_data[line[0].getText()] = line[1].getText()
                room_data["url"] = url
                if DEFAULTS["Campus"] != room_data["Campus"]:
                    warning("not {0} campus".format(DEFAULTS["Campus"]), room_data["name"])
            else:
                error("error length", tds)
        else:
            error("error table", content)

    else:
        error("error parsing", soup)

    return room_data


def writeRow(f, row):
    csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL).writerow(row)


def saveRoom(room):
    row = [room[k] for k in KEY]
    for i in range(len(row)):
        row[i] = row[i].replace("\n", "").replace(u'\xa0', " ").replace(u"\xe9", "e").encode("utf-8")
    with open("rooms.csv", "ab") as f:
        writeRow(f, row)


def loadInTemplate():
    data = ""
    with open("index.jina", "r") as f:
        data = f.read()
    return Template(data)


def createCSVFile():
    with open(ROOM_FILE, "wb") as f:
        writeRow(f, KEY)

    places = getPlaces()

    for site in places:
        saveRoom(getRoom(site))


def outputAsHtml(data):
    with open("index.html", "wb") as f:
        f.write(data)


def main():
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    s = time.time()
    createCSVFile()
    print("finished")
    print(time.time() - s)

    # data = loadInTemplate().render(name="hi")
    # outputAsHtml(data)

    # rooms.append(getRoom(site))


if __name__ == '__main__':
    main()
