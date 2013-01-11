from __init__ import usernames
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
import time
import datetime

start_time = datetime.datetime.now()
driver = webdriver.Firefox()
driver.get("http://127.0.0.1:8000/logout/")
'''
create users
'''
for uname in usernames:
    driver.get("http://127.0.0.1:8000/logout/")
    # create user sequence ensure unique user name
    WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_link_text("New user").is_displayed())
    driver.find_element_by_link_text("New user").click()
    WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='userCreate']/input[@name='email']").is_displayed())
    inputElement = driver.find_element_by_xpath("//form[@name='userCreate']/input[@name='email']")
    inputElement.clear()
    inputElement.send_keys(uname)
    inputElement = driver.find_element_by_xpath("//form[@name='userCreate']/input[@name='password']")
    inputElement.send_keys("p")
    inputElement.submit()
    try:
        WebDriverWait(driver, 3).until(lambda driver: driver.find_element_by_xpath("//div[@id='userCreated']/div/button[@name='okay']").is_displayed())
        driver.find_element_by_xpath("//div[@id='userCreated']/div/button[@name='okay']").click()
    except:
        pass
'''
wind up the browser automation
'''
driver.quit()
end_time = datetime.datetime.now()
time_elapsed = end_time - start_time
print('{0} minutes {1} seconds  elapsed'.format(time_elapsed.seconds / 60, time_elapsed.seconds % 60))
