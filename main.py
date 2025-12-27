from selenium import webdriver
from selenium.webdriver.common.by import By
from time import time
from itertools import chain
import pandas as pd
import json
import time
import os
import re


COOKIE_FILE = "linkedin_cookies.json"
URL = "https://www.linkedin.com/"

driver = webdriver.Chrome()
driver.get(URL)



job_types = [
    "Full-time",
    "Part-time",
    "Self-employed",
    "Freelance",
    "Contract",
    "Internship",
    "Apprenticeship",
    "Temporary"
]


work_modes = [
    "On-site",
    "Hybrid",
    "Remote"
]


def load_cookies():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            cookie.pop("sameSite", None)
            driver.add_cookie(cookie)
        driver.refresh()
        print("[+] Cookies loaded, logged in!")
    else:
        print("[-] No cookies found. Please login manually...")
        driver.get(URL+'login')
        time.sleep(30) 
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f)
        print("[+] Cookies saved for next time!")

def find_section_index(section_name):

    index = 2
    section_count = driver.find_elements(By.XPATH,'//main/section')

    for index in range(2,len(section_count)):
        section_tag = driver.find_element(By.XPATH,f'//main/section[{index}]/div[2]/div/div/div/h2/span[1]')
        if not section_tag:
            return -1
        elif section_tag.text == section_name:
            return index
        index +=1
    return -1

def find_linkedin_dates(text):
    # LinkedIn style date patterns
    pattern = re.compile(
        r'\b('
        r'(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|'
        r'Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)'
        r'\s+(19|20)\d{2}'
        r'|'  # OR year only like "2022"
        r'(19|20)\d{2}'
        r')\s*(–|-)\s*(Present|present|Current|current|'
        r'(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|'
        r'Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?'
        r')\s+(19|20)\d{2})\b'
    )

    return pattern.findall(text)


def get_basic_info():
    details = {}

    name = driver.find_element(By.XPATH,'//main/section[1]/div[2]/div[2]/div[1]/div[1]/span/a/h1').text
    connections_followers = driver.find_elements(By.XPATH,'//main/section[1]/div[2]/ul/li')
    head_line = driver.find_element(By.XPATH,'//main/section[1]/div[2]/div[2]/div[1]/div[2]').text
    
    connections = "Not Found"
    followers = 'Not Found'
    for ele in connections_followers:
        if ele.text.endswith('connections'):
            connections = ele.text
        else:
            followers = ele.text


    about_index = find_section_index('About')
    about = 'Not Found'
    if  about_index != -1:
        about_ele = driver.find_element(By.XPATH,f'//main/section[{about_index}]/div[3]/div/div/div/span[1]')
        about = about_ele.text

    

    activity_index = find_section_index('Activity')
    last_activity = 'Not Found'

    if activity_index != -1:
        post = driver.find_elements(
            By.XPATH,
            f'//main/section[{activity_index}]/div[4]/div/div/div[1]/div[2]/section/div[2]/div/ul/li[1]/div/div/div/div/div/div/div/div/div/div/span/span[2]'
        )

        if post:
            last_activity = post[0].text.split('•')[0]
        else: 
            comment = driver.find_elements(
                By.XPATH,
                f'//main/section[{activity_index}]/div[4]/div/div/div[1]/ul/li[1]/div/div/a/div/span/span[2]'
            )
            if comment:
                last_activity = comment[0].text 

        if followers == 'Not Found':
            followers = driver.find_element(By.XPATH,f'//main/section[{activity_index}]/div[2]/div/div/div/p/span[1]').text

    details['name'] = name
    details['connections'] = connections
    details['followers'] = followers
    details['head_line'] = head_line
    details['about'] = about
    details['last_activity'] = last_activity

    return details


