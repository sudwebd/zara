# import undetected_chromedriver as uc
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# driver = uc.Chrome()
# driver.get("https://www.zara.com/in/en/high-waist-trf-wide-leg-jeans-with-crossover-waistband-p00250232.html?v1=425257398&v2=2419235")

# # Wait for the element to be visible
# element = WebDriverWait(driver, 20).until(
#     EC.presence_of_element_located((By.CLASS_NAME, "product-detail-view__main"))
# )

# print(element.get_attribute("outerHTML"))  # Print the element's HTML

# driver.quit()


import requests
from bs4 import BeautifulSoup

# HEADERS = {
#     "accept": "application/json",
#     "accept-encoding": "gzip, deflate, br, zstd",
#     "accept-language": "en-US,en;q=0.9",
#     "cache-control": "no-cache",
#     "content-type": "application/json",
#     "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
# }

COOKIES = {
"826b75e46a856af63aa6a715b40616e7"	:	"86c30b0a13cc52c06f2265dc029d1f62"	,
"IDROSTA"	:	"d039e0004b9f:1405af2d180f4f54d611f571a"	,
"ITXDEVICEID"	:	"93b3e3e05ba48e8c6341544bc81a5785"	,
"ITXSESSIONID"	:	"f0c999a0a07ea7b424cef9f890c47aa4"	,
"OptanonAlertBoxClosed"	:	"2024-12-12T13:43:32.615Z"	,
"OptanonConsent"	:	"isGpcEnabled=0&datestamp=Thu+Dec+12+2024+19%3A13%3A34+GMT%2B0530+(India+Standard+Time)&version=202401.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=b54d0a0d-049d-403f-81cc-812476bcf8d9&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=IN%3BKA&AwaitingReconsent=false"	,
"TS0122c9b6"	:	"01b752f41eebe5c85dcdac444c22249b8759d76862d947cd272f4f20828161790c80024aa05f2175d5eec7e0eec9d654fa090ac599"	,
"UAITXID"	:	"a2cb9795b3b0e98f5d2994748230d97de927779c2d35e8d3de64ce988632e7eb"	,
"_ALGOLIA"	:	"anonymous-14637dfb-c8dc-43da-9986-1f625661af63"	,
"_abck"	:	"218463D6243CBD2F4AFB624A328D7452~0~YAAQl9cLFyEspbSTAQAA+z0luw3DN2kLUsw+9+xeRwobISIdpexFZw/XOZsMLL3nHEdwQ+4vaGnmqBtkisaoQpR/taYOkFIyw2DQzOP0dFuHRPuK8TezepEUycUCEWS8KjxLb9tSu0FJAVmsc/ijdO2I/pe6ZyRA54Qj1iQ2Oo0B2n8fwdGOrSMu7qQyZ0LwxNPGWzpzE3QUdEk8DepQLVU3wWmvDIPXJfUR7raTL3o+IXbi4yQ1IsxoUI7UsvPKbjFB/yYH6Tcyg4goYnECUTgIFvpMgU8FntfhxmrzXpwFisbz4og7rU48+4ReGVqB9ZnJImeiIpITlpJ1pXUj0xol7IbOv9ImTC78Y+j2BYd0b/Q1muUDSPzJOtaQFBhw5W14pbFXj1n+tb52pSJa6FTJYv5hwK0VDfEtRRbeX7UrmRbSvXyOGshl6tYqRfKUOHQaN2ZppLKNRQmcx39lnjv23cdwJHKz/Y/mMRd+lA8s0/P/tVyZDJJxCblfTe1nC2OrK9fjP6fU/QwYoNNe282URQMly5gHG+EfLc6HMN6WsIU1msGiKm7f5TKCoRP1EA6p2CLp3bYpCrNf66EPCrfwiVbYG3u0toMa/0XgUcgO9tmS9nltjMYs/WFk9Zwv7U8wFwrTrYjAE3x8HdcT3gyUiRcsC828aJW6tvWvCyahZto0TrkuLPJlBA==~-1~-1~1734015200"	,
"_fbp"	:	"fb.1.1733997314481.344839511546255515"	,
"_ga"	:	"GA1.1.656912573.1733997197"	,
"_ga_HCEXQGE0MW"	:	"GS1.1.1734011014.3.0.1734011014.60.0.0"	,
"_ga_NOTFORGA4TRACKING"	:	"GS1.1.1734011013.4.0.1734011014.0.0.31563021"	,
"_gcl_au"	:	"1.1.1358345033.1733997196"	,
"_itxo11y_id.01fa"	:	"c7538edf-ba59-4411-b069-d4d774b86dca.1733997192.1.1734011734..f91cb8d2-f4d2-4869-a184-8df0cb7acfa1..8105c233-1355-49d6-87f1-e431439534a1.1733997192491.524"	,
"_itxo11y_ses.01fa"	:	"*"	,
"ak_bmsc"	:	"66EE5CF5365B1B52C1BA596A5956D2D5~000000000000000000000000000000~YAAQl9cLF3Qco7STAQAAfk4cuxrgGooNgdp+Pdy9MA2BUSLR9FLrY4gsYBC3pt7e1CZQuMyCzJaQy+I8r2LzwA+bp5SJ51DTPXlapkA1uWBD4uwAN60FGlw56k+32dnx8M6gwnX81cMqw8XSwErHd+lkvMV1RxKPQzJe/SiHXehX5aV/LdYOIno0FhEYp7r8tvbQ1d48QpVucDvJnSwV0MTqs1iaBe6qi+rTFPFI6IStfbzgmX+9lHwSBrSocthGQ2IHI59avpOEf/+Ty0rLKzz//YWd72QONgZaO8kn7pFvM16FIGJ+x4JSWsCnthu2epCb9hymtx5ADm8IKJ7X0GErYJLNxyJTagv03AYNRnOqVIr1b8FBQdP3iC6aW47CRcW+FS/lu8OJ0qI7J1hSZHamxhg0jEKKAH/h9nZl9ZReRigzK673BwmfQ651BwZlE8+U5hq4Hg9/mozCDfZnpos8q2s0vLRAwO8AbcS7pazCJEPqfNqmH773Idgp9f0y0AWyqCKGX8DVuJ23U5moQQLqRPPBMxZ/Zz+WBzabznWZbf0AIiZj6mmcyKCpVpO2jtBKcg/9s9PCMW+3cuBEnA=="	,
"ak_bmsc"	:	"CCFB343F7430722420531E9D6844F22A~000000000000000000000000000000~YAAQlNcLF/z1vbKTAQAAN78nuxrkO/2nTJqP8IuvWArleMW5UabTvlt20faDi3ZHcs+AZj5pnnRlV70t7GiP5+1U9S7zXfWpDFgwwROlwMXTBHif/cA44dKHTv9TOWJ39mlVRsMFf76l0/74IYXz3D6KBG0wHqZMddkx5/tuKeek1XdQl5HfqER/MgjE9QkvVn0Z0hok3iZtLj1PmAtpuyuX+h8qOU6wj4dqnPYJblIKlJONzYoal56WmCKeBZI/Lf3ajzOC66L6IkcFUFddhOPKcv97i/ri4NO7sMczHYymkeQkC8KCedTtNF7WvB5TW9ZhVPxMPIORcmvQjGYpRjNQji3I4zej6XXPGqeA9zpc/XbcZVE42NS/Cwp3gDIW3sUISjhQhCFM"	,
"bm_lso"	:	"A55035593DFA4F71A04E1FF13633F9F3B0D24AC1E6CA4ED7CAD77F7765E4B1AF~YAAQl9cLF6MYo7STAQAAbkIcuwGiKd0LLEt6zbIimylzTgi6qeeNMpaGbOKcTnKzQslGs3/BZrG5gZFGFbEK210Yr35nd+cdOtmWy/5wIu3WWoABbs5e/hO4ER89qR48w/vbHhBHNHbr0i9A1CY/diDise5gDHF8eF1WrkXfY40dwEU1KaNDdiJslxVpY0/YqZmpqb8CUwzCW2L3wdeK+TZSMk4Up5cSXk73kapgzC3dU/JJDa2+3f+xPWVruhRmCznTGUCpnXit9VAO9Ut3y3Ynz8uLgrWeYV6EDkOv0PU/uNYieiUrDdWqRT+fnWo3hvQnDHEDs73ihWGPInj08d7CkEruTNMi1k7UVZLD+7Lyigu56KwdZiOOB3q9PNIVluHU3xfeosS+PhhMjnvraeTA0plpbPiyhpQUgtZKK4pTfg04Mh+TUYzNHKbVbHh525syt8XYKmbXv6mcAA==^1734011018513"	,
"bm_mi"	:	"209141C92740FF23F36F407E98358931~YAAQl9cLF6EYo7STAQAAbkIcuxpjL8gl92XKr2n6EHSSaVsQnwywaxg+tQTSFqsUS5BsDc4SRQmQEqTWhBwxnbdVAFRKQwlU2Fvj73PWG2w8KNJ1L2k9NPpoEdeszUp8X1Jlk356S2TC3jBXE7MHKs/7WVM7+kxWQ8p9URCYGlm3MIPq/90NGVeU/wXlHjq4oWLXIvjumRiyogk5fCfhnprSRLr9REo82w0m9DJfSCifzBbYohkUdB+jeRVVDNiqL1A1o2AYLyGkAUsTLJL6rngkEzJxvH4BBgcb+iImJp1dUhiFWz/g2TzQR35D+egRI/D1lV6txnZzhiHJxNu2NSsXKYhG5rlZUxt2fabGAeZbwjZMhoK3cnAAevosdjjuz8GRGzi36KW4IoNjg525Q2W43U2dPeE=~1"	,
"bm_s"	:	"YAAQl9cLFzUco7STAQAAtU0cuwLa7D6Td4Up8U/kJ53ThzEOxvQbNu/Ax2dB7BMl6CXevcAN3ARWZFE6OimqO1kUj15Yc93LYmORoNF+K9MOkGkIj81RNxWa4HTq/XdWBiICnjOd1e5lYiNo8gCijYjSdvh6ri0IqGDLMkqGm9RFkglImK5KBKXgSO+VmPSCyB7nmCcFLhXH22T5UUQoeqe+1t8+OL/l/pdLwBhgUpIVTFuTQ8FdMgFcaCAMhSfEB1j/FvXBxnsNk9L11x4E6HdLa7hg0+VUhJ/DFtNf6nbj7LnaBbXl4tH83XBk+8afHMZ/ji+1SpMyvJVaUriXCSgF+Kk="	,
"bm_so"	:	"A55035593DFA4F71A04E1FF13633F9F3B0D24AC1E6CA4ED7CAD77F7765E4B1AF~YAAQl9cLF6MYo7STAQAAbkIcuwGiKd0LLEt6zbIimylzTgi6qeeNMpaGbOKcTnKzQslGs3/BZrG5gZFGFbEK210Yr35nd+cdOtmWy/5wIu3WWoABbs5e/hO4ER89qR48w/vbHhBHNHbr0i9A1CY/diDise5gDHF8eF1WrkXfY40dwEU1KaNDdiJslxVpY0/YqZmpqb8CUwzCW2L3wdeK+TZSMk4Up5cSXk73kapgzC3dU/JJDa2+3f+xPWVruhRmCznTGUCpnXit9VAO9Ut3y3Ynz8uLgrWeYV6EDkOv0PU/uNYieiUrDdWqRT+fnWo3hvQnDHEDs73ihWGPInj08d7CkEruTNMi1k7UVZLD+7Lyigu56KwdZiOOB3q9PNIVluHU3xfeosS+PhhMjnvraeTA0plpbPiyhpQUgtZKK4pTfg04Mh+TUYzNHKbVbHh525syt8XYKmbXv6mcAA=="	,
"bm_sv"	:	"90A7481F389DA865B1E78850BDAB8537~YAAQl9cLFykdo7STAQAAKlEcuxrqM3JI9f6/Em/h7UOQG4XNt58FTrgRlzqC3W4uSTkWAs+OcU5cTq5Tn8QHZY6xH95R5ZeA0VggucJEAADuebcHveEdOq2wq5u8nWGf0oTlgYrq1i2YvdH6Odi8l7TMh/ToS337CST4aZdakAgY4v12t5ChXJJHKZjOPSWwubzNBTp6id2MMfjO0BE4Awm9NwCDMUfm1FizgadrbDxK029XXaXcDjtxLwMhiCA=~1"	,
"bm_sz"	:	"FA3A672806CA444E5518D5578AC9C7DB~YAAQl9cLF6UYo7STAQAAbkIcuxprNeFCS+LZD1jVjYgQuI76gBTt1toADTfgwBSEkkPODN7hBQEFWSZ5AxMCNuBVnTCyEy9YVw7IQq9/GBSjvf12IgrhD8Pk8DmRM95XRIQWjBBDaOzPhOF8lZBk/m+HygZgNVcWIC7gpFrxUaTKObeH9GIGQrXbFDx3/hhkSZ1KiH5QNXpE6g0b0bmBVm6n+48pwQBEgPEhXFJI8wB4pUC8w6c203RF6e7FyrBndjUjXrlol+/p6HTbK09uelbROLWZEdqrK+y6ZrnoxxfbPQwg/uN+X9Q6FjTz0hr+nMm/FTr/wPwIz71mDo9o74mJ0rgfHf+V9kPt9/Dfj0Xc4O9JC5gQRM3ZmuDsJbc62zd9xQmGtbJiuDMmHCM+tDvvtVbL5NDwWgwZVUY3+uT9CMeZALjCKXHW1JuoKAQ+s74skRiynswhjE1PWWaCAEWZAseAQDpQeK5DvxHMdp8u9PcrK50tiN+YTzrqFYgxmJEM2GNvhb8pG4MVnZPblt5T9yNdjoL2HqU/sukVAKclwZS3xDuMxgj5kS1EhqQ4Jg8LvAaRNfjimYTSAezxig==~3355185~3553091"	,
"cart-was-updated-in-standard"	:	"TRUE"	,
"gut"	:	"oWT9BQppjcLluQFFo99rMGUB2Hk6jheR%2BTCgAibwRoo%3D"	,
"lastRskxRun"	:	"1734011015422"	,
"migrated"	:	"TRUE"	,
"n_suser"	:	"s%3Aj%3A%7B%22userId%22%3A2002839863496%2C%22userToken%22%3A%22oWT9BQppjcLluQFFo99rMGUB2Hk6jheR%2BTCgAibwRoo%3D%22%2C%22WCTrustedToken%22%3A%22Bearer%3AR%3AC5Sbf4iG4nQx3sXzmWD4g767mR3bfrAkV1VRTLDzK462-A3c18uJzoGpyiSzIsUocTARDiOxXr6LzUecdvIWRULZUhbU5B2mDHafYjGp2EDlP-gKfHBjhyZ2-M79rlM8%22%7D.4G5okcp6YBX67dj4hQrfqB0CXzCKkUPqrk0%2BVfVY1D4"	,
"n_user"	:	"s%3Aj%3A%7B%22userId%22%3A2002839863496%2C%22userToken%22%3A%22oWT9BQppjcLluQFFo99rMGUB2Hk6jheR%2BTCgAibwRoo%3D%22%2C%22WCToken%22%3A%22Bearer%3AR%3AC5Sbf4iG4nQx3sXzmWD4g767mR3bfrAkV1VRTLDzK462-A3c18uJzoGpyiSzIsUocTARDiOxXr6LzUecdvIWRULZUhbU5B2mDHafYjGp2EDlP-gKfHBjhyZ2-M79rlM8%22%2C%22kind%22%3A%22registered%22%2C%22storeId%22%3A11744%7D.e9qM96el0OiiqKUo05BU1oAupv4QKrpz2Nsoy0uRf9k"	,
"optimizelyEndUserId"	:	"oeu1733997196459r0.9943327155348554"	,
"optimizelySession"	:	"0"	,
"prst"	:	"s%3ABearer%3AR%3AlruDkRGbxJlJT7Ehthj3xjs-Qy8KtPKC1ckEpH7UlHZbQ3d-GncYTrRV-f_tHdmlWIdtOUk0ntFsH1XD261Xkt7vUg5Ae8eq8ZyfZuP0YYH9pC0CZ4GoLjR-5Y6lUHEl.MmPTjkDdm2wpEJnVj7nRG5VNogb5fXP01EmJSjQ74Wk"	,
"rCookie"	:	"hnsf73ccsq7swkhf6v8flim4l55pnm"	,
"rid"	:	"f2c0236e-f108-41a5-8c31-79dbc5b72d1e"	,
"rskxRunCookie"	:	"0"	,
"sids"	:	"s%3AYr0HAdSElkFWf9SjqeYUyZMT9X4EoJWT.dUzxSy12vu2l2JW4f9CHtAzbOQY5EVj%2FzBTY8Cge%2F44"	,
"storepath"	:	"in%2Fen"	,
"userType"	:	"registered"	,    
}

