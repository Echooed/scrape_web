# scrap real website

from bs4 import BeautifulSoup
import requests
import re
import time
import pandas as pd

while True:
    try:
        response = requests.get(
            'https://www.timesjobs.com/candidate/job-search.html?searchType=Home_Search&from=submit&asKey=OFF&txtKeywords=&cboPresFuncArea=&cboWorkExp1=0&clusterName=CLUSTER_EXP'
            )
        # raise HTTPError for bad response
        response.raise_for_status()

    # keep retrying until a connection is secured    
    except requests.exceptions.ConnectionError:
            print("Connection error. Retrying in 10 seconds...")
            time.sleep(10)  # Wait before retrying
    except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}. Retrying in 10 seconds...")
            time.sleep(10)
    except Exception as e:
            print(f"An error occurred: {e}")
    break  # Optionally exit on unexpected errors

print('Input Job keyword')
job_keyword = input('>> ')
print(f'Searching for keyword: {job_keyword}')

# empty list to append output data
job_data = []

# a function to extract and remove wildspaces for skills embedded within the html span tags
def extract_skills(skills_container):
    if skills_container:
        skills = re.findall(r'<span[^>]*>(.*?)</span>', str(skills_container), re.DOTALL)
        skills_list = [
            skill.strip().replace(' / ', '/').replace('**   ', '').replace('  **', '').replace('amp', '')
            for skill in skills if skill.strip()
        ]
        return skills_list
    return []


def find_jobs():
    if response.status_code == 200:
        html_text = response.text
        soup = BeautifulSoup(html_text, 'lxml')
        job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')

        for job_box in job_boxes:
            job_title = job_box.find('a').text.strip()
            if job_keyword.casefold() in job_title.casefold():
                posting_date = job_box.find('span', class_='sim-posted').text.strip()
                company_name = job_box.find('h3', class_='joblist-comp-name').text.strip()
                more_details = job_box.a['href']
                
                # Locate the skills container and extract skills
                skills_container = job_box.find('div', class_='more-skills-sections')
                skills = extract_skills(skills_container)
                
                # append to empty list job_data
                job_data.append(
                        {
                            'company_name' : {company_name},
                            'job_title' : {job_title},
                            'posting_duration': {posting_date},
                            'skills' : {'|'.join(skills)},
                            'more_details' : {more_details}

                        }
                                )   
        # export as csv            
        df = pd.DataFrame(job_data)
        df.to_csv('job_data.csv', index=False)
    else:
        print("Failed to retrieve the webpage.")
find_jobs()

# a condition for this code to repeat at a given time interval
if __name__ == '__main__':
    while True:
        find_jobs()
        time_wait = 10
        print(f'Waiting {time_wait} seconds...')
        time.sleep(time_wait)

    