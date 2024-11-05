"""
TimesJobs Search Web Application
------------------------------
A Flask-based web application for real-time job searching on TimesJobs.
Includes live updates and a clean interface.
"""

from flask import Flask, render_template, request, Response, jsonify
from dataclasses import dataclass, asdict
import json
import queue
import threading
from datetime import datetime
import time
from typing import Optional, Dict
from bs4 import BeautifulSoup
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Queue for storing search results
result_queue = queue.Queue()

@dataclass
class JobPosting:
    """Represents a single job posting."""
    company_name: str
    job_title: str
    posting_duration: str
    skills: str
    more_details: str
    scraped_at: str

    def to_dict(self) -> Dict:
        """Convert job posting to dictionary."""
        return asdict(self)

class JobScraper:
    """Handles job scraping operations."""
    BASE_URL = 'https://www.timesjobs.com/candidate/job-search.html'
    
    def __init__(self):
        self.session = self._initialize_session()
        self.is_searching = False
        self.current_keyword = None
        self.search_thread = None

    def _initialize_session(self) -> requests.Session:
        """Initialize requests session with headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return session

    def _build_search_url(self, keyword: str) -> str:
        """Construct search URL with parameters."""
        params = {
            'searchType': 'personalizedSearch',
            'from': 'submit',
            'txtKeywords': keyword,
        }
        query = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{self.BASE_URL}?{query}"

    def _parse_job(self, job_box, keyword: str) -> Optional[JobPosting]:
        """Parse single job posting from HTML."""
        try:
            job_title = job_box.find('a').text.strip()
            if keyword.lower() not in job_title.lower():
                return None

            skills_container = job_box.find('div', class_='more-skills-sections')
            skills = []
            if skills_container:
                skills = [skill.text.strip() for skill in skills_container.find_all('span')]

            return JobPosting(
                company_name=job_box.find('h3', class_='joblist-comp-name').text.strip(),
                job_title=job_title,
                posting_duration=job_box.find('span', class_='sim-posted').text.strip(),
                skills='|'.join(skills),
                more_details=job_box.a['href'],
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            logger.error(f"Error parsing job: {e}")
            return None

    def search_jobs(self, keyword: str):
        """Main job search method."""
        self.current_keyword = keyword
        self.is_searching = True
        
        while self.is_searching:
            try:
                url = self._build_search_url(keyword)
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')
                
                for job_box in job_boxes:
                    if not self.is_searching:
                        break
                    
                    job = self._parse_job(job_box, keyword)
                    if job:
                        result_queue.put(job.to_dict())
                
                time.sleep(30)  # Wait 30 seconds before next fetch
                
            except Exception as e:
                logger.error(f"Error during job search: {e}")
                time.sleep(5)

    def start_search(self, keyword: str):
        """Start search in a new thread."""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search()
        
        self.search_thread = threading.Thread(target=self.search_jobs, args=(keyword,))
        self.search_thread.start()

    def stop_search(self):
        """Stop ongoing search."""
        self.is_searching = False
        if self.search_thread:
            self.search_thread.join()
            self.search_thread = None

# Create global scraper instance
scraper = JobScraper()

@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')

@app.route('/start_search', methods=['POST'])
def start_search():
    """Start job search with keyword."""
    keyword = request.json.get('keyword', '').strip()
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    scraper.start_search(keyword)
    return jsonify({'message': 'Search started'})

@app.route('/stop_search', methods=['POST'])
def stop_search():
    """Stop ongoing job search."""
    scraper.stop_search()
    return jsonify({'message': 'Search stopped'})

@app.route('/stream')
def stream():
    """Stream job results using SSE."""
    def generate():
        while True:
            try:
                job = result_queue.get(timeout=1)
                yield f"data: {json.dumps(job)}\n\n"
            except queue.Empty:
                yield "data: {}\n\n"
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)