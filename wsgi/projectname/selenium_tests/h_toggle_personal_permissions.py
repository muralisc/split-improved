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
make transasctions both personal and group
logout and login as the first user
'''
driver.get("http://127.0.0.1:8000/logout/")
driver.get("http://127.0.0.1:8000/login/")
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='login']/input[@name='email']").is_displayed())
inputElement = driver.find_element_by_xpath("//form[@name='login']/input[@name='email']")
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='login']/input[@name='email']").is_displayed())
inputElement.clear()
inputElement.send_keys(usernames[0])
inputElement = driver.find_element_by_xpath("//form[@name='login']/input[@name='password']")
inputElement.send_keys("p")
inputElement.submit()
'''
go to the transaction link
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//li/a[@name='makeTransactionLink']").is_displayed())
driver.find_element_by_xpath("//li/a[@name='makeTransactionLink']").click()
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//form[@name='makeTransactionForm']").is_displayed())
'''
        grant personal permissions
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//a[@name='settings']").is_displayed())
driver.find_element_by_xpath("//a[@name='settings']").click()
driver.find_element_by_xpath("//a[@name='personalTransactionPermission']").click()
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//li/a[@name='makeTransactionLink']").is_displayed())
driver.find_element_by_xpath("//li/a[@name='makeTransactionLink']").click()
'''
wind up the browser automation
'''
driver.quit()
end_time = datetime.datetime.now()
time_elapsed = end_time - start_time
print('{0} minutes {1} seconds  elapsed'.format(time_elapsed.seconds / 60, time_elapsed.seconds % 60))
