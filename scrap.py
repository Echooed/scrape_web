from bs4 import BeautifulSoup
import requests
import re
import time
import pandas as pd
import os

# Define the job keyword input once at the start
print('Input Job keyword')
job_keyword = input('>> ')
print(f'Searching for keyword: {job_keyword}')


# Function to extract skill required from job post
def extract_skills(skills_container):
    if skills_container:
        skills = re.findall(r'<span[^>]*>(.*?)</span>', str(skills_container), re.DOTALL)
        skills_list = [
            skill.strip().replace(' / ', '/').replace('**   ', '').replace('  **', '').replace('amp', '')
            for skill in skills if skill.strip()
        ]
        return skills_list
    return []


# function to extract data from website html
def find_jobs():
    try:
        response = requests.get(
            'https://www.timesjobs.com/candidate/job-search.html?searchType=Home_Search&from=submit&asKey=OFF&txtKeywords=&cboPresFuncArea=&cboWorkExp1=0&clusterName=CLUSTER_EXP'
        )
        response.raise_for_status()
        
        if response.status_code == 200:
            html_text = response.text
            soup = BeautifulSoup(html_text, 'lxml')
            job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')
            
            # Temporary list for current jobs
            current_job_data = []

            for job_box in job_boxes:
                job_title = job_box.find('a').text.strip()
                if job_keyword.casefold() in job_title.casefold():
                    posting_date = job_box.find('span', class_='sim-posted').text.strip()
                    company_name = job_box.find('h3', class_='joblist-comp-name').text.strip()
                    more_details = job_box.a['href']
                    
                    # Extract skills
                    skills_container = job_box.find('div', class_='more-skills-sections')
                    skills = extract_skills(skills_container)

                    # append to list
                    current_job_data.append({
                        'company_name': company_name,
                        'job_title': job_title,
                        'posting_duration': posting_date,
                        'skills': '|'.join(skills),
                        'more_details': more_details
                    })
            
            # Check for existing CSV file
            file_exists = os.path.isfile('job_data.csv')
            
            # Load existing data if CSV exists
            if file_exists:
                previous_data = pd.read_csv('job_data.csv')
                current_data_df = pd.DataFrame(current_job_data)
                
                # Check if dataframes are identical
                if previous_data.equals(current_data_df):
                    print("No new data found; skipping CSV update.")
                    return  
            
            # Write new data to CSV if different
            pd.DataFrame(current_job_data).to_csv('job_data.csv', index=False)
            print("Data updated in CSV file.")

    except requests.exceptions.ConnectionError:
        print("Connection error. Retrying in 10 seconds...")
        time.sleep(10)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}. Retrying in 10 seconds...")
        time.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")

# Run find_jobs repeatedly with time intervals
if __name__ == '__main__':
    while True:
        find_jobs()
        time_wait = 10
        print(f'Waiting {time_wait} seconds...')
        time.sleep(time_wait)
