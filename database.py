import mysql.connector
import json

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='linkedin_db'
    )
    

def prepare_profile_for_db(raw):
    basic = raw.get("basic_info", {})
    exp = raw.get("experience", [])
    first_exp = exp[0] if exp else {}

    return {
        "profile_link": raw.get("profile_link", ""),

        "name": basic.get("name", ""),
        "headline": basic.get("head_line", ""),
        "location": basic.get("location", ""),
        "connections": basic.get("connections", ""),
        "last_activity": basic.get("last_activity", ""),
        "profile_url": basic.get("profile_url", ""),
        
        "job_title": first_exp.get("job_title", ""),
        "company_name": first_exp.get("company_name", ""),
        "company_link": first_exp.get("company_link", ""),
        "work_mode": first_exp.get("work_mode", ""),
        "total_duration": first_exp.get("total_duration", ""),
        "job_type": first_exp.get("job_type", ""),
        "duration": first_exp.get("duration", ""),
        "tenurity": first_exp.get("tenurity", ""),

        "skills": ", ".join(raw.get("skills", [])),
        "experience_json": exp
    }



def insert_li_person(profile,task_id):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO li_person (
        task_id, name, headline, location, connections, last_activity,
        profile_url, job_title, company_name, company_link, work_mode, total_duration,
        job_type, duration, tenurity, skills, experience_json
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        task_id,
        profile["name"],
        profile["headline"],
        profile["location"],
        profile["connections"],
        profile["last_activity"],
        profile["profile_url"],
        profile["job_title"],
        profile["company_name"],
        profile["company_link"],
        profile["work_mode"],
        profile["total_duration"],
        profile["job_type"],
        profile["duration"],
        profile["tenurity"],
        profile["skills"],
        json.dumps(profile["experience_json"], ensure_ascii=False)
    ))

    conn.commit()
    cursor.close()
    conn.close()
    

def upsert_li_person_master(profile,task_id):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO li_person_master (
        task_id, name, headline, location, connections, last_activity,
        profile_url, job_title, company_name, company_link, work_mode, total_duration,
        job_type, duration, tenurity, skills, experience_json
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        task_id=VALUES(task_id),
        name=VALUES(name),
        headline=VALUES(headline),
        location=VALUES(location),
        connections=VALUES(connections),
        last_activity=VALUES(last_activity),
        profile_url=VALUES(profile_url),
        company_name=VALUES(company_name),
        company_link=VALUES(company_link),
        work_mode=VALUES(work_mode),
        total_duration=VALUES(total_duration),
        job_type=VALUES(job_type),
        duration=VALUES(duration),
        tenurity=VALUES(tenurity),
        skills=VALUES(skills),
        experience_json=VALUES(experience_json),
        updated_at = CURRENT_TIMESTAMP
    """

    cursor.execute(sql, (
        task_id,
        profile["name"],
        profile["headline"],
        profile["location"],
        profile["connections"],
        profile["last_activity"],
        profile["profile_url"],
        profile["job_title"],
        profile["company_name"],
        profile["company_link"],
        profile["work_mode"],
        profile["total_duration"],
        profile["job_type"],
        profile["duration"],
        profile["tenurity"],
        profile["skills"],
        json.dumps(profile["experience_json"], ensure_ascii=False)
    ))

    conn.commit()
    cursor.close()
    conn.close()

    