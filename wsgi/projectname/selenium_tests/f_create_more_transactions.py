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
        case4: User is just a payee
        muru -> jay     |700    |uc:CITI    |gc: Food   |today
                ropo
                shakku
                kurian
                dash
                muru
                gman
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//input[@name='group_checkbox']").is_displayed())
driver.find_element_by_xpath("//input[@name='group_checkbox']").click()
select_element = Select(driver.find_element_by_xpath("//select[@name='selectUserPaid']"))
select_element.select_by_visible_text(usernames[0])
driver.find_element_by_id("id_amount").send_keys("700")
driver.find_element_by_xpath("//tbody/tr[1]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[2]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[3]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[4]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[5]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[6]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[7]/td/label/input").click()
driver.find_element_by_id("id_description").send_keys("Pizza")
driver.find_element_by_xpath("//form/div/div/input[@type='submit']").click()
'''
        case4: personal txn without category
        muru            |200    |uc: nil   |uc: nil   |today
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//input[@name='group_checkbox']").is_displayed())
driver.find_element_by_id("id_amount").send_keys("200")
driver.find_element_by_id("id_description").send_keys("Food")
driver.find_element_by_xpath("//form/div/div/input[@type='submit']").click()
'''
        case4: personal txn
        muru            |200    |uc: CITI   |uc: Food   |1992
'''
'''
wind up the browser automation
'''
driver.quit()
end_time = datetime.datetime.now()
time_elapsed = end_time - start_time
print('{0} minutes {1} seconds  elapsed'.format(time_elapsed.seconds / 60, time_elapsed.seconds % 60))
