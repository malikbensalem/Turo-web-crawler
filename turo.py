from email import header
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import csv
import pickle
import os.path
from datetime import datetime

from dateutil.parser import parse

driver = None
counterCsv=0
turoCsv=[]

def getFloat(str) :    
    result = ''
    nums='1234567890.-'
    for char in str:
        if char in nums:
            result += char
            if char=='.':
                nums=nums.replace('.','')
            elif char=='-':
                nums=nums.replace('-','')
    if result=='':
        result=0
    return float(result) 

def setUpDriver():
    options = webdriver.ChromeOptions() 
    
    options.add_argument('--user-data-dir=C:/Users/Malik/AppData/Local/Google/Chrome/User Data/Default')

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=options,executable_path="C:/Users/Malik/Desktop/projects/Turo-web-crawler/chromedriver.exe")
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
    print('\n\n\n\n\n\n\n\n\n')
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
    print('\n\n\n\n\n\n\n\n\n')
    print('Getting upcoming trips.')
    goToTrips('booked')
    getEles('div[data-testid="test-button-dropdown"]')[0].click()

    carAmount=len(getEles('div.css-tlftjr'))-2

    getEles('div[data-testid="test-button-dropdown"]')[0].click()
    for carIndex in range(carAmount):
        getEles('div[data-testid="test-button-dropdown"]')[0].click()
        reg=getEles('div.css-tlftjr')[carIndex].text
        getEles('div.css-tlftjr')[carIndex].click() 
        time.sleep(2)
        tripAmount=len(getEles('a.css-1aq0sp2',2))
        print('\nGetting ',reg,' (',tripAmount,') -> ')
        for tripIndex in range(tripAmount):
            if tripIndex%2==1:
                print(tripIndex//2+1,end=' | ')
                getTripUpcomingSingle(getEles('a.css-1aq0sp2')[tripIndex].get_attribute('href'),reg)

def getTripHistoryAll():
    print('\n\n')
    print('Getting historic trips.')
    goToTrips('history')
    getEles('div[data-testid="test-button-dropdown"]')[0].click()
    carAmount=len(getEles('div.css-tlftjr'))-2
    getEles('div[data-testid="test-button-dropdown"]')[0].click()
    for carIndex in range(2,carAmount):
        getEles('div[data-testid="test-button-dropdown"]')[0].click()
        reg=getEles('div.css-tlftjr')[carIndex].text
        getEles('div.css-tlftjr')[carIndex].click()
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
        miles=getEles('span.css-mrzgsa-StyledText')[0].text
        getEles('a.u-marginTopSmaller.u-displayBlock')[0].click()
        getReceipt(reg,'History',miles)
    else: 
        getReceiptCancelled(reg)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def getTripUpcomingSingle(carLink,reg):
    driver.execute_script("window.open('"+carLink+"','_blank');")
    driver.switch_to.window(driver.window_handles[1])

    getEles('a.u-marginTopSmaller.u-displayBlock')[0].click()
    getReceipt(reg,'booked','0')
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return

def getReceiptCancelled(reg):
    carInfo={}
    carInfo['Registration']=reg
    carInfo['Status']='Cancelled'
    year=''

    carInfo['Guest']=''
    try:    
        carInfo['Guest']=getEles('p.css-g36krj-StyledText')[0].text
    except IndexError:
        driver.execute_script("window.location.reload();") 
        carInfo['Guest']=getEles('p.css-g36krj-StyledText',60)[0].text


    if getEles('h2.css-lb4jzt-StyledText',.001):
        year='-'+getEles('h2.css-lb4jzt-StyledText')[0].text.split(' ')[-1]
    else:
        return

    carInfo['Date Start']=parse(getEles('p.css-9ld7or-StyledText-StyledScheduleDateTime')[0].text+' '+getEles('p.css-mzrfmu-StyledText-StyledScheduleDateTime')[0].text+' '+year).strftime("%m/%d/%Y, %H:%M:%S")

    carInfo['Date End']=parse(getEles('p.css-9ld7or-StyledText-StyledScheduleDateTime')[1].text+' '+getEles('p.css-kg2jz6-StyledText-StyledScheduleDateTime')[0].text).strftime("%m/%d/%Y, %H:%M:%S")

    turoCsv.append(carInfo)

def getReceipt(reg,status,miles):
    carInfo={}
    carInfo['Registration']=reg
    carInfo['Status']=status
    carInfo['Miles']=getFloat(miles)

    carInfo['Date Start']=parse(getEles('span.e1glo9kk7',60)[0].text.replace('BST',''))
    carInfo['Date End']=parse(getEles('span.e1glo9kk7')[1].text.replace('BST',''))
    carInfo['Trip Lenght (Days)']=carInfo['Date Start']-carInfo['Date End']
    carInfo['Date Start']=carInfo['Date Start'].strftime("%m/%d/%Y, %H:%M:%S")
    carInfo['Date End']=carInfo['Date End'].strftime("%m/%d/%Y, %H:%M:%S")

    carInfo['Guest']=getEles('span.css-1kv227m-StyledText a')[0].text

    data=getEles('div.e1glo9kk6 div span')
    for x in range(0,len(data),2):
        carInfo[data[x].text]=data[x+1].text

    turoCsv.append(carInfo)

def manageCSV(csvRows):
    print('\n\n\n\n\n')
    print('Making CSV')
    with open ('turo '+datetime.today().strftime('%Y-%m-%d')+'.csv', 'w',newline='') as file:
        writer = csv.writer(file)
        temp=[]
        count=0
        indexKey={}
        writer.writerow(temp)
        for x in range(len(csvRows)):
            temp=[''] * count
            for y in csvRows[x]:
                try:
                    temp[indexKey[y]] = csvRows[x][y]
                except KeyError:
                    indexKey[y]=count
                    temp.append('')
                    temp[indexKey[y]] = csvRows[x][y]
                    count+=1
            try:
                writer.writerow(temp)
            except UnicodeEncodeError:
                print(temp)
        
        csvHeader=[]
        for x in indexKey:
            csvHeader.append(x)
        writer.writerow(csvHeader)
        


start=time.time()
driver=setUpDriver()
getEles('body')
driver.get("https://turo.com/")
login()
goToTrips('history')
# getTripUpcomingAll()
getTripHistoryAll()

manageCSV(turoCsv)
print('Took',time.time()-start,'seconds')
print('DONE')
