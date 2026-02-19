
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from multiprocessing import Pool
from os import path
import json
import argparse


BASE_LORE_URL = "https://universe.leagueoflegends.com/"

POOL_SIZE = 5

LANGUAGES = ["en_US", "en_GB", "en_AU", "es_MX", "es_ES", "de_DE", "fr_FR", "it_IT", "pl_PL", "el_GR", "ro_RO", "hu_HU", "cs_CZ", "pt_BR", "ja_JP", "ru_RU", "tr_TR", "ko_KR", "vn_VN", "zh_TW", "th_TH"]

def smart_scroll(driver, pause=0.5, max_attempts=20):
    last_height = 0
    for _ in range(max_attempts):
        height = driver.execute_script(
            "return document.documentElement.scrollHeight"
        )
        if height == last_height:
            break

        driver.execute_script(
            "window.scrollTo(0, document.documentElement.scrollHeight);"
        )
        sleep(pause)
        last_height = height

def load_saved_champions_with_lore_data(Lang) -> dict:
    if path.isfile(f"data/Lore_{Lang}.json"):
        with open(f"data/Lore_{Lang}.json", "r", encoding="utf-8") as file:
            content = file.read()
            champions_saved = json.loads(content)
            filtered_champions_saved = [champion for champion  in champions_saved.values() if "lore" in champion.keys() and len(champion["lore"]) > 0]
            champions_saved = {}
            for champ in filtered_champions_saved:
                champions_saved[champ["name"]] = champ
            return champions_saved
    return {}

def scrape_champions_names_and_lore(Lang):
    url = BASE_LORE_URL + Lang + "/champions/"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    # scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(3)
    
    print(f"Loading {Lang} champions names and lore...")
    saved_champions_content = load_saved_champions_with_lore_data(Lang)
    champions_content = {}

    print(f"Scraping {Lang} champions names and lore...")
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
            champion = { "name": name, "region": region, "image_url": champ_image, "champ_url": champ_url, "lore": ""}
            champions_content[name] = champion
    
    filtered_champions_content = [champion for champion in champions_content.values() if champion["name"] not in saved_champions_content.keys()]

    for i in range(0, len(filtered_champions_content), POOL_SIZE):
        with Pool(POOL_SIZE) as p: 
            results = p.starmap(scrape_one_champions_lore, [(champion["champ_url"], champion["name"], Lang) for champion in filtered_champions_content[i:i+POOL_SIZE]])
            for j in range(len(results)):
                champions_content[results[j][0]]["lore"] = results[j][1]
    for champ_name in champions_content:
        if champ_name in saved_champions_content.keys():
            champions_content[champ_name]["lore"] = saved_champions_content[champ_name]["lore"]

    with open(f"data/Lore_{Lang}.json", "w", encoding="utf-8") as f:
        json.dump(champions_content, f, indent=4, ensure_ascii=False)
    print(f"{Lang} champions lore scraped and saved successfully.")
    driver.quit()


def scrape_one_champions_lore(champ_url, champ_name, Lang) -> tuple:
    url = champ_url.replace("champion", "story/champion")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    # scroll to trigger lazy loading
    smart_scroll(driver, pause=1, max_attempts=10)
    sleep(1)
    content = driver.find_element(By.ID, "CatchElement").text
    driver.quit()
    return (champ_name, content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape League of Legends champions lore in different languages.")
    parser.add_argument("--languages", nargs="+", help="List of languages to scrape (e.g., en_US es_ES de_DE). If not provided, all languages will be scraped.")
    parser.add_argument("--pool-size", type=int, default=POOL_SIZE, help="Number of parallel processes to use for scraping champion lore. Default is 5.")
    args = parser.parse_args()
    if args.pool_size:
        POOL_SIZE = args.pool_size
    if args.languages:
        LANGUAGES = args.languages
    for lang in LANGUAGES:
        scrape_champions_names_and_lore(lang)   