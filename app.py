from flask import Flask, render_template, request, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass, asdict
import json
import queue
import threading
from datetime import datetime
import time
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import requests
import logging
from sqlalchemy import desc



class JobScraper:
    """Handles job scraping operations."""
    BASE_URL = 'https://www.timesjobs.com/candidate/job-search.html'
    
    def __init__(self):
        self.session = self._initialize_session()
        self.is_searching = False
        self.current_keyword = None
        self.search_thread = None
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 5

    def _initialize_session(self) -> requests.Session:
        """Initialize requests session with updated headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        })
        return session

    def _build_search_url(self, keyword: str, page: int = 1) -> str:
        """Construct search URL with updated parameters."""
        params = {
            'searchType': 'personalizedSearch',
            'from': 'submit',
            'txtKeywords': keyword,
            'sequence': str(page),
            'startPage': '1',
            'pageNum': str(page),
            'totalCount': '40',
            'searchBy': '1',  # Changed to 1 for better results
            'luceneResultSize': '25',
            'postWeek': 'Select',
            'txtLocation': '',
            'cboWorkExp1': '0'
        }
        return f"{self.BASE_URL}?{'&'.join(f'{k}={requests.utils.quote(str(v))}' for k, v in params.items())}"

    def _parse_job(self, job_box, keyword: str) -> Optional[JobPosting]:
        """Parse single job posting with improved selectors."""
        try:
            # Updated selectors based on current TimeJobs HTML structure
            job_title_elem = job_box.find('h2')
            if not job_title_elem:
                job_title_elem = job_box.find('a', {'title': True})
            if not job_title_elem:
                return None
                
            job_title = job_title_elem.text.strip()
            
            # Company name extraction with fallback
            company_elem = job_box.find('h3', class_='joblist-comp-name')
            if not company_elem:
                company_elem = job_box.find('h4', class_='comp-name')
            company_name = company_elem.text.strip() if company_elem else "Company Not Listed"

            # Duration with fallback
            duration_elem = job_box.find('span', class_='sim-posted')
            if not duration_elem:
                duration_elem = job_box.find('span', class_='posting-time')
            posting_duration = duration_elem.text.strip() if duration_elem else "Recently Posted"

            # Skills extraction with improved handling
            skills_container = job_box.find('span', class_='srp-skills') or \
                             job_box.find('ul', class_='top-jd-dtl clearfix')
            if skills_container:
                skills = [skill.strip() for skill in skills_container.text.split(',')]
            else:
                skills = ["Skills not specified"]

            # Get job details URL with validation
            link_elem = job_box.find('a', href=True)
            if not link_elem:
                return None
            more_details = link_elem['href']
            if not more_details.startswith('http'):
                more_details = f"https://www.timesjobs.com{more_details}"

            logger.info(f"Successfully parsed job: {job_title}")
            
            return JobPosting(
                company_name=company_name,
                job_title=job_title,
                posting_duration=posting_duration,
                skills=', '.join(skills),
                more_details=more_details,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                search_keyword=keyword
            )
        except Exception as e:
            logger.error(f"Error parsing job: {str(e)}")
            return None

    def search_jobs(self, keyword: str):
        """Enhanced job search method with better error handling."""
        self.current_keyword = keyword
        self.is_searching = True
        page = 1
        
        while self.is_searching:
            try:
                url = self._build_search_url(keyword, page)
                logger.info(f"Searching URL: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Updated job listing selector
                job_boxes = soup.find_all('li', class_='clearfix job-bx wht-shd-bx') or \
                           soup.find_all('div', class_='job-bx-title')
                
                if not job_boxes:
                    logger.warning(f"No jobs found on page {page}. Response length: {len(response.text)}")
                    # Save HTML for debugging
                    with open(f'debug_page_{page}.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    if page > 1:
                        break
                    time.sleep(30)
                    continue

                jobs_found = False
                for job_box in job_boxes:
                    if not self.is_searching:
                        break
                    
                    job = self._parse_job(job_box, keyword)
                    if job:
                        jobs_found = True
                        if self._save_job(job):
                            result_queue.put(job.to_dict())
                
                if not jobs_found:
                    logger.warning(f"No valid jobs found on page {page}")
                    if page > 1:
                        break
                
                page += 1
                time.sleep(5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                self.retry_count += 1
                if self.retry_count > self.max_retries:
                    logger.error("Max retries exceeded")
                    break
                time.sleep(self.retry_delay * self.retry_count)
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                break