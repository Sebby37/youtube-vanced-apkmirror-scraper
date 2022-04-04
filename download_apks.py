from bs4 import BeautifulSoup as soup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser
from time import sleep
from os import system, path
from requests import get
from warnings import filterwarnings
from traceback import format_exc

filterwarnings("ignore", category=DeprecationWarning)

'''
IMPORTANT:
- THE DOWNLOAD LINK WORKS WITH REQUESTS
- if a file has the format apkm, it can be renamed to .apks
- Also maybe call an os.rename on the downloaded file to make it's version more clear (or not to preserve original formatting)
- Do the below url instead where there are 4 pages but there is every bit of vanced software:
    - https://www.apkmirror.com/uploads/?devcategory=team-vanced
- The sleeps are because cloudflare is rate limiting and preventing the program from getting the request data
- Download rate limiting began around getting download #48
- I become unable to get any pages after download #59
'''

'''
TODO:
- Instead of using the browser to automatically download the apks, click the "here" link in the downloads page to get the
'''

RATE_LIMIT_PAUSE = .5

def main(url):
    # Setting up the webdriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {"download.default_directory": "apks", "download_restrictions": 3})
    options.add_extension("ublock-origin.crx")
    driver = webdriver.Chrome(options=options)
    apks_list_final = []
    dl_urls_list = []

    # Getting a list of all download urls
    if not path.exists("apks_list.txt"):
        for i in range(4):
            driver.get(url if i == 0 else url.replace("/uploads", f"/uploads/page/{i+1}"))
            sleep(RATE_LIMIT_PAUSE)
            apks_list = soup(driver.page_source, "html.parser")
            apks_list = apks_list.find_all("div", {"class": "iconsBox"})

            for elm in apks_list:
                try: apks_list_final.append("https://apkmirror.com" + elm.find_all("a")[1].get("href"))
                except IndexError: pass
    else:
        apks_list_final = open("apks_list.txt").read().split("\n")
    
    system("cls")

    open("apks_list.txt", "w+").write("\n".join(apks_list_final))

    try: apks_list_begin = len(open("download_urls_incomplete.txt").readlines())
    except: apks_list_begin = 0

    if not path.exists("download_urls.txt"):
        for i, link in enumerate(apks_list_final[apks_list_begin:]):
            #pause()
            driver.get(link + "#download")
            dl_name = link.split("/")[-2]
            print(f"{i+1+apks_list_begin}/{len(apks_list_final)}) Downloading {dl_name}")
            dl_url = None

            try:
                dl_url = driver.find_element_by_class_name("downloadButton")#.get_attribute("href") # Clicking the download button
                if dl_url.tag_name != "a": 
                    dl_url = None
                    raise Exception

                driver.get(dl_url)#driver.execute_script(f"window.open(\"{dl_url}\");")
                print("Found immediate dl button")
                #print("-" * 20)
                continue
            except:
                dl_url = None
                print("No immediate dl button found")
                pass
            
            if not dl_url:
                print("Navigating to dl page")
                accent_color_elms = driver.find_elements_by_class_name("accent_color")
                dl_page_navigated = False
                for url in accent_color_elms:
                    cur_accent_url = url.get_attribute("href")
                    if cur_accent_url is not None and dl_name in cur_accent_url and "apk-download" in cur_accent_url:
                        dl_page_navigated = True
                        url.click()
                        sleep(RATE_LIMIT_PAUSE)
                        break

                if not dl_page_navigated:
                    print("Could not navigate to download page!", accent_color_elms)
                    print("-" * 20)
                    continue
                #driver.find_elements_by_class_name("accent_color")[-1].click() # Getting to the download page
                print("Clicking dl button")
                dl_url = driver.find_element_by_class_name("downloadButton").get_attribute("href") # Clicking the download button
                driver.get(dl_url)
                sleep(RATE_LIMIT_PAUSE)

            # Getting the apk download url that works with requests
            print("Getting static download url")
            cur_href = ""
            #e = "\n".join([str(i.get_attribute("href")) for i in driver.find_elements_by_tag_name("a")[::-1]])
            #print(e)
            for url in driver.find_elements_by_tag_name("a")[::-1]:
                cur_href = url.get_attribute("href")
                if "download.php" in str(cur_href):
                    #driver.get(cur_href)#dl_url = url.get_attribute("href")
                    sleep(RATE_LIMIT_PAUSE)                
                    dl_url = cur_href if "wp-content" in cur_href.lower() else driver.current_url
                    print("Static download url found! Using " + "cur_href" if "wp-content" in cur_href.lower() else "driver.current_url")
                    cur_href = None
                    break
            
            #print(dl_url)
            dl_url = driver.current_url if cur_href else dl_url
            dl_urls_list.append(f"{i+1+apks_list_begin}) {dl_name} | {dl_url}")
            print(f"Successfully finished on url '{dl_name}'\nDL URL: '{dl_url}'\nCur URL: '{driver.current_url}'")
            sleep(RATE_LIMIT_PAUSE)
            print("-" * 20)
            #break

            # Below code uses string manipulation to hopefully get a dl url, that appears to return 404 on some dls so I'll be using selenium to navigate to the download button
            '''link = link + link.split("/")[-2].replace("release", "android-apk-download/download") # needs reworking to work with other vanced stuff
            #print(link, "\n")#, link.split("/"), "\n")
            print(f"Downloading {dl_name} | {link}")
            driver.get(link)
            if "<h1>404</h1>" in str(soup(driver.page_source, "html.parser")):
                print(f"404 at {dl_name} | {link}")
            else: print(f"Success downloading {dl_name} | {link}")'''
        # TODO: Close current webdriver, create new one that allows downloads, download all dl urls
        print("\n".join(dl_urls_list))
        open("download_urls.txt", "w+").write("\n".join(dl_urls_list))
    driver.quit()

    ''' Downloading all the apks '''
    # Setting up the webdriver
    download_options = webdriver.ChromeOptions()
    download_options.add_experimental_option("prefs", {"download.default_directory": "apks"})
    download_driver = webdriver.Chrome(options=download_options)
    # Dictionary containing the download status of each download 
    download_statuses = {}
    if path.exists("download_statuses.txt"):
        with open("download_statuses.txt") as status_file:
            for status in status_file.read().split("\n"):
                cur_num = status.split(": ")[0]
                cur_status = status.split(": ")[-1]
                download_statuses[cur_num] = cur_status
    print("Downloading apks...")
    with open("download_urls.txt") as dl_urls:
        for i, cur_line in enumerate(dl_urls.read().split("\n")):
            if float(i) == 50:
                print("!!!WARNING, CLOUDFLARE WILL PROBABLY BEGIN RATE LIMITING NOW!!!")
            # Getting the string values needed
            cur_url = cur_line.split("| ")[-1]
            cur_num = cur_line.split(")")[0]
            cur_name = cur_line.split(" ")[1]
            print(f"{cur_num}) DOWNLOADING '{cur_name}'...")

            # Rerunning the download if the entry for it in the download_statuses dict is blocked due to cloudflare
            try:
                if download_statuses[cur_num] == "Cloudflare":
                    print("Download was previously blocked by Cloudflare, retrying...")
                else:
                    # TODO: Probably check the apks folder to see if the download was actually successful instead of assuming that the dictionary was correct
                    # Edit: I don't think that will be possible as the file names are different to the url or 'name'
                    print("Download was previously successful, continuing to next download...")
                    print("-" * 20)
                    continue
            except:
                print("No entry for this download's status exists, continuing download...")

            # Getting the download page of the apk
            download_driver.get(cur_url)

            # Detecting if cloudflare has rate limited the program
            if "cloudflare" in download_driver.page_source.lower() or "rate" in download_driver.page_source.lower() or "limit" in download_driver.page_source.lower() or "request" in download_driver.page_source.lower():
                print("ERROR: CLOUDFLARE IS RATE LIMITING!")
                download_statuses[cur_num] = "Cloudflare"
            else:
                print("DOWNLOAD SUCCESSFUL!")
                download_statuses[cur_num] = "Success"
            print("-" * 20)

    print("Apks downloaded!")
    pause()
    #download_driver.quit()
    # Saving the dictionary to a file
    with open("download_statuses.txt", "w+") as status_file:
        for status in download_statuses:
            status_file.write(f"{status}: {download_statuses[status]}\n")

if __name__ == "__main__":
    pause = lambda: system("pause")
    try: main("https://www.apkmirror.com/uploads/?devcategory=team-vanced")
    except KeyboardInterrupt: pass
    except Exception as e: print(e, "\n", format_exc())
    #pause()
