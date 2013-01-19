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
# create group categories
'''
go to the transaction link
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//li/a[@name='makeTransactionLink']").is_displayed())
driver.find_element_by_xpath("//li/a[@name='makeTransactionLink']").click()
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='makeTransactionForm']").is_displayed())
driver.find_element_by_xpath("//a[@name='toGroupCategoryCreateLink']").click()
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//input[@name='newCategoryName']").is_displayed())
inputElement = driver.find_element_by_xpath("//input[@name='newCategoryName']")
inputElement.clear()
inputElement.send_keys('asdf')
select_element = Select(driver.find_element_by_xpath("//select[@name='selectUserPaid']"))
select_element.select_by_visible_text(usernames[4])
inputElement.submit()
'''
wind up the browser automation
'''
driver.quit()
end_time = datetime.datetime.now()
time_elapsed = end_time - start_time
print('{0} minutes {1} seconds  elapsed'.format(time_elapsed.seconds / 60, time_elapsed.seconds % 60))
