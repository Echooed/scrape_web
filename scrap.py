#1 scrap simple html file.

from bs4 import BeautifulSoup

with open('home.html', 'r') as html_file:
    content =html_file.read()
    
    soup = BeautifulSoup(content, 'lxml')
    course_cards =soup.find_all('div', class_ = 'card-body')
    for course in course_cards:
        course_price = course.a.text.split()[-1]
        print(f'The course {course.h5.text} cost ${course_price[:-1]}')



#2 scrap real website

import requests
import re
import pandas as pd

response = requests.get('https://www.timesjobs.com/candidate/job-search.html?from=submit&luceneResultSize=25&txtKeywords=data&postWeek=60&searchType=personalizedSearch&actualTxtKeywords=data&searchBy=0&rdoOperator=OR&pDate=I&sequence=10&startPage=1')

if response.status_code == 200:
    html_text =response.text
    soup = BeautifulSoup(html_text, 'lxml')
    job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')

    job_data = []

    for job_box in job_boxes:
        company_name = job_box.find('h3', class_='joblist-comp-name').text.strip()
        job_title = job_box.find('a').text.strip()
        posting_date = job_box.find('span', class_='sim-posted').text.strip()

        # Locate the skills container and pass it to the function
        skills_container = job_box.find_all('div', class_='more-skills-sections')
        

        # function to extract skills from with the span tags using regex
        def extract_skills(skills_container):
            if skills_container:
                skills = re.findall(r'<span[^>]*>(.*?)</span>', str(skills_container), re.DOTALL)
                skills_list = [skill.strip() for skill in skills if skill.strip()]
                return skills_list
            return []

        skills = extract_skills(skills_container)

        job_data.append(
            {
                'company_name' : {company_name},
                'job_title' : {job_title},
                'posting_duration': {posting_date},
                'skills' : {'|'.join(skills)}
            }
                     )       
        df = pd.DataFrame(job_data)
        df.to_csv('job_data.csv', index=False)
else:
    print("Failed to retrieve the webpage.")
    