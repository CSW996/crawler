import re
import shutil
import time
import os
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import math


# 等待加载
def loading(t):
    for wait in range(t):
        try:
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="dialog-loading-1584855744626"]/div/div/span')))
        except TimeoutException:
            break


def wait_click(t, selector, element):
    for wait in range(t):
        try:
            if element == "text":
                to_click = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.LINK_TEXT, selector)))
            if element == "xpath":
                to_click = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, selector)))
            if element == "css":
                to_click = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.CLASS_NAME, selector)))
            to_click.click()
            break
        except ElementClickInterceptedException:
            pass


def wait_download(t, element):
    for wait in range(t):
        try:
            element.click()
            if element.get_attribute("class") == "active":
                wait_click(t, "下载", "text")
                time.sleep(1)
                break
        except Exception:
            pass


"""超参数"""

GOV_USER = "" ######
GOV_PSWD = "" ######
FIRST_PAGE_URL = "http://data.sd.gov.cn/odweb//catalog/index.htm"

# 打开浏览器
driver = webdriver.Chrome()
driver.get(FIRST_PAGE_URL)

driver.implicitly_wait(2)

print("访问成功，下面开始用户登陆阶段……")

# 进入登陆页面
loading(10)
element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "bounceIn"))
)
element.click()

# 账号&密码 & 验证码输入
driver.find_element_by_id("grusername").click()
driver.find_element_by_id("grusername").clear()
driver.find_element_by_id("grusername").send_keys(GOV_USER)

driver.find_element_by_id("grpwd").click()
driver.find_element_by_id("grpwd").clear()
driver.find_element_by_id("grpwd").send_keys(GOV_PSWD)

# driver.find_element_by_id("loginbtn").click()

# 完成登陆跳转
loading(15)

"""profile"""

if os.path.exists("./data_profile_0402.log"):
    with open("./data_profile_0402.log", "w", encoding="utf-8") as f:
        f.close()

table = driver.find_elements_by_xpath('//*[@id="getOrg"]/li')
province_list = [item.text.split("\n") for item in table]

for index in range(48, len(province_list)):
    province = province_list[index][0]  #
    time.sleep(1)
    province_dataset_count = province_list[index][1]  #
    page_total = math.ceil(int(province_dataset_count) / 6)
    loading(40)
    province_click = driver.find_elements_by_xpath('//*[@id="getOrg"]/li')[index]
    province_click.click()
    loading(40)

    for current_page in range(1, page_total + 1):
        loading(40)
        province_dataset_element = driver.find_elements_by_xpath('//*[@id="catalog-list"]/li')
        for item in province_dataset_element:
            url = item.find_elements_by_xpath('div[1]/div[1]/a')[0].get_attribute("href")
            data_detail_ = item.text.split("\n")
            data_name = data_detail_[0]
            data_field = data_detail_[2]
            data_prof = data_detail_[-1].split("  ")
            # 每一个数据集输出的信息：数据集所属省市名称 / 该省市包含的数据集数量 / 该数据集名称 / 该数据集所属领域 / 数据量 / 接口数量 / 文件数
            with open("data_profile_0402.log", "a") as writer:
                writer.write(province + "\t" + province_dataset_count + "\t" + data_name + "\t" + data_field + "\t")
                writer.write("\t".join([_.split(":")[-1] for _ in data_prof]) + "\t" + url + "\n")

        if page_total != current_page:
            driver.find_elements_by_xpath('//*[@id="Pagination"]/a')[-1].click()
            loading(40)

"""对照查看缺失文件"""

profile = [line.split("\t") for line in open("data_profile_0402.log").readlines()]
profile = pd.DataFrame(profile, columns=[
    "province", "province_dataset_count", "data_name", "data_field",
    "id1", "id2", "id3", "url"])

for index in range(len(profile)):
    profile.loc[index, "data_name"] = re.sub(r"\+|、|”|“|\(|\)|（|）| |[a-zA-Z]|\.|《|》|Ⅱ", "",
                                             profile.loc[index, "data_name"])

PATH_Direction = "" ######
if os.path.exists("./error.log"):
    with open("./error.log", "w", encoding="utf-8") as f:
        f.close()