def extract_nested(section_count,index):
    
    experiences = []
    
    company_name = driver.find_element(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/div/div/div/div/span[1]').text.strip()
    
    company_link = driver.find_element(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[1]/a').get_attribute('href')

    duration_ele = driver.find_elements(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/span/span[1]')
    location_ele = driver.find_elements(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/span[2]/span[1]')
    

    work_mode = 'Not Found'
    location = 'Not Found'

    total_duration = 'Not Found'
    job_type = 'Not Found'
    
    duration = 'Not Found'
    tenurity = 'Not Found'

    if location_ele:
        if '·' in location_ele[0].text:
            location = location_ele[0].text.split('·')[0].strip()
            work_mode = location_ele[0].text.split('·')[1].strip()
        else:
            if location_ele[0].text in work_modes:
                work_mode = location_ele[0].text.strip()
                location = 'Not Found'
            else:
                work_mode = 'Not Found'
                location = location_ele[0].text.strip()

    if duration_ele:
        if '·' in duration_ele[0].text:
            job_type = duration_ele[0].text.split('·')[0]
            total_duration = duration_ele[0].text.split('·')[1]
        else:
            if duration_ele[0].text in job_types:
                job_type = duration_ele[0].text.strip()
                total_duration = 'Not Found'
            else:
                job_type = 'Not Found'
                total_duration = duration_ele[0].text.strip()
    
    
    nested_count = driver.find_elements(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[2]/ul/li')

    
    for nested_index in range(1,len(nested_count)+1):
        
        
        span_ele = driver.find_elements(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[2]/ul/li[{nested_index}]/div/div[2]/div[1]/a/span')
        
        for span_index in range(1,len(span_ele)+1):
            ele = driver.find_element(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[2]/ul/li[{nested_index}]/div/div[2]/div[1]/a/span[{span_index}]/span[1]')
            
            if find_linkedin_dates(ele.text):
                if '·' in ele.text:
                    tenurity = ele.text.split('·')[0]
                    duration = ele.text.split('·')[1]
            elif ',' in ele.text:
                if '·' in ele.text:
                    location = ele.text.split('·')[0]
                    work_mode = ele.text.split('·')[1]
                elif ele.text in work_modes:
                    work_mode = ele.text
                else:
                    location = ele.text
            elif ele.text in job_types:
                job_type = ele.text
        
       

        experiences.append({
            'company_name':company_name,
            'company_link':company_link,
            'location':location,
            'work_mode':work_mode,
            'total_duration':total_duration,
            'job_type':job_type,
            'duration':duration,
            'tenurity':tenurity
        })
    return experiences


def extract_single(section_count,index):
    

    experience = {}

    job_title_elements = driver.find_elements(
    By.XPATH, f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/div/div/div/div/span[1]')

    job_title = job_title_elements[0].text if job_title_elements else "Not Found"
    company_link = driver.find_element(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[1]/a').get_attribute('href')
    company_elements = driver.find_elements(
        By.XPATH, f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/span[1]/span[1]'
    )
    company_name = "Not Found"
    job_type = "Not Found"

    company_name_job_type = company_elements[0].text if company_elements else "Not Found"
    if len(company_name_job_type.split('·')) > 1:
        company_name = company_name_job_type.split('·')[0]
        job_type = company_name_job_type.split('·')[1]
    else:
        if company_elements[0].text in job_types:
            job_type = company_elements[0].text
        else:
            company_name = company_elements[0].text
    
        

    tenure_elements = driver.find_elements(
        By.XPATH, f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/span[2]/span[1]'
    )
    tenure = tenure_elements[0].text if tenure_elements else "Not Found"

    tenurity = tenure.split('·')[0] if '·' in tenure else 'Not Found'
    duration = tenure.split('·')[1] if '·' in tenure else 'Not Found'

    location_elements = driver.find_elements(
        By.XPATH, f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[1]/a/span[3]/span[1]'
    )
    location = location_elements[0].text if location_elements else 'Not Found'

    work_mode = 'Not Found'

    if location_elements:
        if '·' in location_elements[0].text.strip():
            if len(location_elements[0].text.split('·')) > 1:
                location = location_elements[0].text.split('·')[0]
                work_mode = location_elements[0].text.split('·')[1]
            else:
                if location_elements[0].text in work_modes:
                    work_mode = location_elements[0].text
                else:
                    location = location_elements[0].text
        else:
            if location_elements[0].text in work_modes:
                work_mode = location_elements[0].text
                location = 'Not Found'
            else:
                location = location_elements[0].text
                work_mode = 'Not Found'


    experience['job_title'] = job_title 
    experience['company_link'] = company_link 
    experience['company_name'] = company_name
    experience['job_type'] = job_type
    experience['tenurity'] = tenurity 
    experience['duration'] = duration 
    experience['location'] = location
    experience['work_mode'] = work_mode


    return experience 







def get_experience():

    time.sleep(4)

    experiences = []

    section_count = find_section_index('Experience')

    total_experience = driver.find_elements(By.XPATH,f'//main/section[{section_count}]/div[3]/ul/li')

    for index in range(1,len(total_experience)+1):
        check_nested = bool(driver.find_elements(By.XPATH, f'//main/section[{section_count}]/div[3]/ul/li[{index}]/div/div[2]/div[2]/ul/li[1]/span'))
        if check_nested:
            experiences.append(extract_nested(section_count,index))
        else:
            pass
            experiences.append(extract_single(section_count,index))
    
    flattened = list(chain.from_iterable(
        item if isinstance(item, list) else [item]
        for item in experiences
    ))
    
    return flattened



def start_scrap():
    load_cookies()

    driver.get('ENTER PROFILE URL')

    basic_info = get_basic_info()   
    experience = get_experience()

    return {'basic_info':basic_info,'experience':experience}




result = start_scrap()


df = pd.DataFrame([result])

df.to_json('result.json', orient='records', indent=4)

time.sleep(2)
driver.quit()
