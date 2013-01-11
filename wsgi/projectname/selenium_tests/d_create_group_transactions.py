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
SECTION 2 CAN be run independantly
make group categories and user categories
make transasctions both personal and group TODO
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
enter transaction details
        case1: user just paid
        jay ->  kurian  |200    |Rent   |gc:Bills   |1988
                ropo
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//select[@name='selectUserPaid']").is_displayed())
select_element = Select(driver.find_element_by_xpath("//select[@name='selectUserPaid']"))
select_element.select_by_visible_text(usernames[1])
driver.find_element_by_id("id_amount").send_keys("200")
driver.find_element_by_xpath("//tbody/tr[4]/td/label/input").click()    # by xpath W3C spec spath index start at 1
driver.find_element_by_xpath("//tbody/tr[7]/td/label/input").click()
driver.find_element_by_id("id_description").send_keys("Rent")
driver.find_element_by_id("id_date").send_keys("1988-1-1")
driver.find_element_by_xpath("//form/div/div/input[@type='submit']").click()
'''
        case2: user paid and is also a payee
        dash >  dash    |1500   |e-bill |gc:Bills   |1989
                shkku
                jay
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//select[@name='selectUserPaid']").is_displayed())
select_element = Select(driver.find_element_by_xpath("//select[@name='selectUserPaid']"))
select_element.select_by_visible_text(usernames[4])
driver.find_element_by_id("id_amount").send_keys("1500")
driver.find_element_by_xpath("//tbody/tr[5]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[6]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[2]/td/label/input").click()
driver.find_element_by_id("id_description").send_keys("e-bill")
driver.find_element_by_id("id_date").send_keys("1989-1-1")
driver.find_element_by_xpath("//form/div/div/input[@type='submit']").click()
'''
        case3: User is just a payee
        ropo >  jay     |400    |Pizza  |gc:Food    |1990
                shakku
                dash
                kurian
'''
WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_xpath("//select[@name='selectUserPaid']").is_displayed())
select_element = Select(driver.find_element_by_xpath("//select[@name='selectUserPaid']"))
select_element.select_by_visible_text(usernames[6])
driver.find_element_by_id("id_amount").send_keys("400")
driver.find_element_by_xpath("//tbody/tr[2]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[6]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[5]/td/label/input").click()
driver.find_element_by_xpath("//tbody/tr[4]/td/label/input").click()
driver.find_element_by_id("id_description").send_keys("Pizza")
driver.find_element_by_id("id_date").send_keys("1990-1-1")
driver.find_element_by_xpath("//form/div/div/input[@type='submit']").click()
time.sleep(5)
'''
wind up the browser automation
'''
driver.quit()
end_time = datetime.datetime.now()
time_elapsed = end_time - start_time
print('{0} minutes {1} seconds  elapsed'.format(time_elapsed.seconds / 60, time_elapsed.seconds % 60))
