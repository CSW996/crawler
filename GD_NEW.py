import math
import shutil
import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re

# 超参数
chrome_options = Options()
chrome_options.add_argument("--headless")

GOV_USER = "" ######
GOV_PSWD = "" ######
FIRST_PAGE_URL = "http://gddata.gd.gov.cn/data/dataSet/toDataSet"
SCREEN_IMG_PATH = "./screenImggd.png"
FOLDER_OF_DOWNLOAD = u"C:\\Users\\901Family\\Downloads"
EXISTED_FILE_NUM = len(os.listdir(FOLDER_OF_DOWNLOAD))
target = ["潮州市", "河源市", "揭阳市", "茂名市",
          "梅州市", "清远市", "汕头市", "汕尾市",
          "韶关市", "阳江市", "云浮市", "湛江市", "肇庆市"]

# 打开浏览器
driver = webdriver.Chrome()
driver.set_window_size(1200, 800)
driver.get(FIRST_PAGE_URL)

"""driver.implicitly_wait(20)
time.sleep(5)

print("访问成功，下面开始用户登陆阶段……")

# 进入登陆页面
driver.find_element_by_id("loginBtn").click()

# 账号&密码 & 验证码输入
driver.find_element_by_id("loginUsername").click()
driver.find_element_by_id("loginUsername").clear()
driver.find_element_by_id("loginUsername").send_keys(GOV_USER)

driver.find_element_by_id("loginPassword").click()
driver.find_element_by_id("loginPassword").clear()
driver.find_element_by_id("loginPassword").send_keys(GOV_PSWD)

driver.find_element_by_id("loginValidCode").click()
driver.find_element_by_id("loginValidCode").clear()
driver.find_element_by_id("loginValidCode").send_keys(result)

driver.find_element_by_id("loginBtnBox").click()

driver.find_element_by_link_text("确定").click()

# 完成登陆跳转
time.sleep(2)

# 开始爬取，清空日志
if os.path.exists("./download.log"):
    with open("./download.log", "w", encoding="utf-8") as f:
        f.close()
"""

"""目标文件获取"""
driver.implicitly_wait(5)
driver.find_element_by_link_text("地方政府").click()
city = driver.find_elements_by_xpath("//*[@class='clearfloat']")[1:]
city_list = [item.text.replace("（", "").replace("）", "").split("\n") for item in city if len(item.text) > 1]

city_num = len(city_list)
city_id = [item.get_attribute("onclick").split("'")[1] for item in city][-city_num:]
for ii in range(len(city_list)):
    # prov, len, id
    city_list[ii].append(city_id[ii])


def obtain_city(city_name):
    city = driver.find_elements_by_xpath("//*[@class='clearfloat']")[1:]
    city_list = [item.text.replace("（", "").replace("）", "").split("\n")[0] for item in city if len(item.text) > 1]
    city_num = len(city_list)
    return city[-city_num:][city_list.index(city_name)]


if os.path.exists("./profile.txt"):
    with open("./profile.txt", "w", encoding="utf-8") as f:
        f.close()

for index in range(len(city_list)):
    city_name = city_list[index][0]
    crawl_page = math.ceil(int(city_list[index][1]) / 6)
    if city_name in target:
        obtain_city(city_name).click()

        for pg in range(1, crawl_page + 1):
            # 获取本页爬取内容的信息
            time.sleep(1)
            dig_in = driver.find_elements_by_xpath('//*[@id="dataSetContent_list"]')[0]
            for li in dig_in.find_elements_by_xpath("li"):
                file_name = li.find_elements_by_class_name("tit_txt")[0].text
                file_url = li.find_elements_by_class_name("tit_txt")[0].get_attribute("href")
                file_abs = li.find_elements_by_class_name("ms_row1")[0].find_elements_by_xpath('span')
                with open("profile.txt", "a", encoding="utf-8") as w:
                    w.write("%s\t%s\t%s\t" % (city_name, file_name, file_url))
                    for item in file_abs:
                        w.write(item.text + "\t")
                    w.write("\n")

            # 下一页
            if pg != crawl_page:
                driver.find_elements_by_class_name("next")[0].click()


"""与已有的文件进行对比，得到缺少的文件"""
profile = pd.read_csv("profile.txt", sep="\t", header=None)
profile.columns = [
    "city", "file_name", "url", "update_date",
    "topic", "bu", "freq", "star", "unknown"
]
for index in range(len(profile)):
    profile.loc[index, "file_name"] = re.sub(r"\+|、|”|“|\(|\)|（|）| |[a-zA-Z]|\.|《|》|Ⅱ", "",profile.loc[index,"file_name"])

PATH_Direction = "" ######
if os.path.exists("./error.log"):
    with open("./error.log", "w", encoding="utf-8") as f:
        f.close()

for city in target:
    city_path = PATH_Direction + city
    if not os.path.exists(city_path):
        os.mkdir(city_path)
    file_exist = os.listdir(city_path)
    file_exist = [re.sub(r"\+|、|”|“|\(|\)|（|）| |[a-zA-Z]|\.|《|》|Ⅱ", "",item) for item in file_exist]
    file_should = profile[profile["city"] == city].reset_index(drop=True)
    for index in range(len(file_should)):
        file_name = file_should.loc[index, "file_name"]
        if file_name not in file_exist:
            with open("error.log", "a") as w:
                w.write("{city}\t{file_name}\t{url}\n".format(
                    city=city,
                    file_name=file_name,
                    url=file_should.loc[index, "url"]
                ))

"""按照上述对比结果，按照url下载"""
file_plus = [line.split("\t") for line in open("error.log").readlines()]
file_plus = pd.DataFrame(file_plus, columns=["city", "file_name", "url"])
file_third = pd.DataFrame()

for index in range(len(file_plus)):
    url = file_plus.loc[index, "url"]
    driver.get(url)
    try:
        time.sleep(1)
        driver.find_element_by_id("selectAllId").click()
        time.sleep(1)
        driver.find_element_by_link_text(u"下载").click()
        time.sleep(1)
        driver.find_element_by_link_text(u"确认").click()
        time.sleep(1)
    except Exception as error:
        print(error)
        file_third = pd.concat([file_third, file_plus.iloc[index]])

"""移动文件archive"""

DOWNLOAD_PATH = '' ######

# 需要迁移的文件名
file_exists = os.listdir(DOWNLOAD_PATH)
file_exists = [item for item in file_exists if item.endswith('.zip')]

# 对应的error文件，去除文件名的字符
for index in range(len(file_plus)):
    file_plus.loc[index, "file_name"] = re.sub(r"\+|、|”|“|\(|\)|（|）| |[a-zA-Z]|\.|《|》|Ⅱ|，", "",file_plus.loc[index,"file_name"])


for index in range(len(file_exists)):
    try:
        file_name_old = file_exists[index]
        file_name_new = file_exists[index][:file_name_old.find(".zip")]
        city = file_plus[file_plus["file_name"] == file_name_new]["city"].values[0]
        file_to_path = PATH_Direction + city
        # os.rename(os.path.join(DOWNLOAD_PATH, file_name_old), os.path.join(DOWNLOAD_PATH, file_name_new + ".zip"))
        shutil.move(os.path.join(DOWNLOAD_PATH, file_name_new + ".zip"), os.path.join(file_to_path, file_name_new + ".zip"))
    except:
        pass



