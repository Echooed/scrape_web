#1 scrap simple html file.

from bs4 import BeautifulSoup

with open('home.html', 'r') as html_file:
    content =html_file.read()
    
    soup = BeautifulSoup(content, 'lxml')
    course_cards =soup.find_all('div', class_ = 'card-body')
    for course in course_cards:
        course_price = course.a.text.split()[-1]
        print(f'The course {course.h5.text} cost ${course_price[:-1]}')