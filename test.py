from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time

app = Flask(__name__)

# Job scraping function
def scrape_jobs(job_keyword):
    url = 'https://www.timesjobs.com/candidate/job-search.html?searchType=Home_Search&from=submit&asKey=OFF&txtKeywords=&cboPresFuncArea=&cboWorkExp1=0&clusterName=CLUSTER_EXP'
    response = requests.get(url)
    response.raise_for_status()
    html_text = response.text
    soup = BeautifulSoup(html_text, 'lxml')
    job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')

    job_data = []

    for job_box in job_boxes:
        job_title = job_box.find('a').text.strip()
        if job_keyword.casefold() in job_title.casefold():
            posting_date = job_box.find('span', class_='sim-posted').text.strip()
            company_name = job_box.find('h3', class_='joblist-comp-name').text.strip()
            more_details = job_box.a['href']

            # Extract skills
            skills_container = job_box.find('div', class_='more-skills-sections')
            skills = re.findall(r'<span[^>]*>(.*?)</span>', str(skills_container), re.DOTALL)
            skills_list = '|'.join(skill.strip() for skill in skills if skill.strip())

            job_data.append({
                'company_name': company_name,
                'job_title': job_title,
                'posting_date': posting_date,
                'skills': skills_list,
                'more_details': more_details
            })
    return job_data

# Route for the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route to get jobs based on keyword
@app.route('/get_jobs', methods=['POST'])
def get_jobs():
    job_keyword = request.form.get('keyword')
    job_data = scrape_jobs(job_keyword)
    return jsonify(job_data)

if __name__ == '__main__':
    app.run(debug=True)
