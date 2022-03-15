import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import csv
import re

import pickle
import os.path



driver = None
turoCsv=[['Guest','Reg','Status','Start','End','Miles','Extras','Reimbursements','Trip Cost','Earnings']]

def getFloat(str) :  
    str=  re.sub('[^0-9.]+', '', str).replace(",", ".")
    return float(str)

def setUpDriver():
    options = webdriver.ChromeOptions() 
    options.add_argument("headless")
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})

    return driver


def getEles(selector,waitTime=5):
    driver.implicitly_wait(waitTime)
    return driver.find_elements(By.CSS_SELECTOR,selector)
    
def scrollDown():
    time.sleep(2)
    driver.execute_script("window.scroll({  top: document.body.scrollHeight*3, behavior: 'smooth'});") 
    while getEles('div.css-kqbngd'):
        time.sleep(3)
        driver.execute_script("window.scroll({  top: document.body.scrollHeight*3, behavior: 'smooth'});") 

     
def login():
    if os.path.isfile('cookies.pkl'):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        
    if not getEles('#__next > header > div.seo-pages-16jy2gd-FlexAlignEnd-FlexAlignEnd.e1cqkxkz0 > div:nth-child(1) > button'):
        getEles('a[href="/gb/en/login"]')[0].click()
        input('Press enter once you have logged in and done 2 step: ')        

    pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))
    