# import requests
import brotli
# from bs4 import BeautifulSoup

# import requests
# import brotli
# from bs4 import BeautifulSoup

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
}

def fetch_html_with_debugging(url):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        print(f"\n[DEBUG] Starting fetch for URL: {url}")
        response = session.get(url)
        print(f"[DEBUG] Response Status Code: {response.status_code}")
        print(f"[DEBUG] Content-Type Header: {response.headers.get('Content-Type')}")
        
        # Check Content-Encoding
        content_encoding = response.headers.get("content-encoding", "")
        print(f"[DEBUG] Content-Encoding: {content_encoding}")
        
        raw_content = response.content

        # Decompress Brotli if indicated
        if content_encoding == "br":
            try:
                print("[DEBUG] Brotli compression detected. Attempting decompression...")
                raw_content = brotli.decompress(raw_content)
                print("[DEBUG] Brotli decompression successful.")
            except brotli.error as e:
                print(f"[ERROR] Brotli decompression failed: {e}")
                print("[DEBUG] Falling back to raw content.")

        # Set encoding manually
        try:
            response_text = raw_content.decode("utf-8")
            print("[DEBUG] Response decoded successfully.")
        except UnicodeDecodeError as e:
            print(f"[ERROR] Unicode decode failed: {e}")
            response_text = raw_content.decode("latin-1", errors="replace")
            print("[DEBUG] Decoded using 'latin-1' with errors replaced.")
        
        # Save raw and decoded content for debugging
        with open("debug_raw_output.bin", "wb") as f:
            f.write(response.content)
        with open("debug_decoded_output.html", "w", encoding="utf-8") as f:
            f.write(response_text)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response_text, "html.parser")
        print("[DEBUG] BeautifulSoup object created successfully.")
        
        # Debug: Output a snippet of the HTML
        print(f"[DEBUG] HTML Snippet (first 500 chars):\n{response_text[:500]}")
        
        return soup

    except Exception as e:
        print(f"[ERROR] Failed to fetch or parse the page. Exception {e}")
        return None

# Example usage
url = "https://www.zara.com/in/en/high-waist-trf-wide-leg-jeans-with-crossover-waistband-p00250232.html?v1=425257398&v2=2419235"
soup = fetch_html_with_debugging(url)
all_divs = soup.find_all('div', class_='product-detail-view__main')
print(len(all_divs))  # Number of matching elements

if soup:
    print("\n[INFO] Successfully fetched and parsed the page!")
    print(f"[INFO] Title of the page: {soup.title.string if soup.title else 'No title found.'}")
else:
    print("[ERROR] Failed to fetch or parse the page.")
