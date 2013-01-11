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
#log in first user
driver.get("http://127.0.0.1:8000/login/")
inputElement = driver.find_element_by_xpath("//form[@name='login']/input[@name='email']")
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='login']/input[@name='email']").is_displayed())
inputElement.clear()
inputElement.send_keys(usernames[0])
inputElement = driver.find_element_by_xpath("//form[@name='login']/input[@name='password']")
inputElement.send_keys("p")
inputElement.submit()
# create a group
driver.find_element_by_link_text("createGroup").click()
inputElement = driver.find_element_by_xpath("//form[@name='groupCreate']/input[@name='name']")
inputElement.send_keys("car")
for i in range(1, 7):
    inputElement = driver.find_element_by_xpath("//li/input")
    inputElement.send_keys(usernames[i])
    time.sleep(0.5)
    inputElement.send_keys(Keys.RETURN)
select_element = Select(driver.find_element_by_xpath("//select[@name='privacy']"))
select_element.select_by_visible_text('private')
inputElement.submit()
driver.get("http://127.0.0.1:8000/logout/")
# accept all invites
for i in range(1, 7):
    WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='login']/input[@name='email']").is_displayed())
    inputElement = driver.find_element_by_xpath("//form[@name='login']/input[@name='email']")
    inputElement.clear()
    inputElement.send_keys(usernames[i])
    inputElement = driver.find_element_by_xpath("//form[@name='login']/input[@name='password']")
    inputElement.send_keys("p")
    inputElement.submit()
    inputElement = driver.find_element_by_xpath("//a[@name='invites_link']")
    inputElement.click()
    try:
        WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_link_text("Accept").is_displayed())
        driver.find_element_by_link_text("Accept").click()
    except:
        pass
    driver.get("http://127.0.0.1:8000/logout/")

'''
wind up the browser automation
'''
driver.quit()
end_time = datetime.datetime.now()
time_elapsed = end_time - start_time
print('{0} minutes {1} seconds  elapsed'.format(time_elapsed.seconds / 60, time_elapsed.seconds % 60))
