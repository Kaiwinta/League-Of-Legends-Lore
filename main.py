import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from multiprocessing import Pool

BASE_LORE_URL = "https://universe.leagueoflegends.com/"

POOL_SIZE = 10

LANGUAGES = ["en_US", "en_GB", "en_AU", "es_MX", "es_ES", "de_DE", "fr_FR", "it_IT", "pl_PL", "el_GR", "ro_RO", "hu_HU", "cs_CZ", "pt_BR", "ja_JP", "ru_RU", "tr_TR", "ko_KR", "vn_VN", "zh_TW", "th_TH"]

def scrape_champions_names_and_lore(Lang="en_US"):
    url = BASE_LORE_URL + Lang + "/champions/"
    driver = selenium.webdriver.Chrome()
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    # scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(2)

    champions_content = []

    champions_row = driver.find_elements(By.CLASS_NAME, "champsListUl_2Lmb")
    for row in champions_row:
        champions = row.find_elements(By.TAG_NAME, "li")
        for champ in champions:
            champ_url = champ.find_element(By.TAG_NAME, "a").get_attribute("href")
            champ_image = champ.find_element(By.CLASS_NAME, "itemContent_3olR").get_attribute("innerHTML").split("data-am-url=\"")[1].split("\"")[0]
            name = champ.text.split("\n")[0].lower()
            name = name[0].upper() + name[1:]
            region = champ.text.split("\n")[1].lower()
            region = region[0].upper() + region[1:]
            champion = { "name": name, "region": region, "image_url": champ_image, "champ_url": champ_url}
            champions_content.append(champion)

    for i in range(0, len(champions_content), POOL_SIZE):
        with Pool(POOL_SIZE) as p: 
            results = p.starmap(scrape_one_champions_lore, [(champion["champ_url"], Lang) for champion in champions_content[i:i+POOL_SIZE]])
            for j in range(len(results)):
                champions_content[i+j]["lore"] = results[j]

    with open(f"data/Lore_{Lang}.json", "w", encoding="utf-8") as f:
        import json
        json.dump(champions_content, f, indent=4, ensure_ascii=False)
    driver.quit()


def scrape_one_champions_lore(champ_url, Lang):
    url = champ_url.replace("champion", "story/champion")
    driver = selenium.webdriver.Chrome()
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    # scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(2)
    content = driver.find_element(By.ID, "CatchElement").text
    driver.quit()
    return content

if __name__ == "__main__":
    for lang in LANGUAGES:
        scrape_champions_names_and_lore(lang)