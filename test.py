from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time

# fetch website and pass into variable
response = requests.get('https://www.timesjobs.com/candidate/job-search.html?from=submit&luceneResultSize=25&txtKeywords=data&postWeek=60&searchType=personalizedSearch&actualTxtKeywords=data&searchBy=0&rdoOperator=OR&pDate=I&sequence=1&startPage=1')

def find_jobs():
    if response.status_code == 200:
        html_text =response.text
        soup = BeautifulSoup(html_text, 'lxml')
        job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')

        for job_box in job_boxes:
            posting_date = job_box.find('span', class_='sim-posted').text.strip()
            company_name = job_box.find('h3', class_='joblist-comp-name').text.strip()
            job_title = job_box.find('a').text.strip()
            more_details = job_box.a['href']
            
            # Locate the skills container and pass it to the function
            skills_container = job_box.find_all('div', class_='more-skills-sections')

            # function to extract skills from with the span tags using regex
            def extract_skills(skills_container):
                    if skills_container:
                        skills = re.findall(r'<span[^>]*>(.*?)</span>', str(skills_container), re.DOTALL)
                        skills_list = [skill.strip().replace(' / ', '/').replace('**   ', '').replace('  **', '').replace('amp','') for skill in skills if skill.strip()]
                        return skills_list
                    return []
                
            skills = extract_skills(skills_container)

            print(f"Company: {company_name}")
            print(f"Job Title: {job_title}")
            print(f"Posting Date: {posting_date}")            
            print(f"Skills: {'|'.join(skills)}")
            print(f"more_details: {more_details}\n")
    else:
        print("Failed to retrieve the webpage.")
        
if __name__ == '__main__':
     while True:
          find_jobs()
          time_wait = 10
          print(f'waiting {time_wait} seconds...')
          time.sleep(time_wait)