for province in profile["province"].drop_duplicates():
    city_path = PATH_Direction + province
    if not os.path.exists(city_path):
        os.mkdir(city_path)
    file_exist = os.listdir(city_path)
    file_exist = [item for item in file_exist if not item.startswith("._")]
    file_exist = [re.sub(r"\+|、|”|“|\(|\)|（|）| |《|》|Ⅱ", "", item) for item in file_exist]
    file_should = profile[profile["province"] == province].reset_index(drop=True)
    for index in range(len(file_should)):
        file_name = file_should.loc[index, "data_name"]
        xls = file_name + "_xls.zip"
        csv = file_name + "_csv.zip"
        xml = file_name + "_xml.zip"
        json = file_name + "_json.zip"
        one_file = [xls, csv, xml, json]
        for file in one_file:
            if file not in file_exist:
                with open("error.log", "a") as w:
                    w.write("{city}\t{file_name}\t{url}".format(
                        city=province,
                        file_name=file,
                        url=file_should.loc[index, "url"]
                    ))

"""按照上述对比结果，按照url下载"""

error = [line.split("\t") for line in open("error.log").readlines()]
error = pd.DataFrame(error, columns=["province", "data_name", "url"])

error_dict = {}
for index in range(len(error)):
    line = error.loc[index, "data_name"]
    name = line[:line.rfind("_")]
    f_type = line[line.rfind("_") + 1:].split(".")[0]
    if name in error_dict.keys():
        error_dict[name].append(f_type)
    else:
        error_dict[name] = [error.loc[index, "url"], f_type]

error_list = list(error_dict.keys())
if os.path.exists("./exist.log"):
    with open("./exist.log", "w", encoding="utf-8") as f:
        f.close()

for index in range(len(error_list)):
    f_name = error_list[index]
    """按url搜索"""
    url = error_dict[f_name][0]
    driver.get(url)
    loading(20)
    for wait in range(10):
        try:
            to_click = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "data-download")))
            to_click.click()
            break
        except ElementClickInterceptedException:
            print(f_name)
        time.sleep(1)

    """按文件后缀下载"""
    try:
        to_download = driver.find_elements_by_xpath('//*[@action="data-download"]/div/div[1]/ul/li')

        # xls
        if "xls" in error_dict[f_name]:
            sign = driver.find_elements_by_xpath('//*[@id="catalog-excel-file-table"]/tbody[1]/tr/td')[0].text
            if len(sign) > 1:
                with open("exist.log", "a") as f:
                    f.write("xls\t{f_name}\t{url}".format(
                        f_name=f_name,
                        url=url
                    ))
            else:
                xls_active = to_download[0]
                wait_download(4, xls_active)

        # csv
        if "csv" in error_dict[f_name]:
            sign = driver.find_elements_by_xpath('//*[@id="catalog-csv-file-table"]/tbody[1]/tr/td')[0].text
            if len(sign) > 1:
                with open("exist.log", "a") as f:
                    f.write("csv\t{f_name}\t{url}".format(
                        f_name=f_name,
                        url=url
                    ))
            else:
                csv_active = to_download[1]
                wait_download(4, csv_active)

        # xml
        if "xml" in error_dict[f_name]:
            sign = driver.find_elements_by_xpath('//*[@id="catalog-xml-file-table"]/tbody[1]/tr/td')[0].text
            if len(sign) > 1:
                with open("exist.log", "a") as f:
                    f.write("xml\t{f_name}\t{url}".format(
                        f_name=f_name,
                        url=url
                    ))
            else:
                xml_active = to_download[2]
                wait_download(4, xml_active)

        # json
        if "json" in error_dict[f_name]:
            sign = driver.find_elements_by_xpath('//*[@id="catalog-json-file-table"]/tbody[1]/tr/td')[0].text
            if len(sign) > 1:
                with open("exist.log", "a") as f:
                    f.write("json\t{f_name}\t{url}".format(
                        f_name=f_name,
                        url=url
                    ))
            else:
                json_active = to_download[3]
                wait_download(4, json_active)

    except Exception as e:
        print(e)

"""移动file"""

DOWNLOAD_PATH = "" ######
file_exists = os.listdir(DOWNLOAD_PATH)
file_exists = [item for item in file_exists if item.endswith('.zip')]

# 对应的error文件，去除文件名的字符
for index in range(len(error)):
    error.loc[index, "data_name"] = re.sub(r"\+|、|”|“|\(|\)|（|）| |[a-zA-Z]|\.|《|》|Ⅱ|，", "",
                                           error.loc[index, "data_name"])

for index in range(len(file_exists)):
    try:
        file_name = file_exists[index]
        file_name_ = re.sub(r"\+|、|”|“|\(|\)|（|）| |[a-zA-Z]|\.|《|》|Ⅱ|，", "", file_name)
        province = error[error["data_name"] == file_name_]["province"].values[0]
        file_to_path = PATH_Direction + province
        shutil.move(os.path.join(DOWNLOAD_PATH, file_name), os.path.join(file_to_path, file_name))
    except:
        pass