def getTripUpcomingAll():
    print('Getting upcoming trips.')
    goToTrips('booked')
    getEles('div[data-testid="test-button-dropdown"]')[0].click()

    carAmount=len(getEles('span.dropdownVehicleItem-license'))
    
    getEles('div[data-testid="test-button-dropdown"]')[0].click()
    for carIndex in range(carAmount):
        getEles('div[data-testid="test-button-dropdown"]')[0].click()
        reg=getEles('span.dropdownVehicleItem-license')[carIndex].text
        getEles('span.dropdownVehicleItem-license')[carIndex].click() 
        time.sleep(2)
        tripAmount=len(getEles('a.css-1aq0sp2',2))
        print('\nGetting ',reg,' (',tripAmount,') -> ')
        for tripIndex in range(tripAmount):
            if tripIndex%2==1:
                print(tripIndex//2+1,end=' | ')
                getTripUpcomingSingle(getEles('a.css-1aq0sp2')[tripIndex].get_attribute('href'),reg)

def getTripHistoryAll():
    print('Getting historic trips.')
    goToTrips('history')
    getEles('div[data-testid="test-button-dropdown"]')[0].click()
    carAmount=len(getEles('span.dropdownVehicleItem-license'))
    getEles('div[data-testid="test-button-dropdown"]')[0].click()
    for carIndex in range(carAmount):
        getEles('div[data-testid="test-button-dropdown"]')[0].click()
        reg=getEles('span.dropdownVehicleItem-license')[carIndex].text
        getEles('span.dropdownVehicleItem-license')[carIndex].click()
        scrollDown()
        tripAmount=len(getEles('a.historyFeedItem-details'))
        print('\nGetting ',reg,' (',tripAmount,') -> ')
        for tripIndex in range(tripAmount):
            print(tripIndex+1,end=' | ')
            getTripHistorySingle(getEles('a.historyFeedItem-details')[tripIndex].get_attribute('href'),reg)

def goToTrips(status):
    driver.get('https://turo.com/gb/en/trips/'+status)

def getTripHistorySingle(carLink,reg):
    driver.execute_script("window.open('"+carLink+"','_blank');")
    driver.switch_to.window(driver.window_handles[1])
    if getEles('a.u-marginTopSmaller.u-displayBlock'):
        getEles('a.u-marginTopSmaller.u-displayBlock')[0].click()
        getReceipt(reg,'History')
    else: 
        getReceiptCancelled(reg)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def getTripUpcomingSingle(carLink,reg):
    driver.execute_script("window.open('"+carLink+"','_blank');")
    driver.switch_to.window(driver.window_handles[1])

    getEles('a.u-marginTopSmaller.u-displayBlock')[0].click()
    getReceipt(reg,'booked')
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return

def getReceiptCancelled(reg):
    carInfo={}
    carInfo['reg']=reg
    carInfo['status']='Cancelled'
    year=''

    carInfo['guest']=getEles('p.css-g36krj-StyledText')[0].text
    carInfo['miles']='0'
    carInfo['earnings']='0'
    carInfo['tripPrice']='0'
    carInfo['reimbursements']='0'

    if getEles('h2.css-lb4jzt-StyledText',.001):
        year='-'+getEles('h2.css-lb4jzt-StyledText')[0].text.split(' ')[-1]
    else:
        return

    carInfo['start']=getEles('#pageContainer-content > div.app > div.app-content > div > div > div > div.css-5uizmy-ReservationDetailsDesktopLayout-ReservationDetailsDesktopLayoutContainer.e6je8v60 > div.gutter--6.row.u-justifyContentBetween.u-marginTop2 > div.col.col--md7.col--lg8 > div > section:nth-child(1) > div.detailsSection-description.col.col--12 > div > div:nth-child(1) > p.css-9ld7or-StyledText-StyledScheduleDateTime')[0].text.split(',')[1].split(' ')
    carInfo['start']=carInfo['start'][1]+'-'+carInfo['start'][0]+year

    carInfo['end']=getEles('#pageContainer-content > div.app > div.app-content > div > div > div > div.css-5uizmy-ReservationDetailsDesktopLayout-ReservationDetailsDesktopLayoutContainer.e6je8v60 > div.gutter--6.row.u-justifyContentBetween.u-marginTop2 > div.col.col--md7.col--lg8 > div > section:nth-child(1) > div.detailsSection-description.col.col--12 > div > div:nth-child(3) > p.css-9ld7or-StyledText-StyledScheduleDateTime')[0].text.split(',')[1].split(' ')
    carInfo['end']=carInfo['end'][1]+'-'+carInfo['end'][0]+year

    turoCsv.append(carInfo)

def getReceipt(reg,status):
    carInfo={}
    carInfo['reg']=reg
    carInfo['status']=status

    carInfo['start']=getEles('div.receiptSchedule p')[0].text.split(',')[1:]
    carInfo['start']='-'.join(carInfo['start']).replace(' ','-')
    carInfo['end']=getEles('div.receiptSchedule p')[2].text.split(',')[1:]
    carInfo['end']='-'.join(carInfo['end']).replace(' ','-')
    carInfo['guest']=getEles('#receipt-container > div > div:nth-child(6) > li > span.value > a')[0].text
    carInfo['miles']='0'

    if getEles('#receipt-container > div > div:nth-child(8) > li:nth-child(2) > span.value',0.01):
        carInfo['miles']=getEles('#receipt-container > div > div:nth-child(8) > li:nth-child(2) > span.value')[0].text
    
    carInfo['reimbursements']='0'
    if getEles('#receipt-container > div > div.reimbursements > ul > li:nth-last-child(1) > span.value.total > span',0.01):
        carInfo['reimbursements']=getEles('#receipt-container > div > div.reimbursements > ul > li:nth-last-child(1) > span.value.total > span')[0].text

    carInfo['tripPrice']=getEles('#receipt-container > div > div.cost-details > ul > li:nth-last-child(1) > span.value.total > span')[0].text
   
    try:
        carInfo['earnings']=getEles('#receipt-container > div > div.payment-details > ul > li:nth-child(6) > span.value.earned.total > span',.01)[0].text
    except IndexError:
        try:
            carInfo['earnings']=getEles('#receipt-container > div > div.payment-details > ul > li:nth-child(3) > span.value.earned.total > span',.01)[0].text
        except IndexError:
            carInfo['earnings']='missing'

    turoCsv.append(carInfo)

def manageCSV(csvRows):
    with open ('turo.csv', 'w',newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csvRows[0])
        for x in range(1,len(csvRows)):
            writer.writerow([csvRows[x]['guest'],csvRows[x]['reg'],csvRows[x]['status'],csvRows[x]['start'],csvRows[x]['end'],getFloat(csvRows[x]['miles']),0,getFloat(csvRows[x]['reimbursements']),getFloat(csvRows[x]['tripPrice']),getFloat(csvRows[x]['earnings'])])

start=time.time()
driver=setUpDriver()
getEles('body')
driver.get("https://turo.com/")
print('\n\n\n\n\n\n\n\n\n')
login()

print('\n\n\n\n\n\n\n\n\n')
getTripUpcomingAll()
getTripHistoryAll()
print('\n\n')


manageCSV(turoCsv)
print('Took',time.time()-start,'seconds')
input('DONE')
