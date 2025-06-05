# parse_hh.py

import requests
from bs4 import BeautifulSoup

def get_html(url: str) -> str:
    """
    Получает HTML-код по переданному URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def extract_vacancy_data(html: str) -> str:
    """
    Извлекает из HTML вакансии ключевые поля:
    - Заголовок вакансии (h1)
    - Название компании
    - Зарплату
    - Описание вакансии (блок data-qa="vacancy-description")
    Возвращает строку в Markdown-формате.
    """
    soup = BeautifulSoup(html, 'html.parser')

    def safe_text(selector, attrs=None):
        el = soup.find(selector, attrs or {})
        return el.text.strip() if el else "Не найдено"

    title = safe_text('h1')
    company = safe_text('a', {'data-qa': 'vacancy-company-name'})
    salary = safe_text('span', {'data-qa': 'vacancy-salary'})
    desc_block = soup.find('div', {'data-qa': 'vacancy-description'})
    description_text = desc_block.get_text(separator="\n").strip() if desc_block else "Описание не найдено"

    markdown = f"# Вакансия: {title}\n\n"
    markdown += f"**Компания:** {company}\n\n"
    markdown += f"**Зарплата:** {salary}\n\n"
    markdown += f"## Описание вакансии:\n{description_text}\n"
    return markdown.strip()


def extract_resume_data(html: str) -> str:
    """
    Извлекает из HTML резюме ключевые поля:
    - ФИО (h2 с data-qa="bloko-header-1")
    - Пол, возраст (первый <p>)
    - Локация (span с data-qa="resume-personal-address")
    - Должность (span data-qa="resume-block-title-position")
    - Статус (span data-qa="job-search-status")
    - Опыт работы (блок data-qa="resume-block-experience")
    - Навыки (блок data-qa="skills-table")
    Возвращает строку в Markdown-формате.
    """
    soup = BeautifulSoup(html, 'html.parser')

    def safe_text(selector, **kwargs):
        el = soup.find(selector, kwargs)
        return el.text.strip() if el else "Не найдено"

    name = safe_text('h2', **{'data-qa': 'bloko-header-1'})
    gender_age = safe_text('p')
    location = safe_text('span', **{'data-qa': 'resume-personal-address'})
    job_title = safe_text('span', **{'data-qa': 'resume-block-title-position'})
    job_status = safe_text('span', **{'data-qa': 'job-search-status'})

    # Опыт работы
    experiences = []
    exp_section = soup.find('div', {'data-qa': 'resume-block-experience'})
    if exp_section:
        items = exp_section.find_all('div', class_='resume-block-item-gap')
        for item in items:
            try:
                period = item.find('div', class_='bloko-column_s-2').text.strip()
                duration = item.find('div', class_='bloko-text').text.strip()
                period = period.replace(duration, f" ({duration})")
                company = item.find('div', class_='bloko-text_strong').text.strip()
                position = item.find('div', **{'data-qa': 'resume-block-experience-position'}).text.strip()
                desc = item.find('div', **{'data-qa': 'resume-block-experience-description'}).text.strip()
                experiences.append(f"**{period}**\n*{company}* — **{position}**\n{desc}\n")
            except Exception:
                continue

    # Навыки
    skills = []
    skills_section = soup.find('div', {'data-qa': 'skills-table'})
    if skills_section:
        skills = [tag.text.strip() for tag in skills_section.find_all('span', {'data-qa': 'bloko-tag__text'})]

    markdown = f"# Резюме: {name}\n\n"
    markdown += f"**{gender_age}**\n\n"
    markdown += f"**Локация:** {location}\n\n"
    markdown += f"**Должность:** {job_title}\n\n"
    markdown += f"**Статус:** {job_status}\n\n"
    markdown += "## Опыт работы:\n"
    markdown += "\n".join(experiences) if experiences else "Опыт работы не найден.\n"
    markdown += "\n## Навыки:\n"
    markdown += ", ".join(skills) if skills else "Навыки не указаны.\n"

    return markdown.strip()
