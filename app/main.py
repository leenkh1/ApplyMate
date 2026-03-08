import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from pydantic import BaseModel
from app.core.trace import Trace
from app.modules.router import route
from app.modules import resume_flow, email_flow
from fastapi import HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
def ui_home():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="static/index.html not found")
    return FileResponse(index_path, media_type="text/html")

load_dotenv(BASE_DIR / ".env")


class ExecuteRequest(BaseModel):
    prompt: str


@app.get("/api/team_info")
def team_info():
    return {
        "group_batch_order_number": "2_04",
        "team_name": "Ameer_Leen_Yechezkel_Aviv",
        "students": [
            {"name": "Ameer kashkoush", "email": "Ameerk@campus.technion.ac.il"},
            {"name": "Leen Khamis", "email": "leen.khamis@campus.technion.ac.il"},
            {"name": "Aviv Cohen", "email": "cohen.aviv@campus.technion.ac.il"},
            {"name": "Yechezkel Nikop", "email": "nikop@campus.technion.ac.il"},
        ],
    }


@app.get("/api/agent_info")
def agent_info():
    return {
        "description": (
            "ApplyMate is an AI agent that supports the job-application lifecycle: "
            "it tailors a student’s resume to a specific job description using only supported facts, "
            "and analyzes recruiter emails to extract intent, required actions, deadlines, and next steps."
        ),
        "purpose": (
            "Support students throughout the full job-application lifecycle by tailoring resumes to specific roles and analyzing recruiter emails within the same application context. "
            "Provide grounded, retrieval-enhanced guidance that helps users understand their fit, improve their materials, and respond professionally to rejections, requests, and interview invitations. "
            "Make the process more effective, personalized, and transparent through traceable multi-step reasoning, persistent context, and practical next-step recommendations."
        ),
        "prompt_template": {
            "template": (
                "Choose one:\n"
                "A) Resume tailoring (creates an application context in Supabase)\n"
                "TASK: RESUME_TAILOR\n"
                "JOB_TITLE: {job_title}\n"
                "CV:\n<<<\n{paste_cv_text}\n>>>\n"
                "JOB_DESCRIPTION:\n<<<\n{paste_job_description_text}\n>>>\n\n"
                "You will receive an APPLICATION_ID in the response. Save it.\n\n"
                "B) Recruiter email analysis (reuse stored context)\n"
                "TASK: EMAIL_ANALYZE\n"
                "APPLICATION_ID: {application_id}\n"
                "EMAIL:\n<<<\n{paste_email_text}\n>>>\n"
            )
        },
        "prompt_examples": [
            {
                "prompt": """TASK: RESUME_TAILOR
        JOB_TITLE: Data Analyst Intern
        CV:
        <<<
        Name: Leen Khamis
        Education: B.Sc. in Data Science and Engineering, Technion
        Skills: Python, SQL, Pandas, Tableau, Excel, Data Visualization
        Projects:
        - Built an interactive Tableau dashboard to analyze customer retention trends from sales data.
        - Used Python and Pandas to clean and analyze survey data and present insights.
        Experience:
        - Student Assistant: prepared weekly reports and summarized data for academic staff.
        >>>
        JOB_DESCRIPTION:
        <<<
        We are looking for a Data Analyst Intern to support reporting and business analysis.
        Requirements:
        - Strong SQL and Excel skills
        - Experience with dashboards and data visualization
        - Ability to analyze datasets and communicate findings clearly
        - Familiarity with Python is an advantage
        >>>""",
                "full_response": """Thank you for providing the relevant information. Below is the analysis explanation:

        Match score: 90/100 - CV lists the core technical requirements (SQL, Excel, Tableau/data visualization, Python/Pandas) and shows relevant projects (Tableau dashboard on sales/customer retention; Python/Pandas survey analysis) plus weekly reporting experience; missing quantification of impact and explicit examples of SQL usage or database environments.

        Here are the strengths between your CV and the job description:
        - Strong SQL and Excel skills — CV Skills list includes "SQL" and "Excel".
        - Experience with dashboards and data visualization — CV Projects: "Built an interactive Tableau dashboard to analyze customer retention trends from sales data" and Skills: "Tableau, Data Visualization".
        - Ability to analyze datasets and communicate findings clearly — CV Project: "Used Python and Pandas to clean and analyze survey data and present insights" and Experience: "prepared weekly reports and summarized data for academic staff".
        - Familiarity with Python — CV Skills list includes "Python" and the survey project used Python and Pandas.

        Here are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:
        1. Put a short skills-first header or reorder Skills to list SQL, Excel, Tableau, Python (and Pandas) first so ATS and hiring managers immediately see core requirements.
        2. Expand the Tableau project bullet to highlight scope and outcome using only facts you can support: mention the data source (sales data), the objective (customer retention trends), the dashboard type (interactive), and any improvements to reporting or decision-making if available.
        3. For the Python/Pandas project, rephrase to clarify your analytical actions and outputs: e.g., "cleaned and analyzed survey data using Python and Pandas and presented insights" — add the specific types of analyses or visualizations you performed if you can support them.
        4. Add concise examples of SQL-related work (if you performed any): state the kinds of queries or tasks (joins, aggregations, reporting queries) and the context (datasets or reporting) rather than inventing database names.
        5. Emphasize reporting and business-analysis language from the JD: include the phrases "reporting" and "business analysis" near your Student Assistant bullet and projects to improve ATS alignment (e.g., "prepared weekly reports for academic staff supporting reporting and analysis").
        6. Quantify workload and cadence where possible using existing facts: keep "weekly reports" but, if true, add number of stakeholders or frequency impact (e.g., supported X academic staff) only if you can verify it.
        7. Reorder content so that the most relevant project (Tableau dashboard) appears above the Student Assistant entry to foreground visualization and dashboard experience.
        8. Keep technical tool names exact (SQL, Python, Pandas, Tableau, Excel) to match ATS keyword matching; avoid broad paraphrases that might reduce keyword hits.

        Here are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:
        - sql
        - excel
        - tableau
        - python
        - analytics
        - data analysis
        - communication
        - problem solving
        - statistics
        - teamwork
        - attention to detail

        APPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b
        ---------------------------------------------------------------------------------------------------------------

        Here is a candidate of a good CV that matches the job description you provided:
        <<<
        FINANCIAL ANALYST INTERN

        Skills

        Financial Planning & Analysis, Analytical skills, Forecasting, Portfolio & Wealth Management, Financial Reporting, Business Analysis, Financial Consulting, Quantitative Analysis, Market Research, Financial Modelling, Project Management, Strategy, Operations, Risk Management, Corporate Finance, Global Finance, Product Management Slabware, Quickbooks, Busy LS, Microsoft Office, Microsoft Excel, Mutual Funds, Alternate Investments, Real Estate Funds, Mortgages, Consumer Loans, Insurance, Microsoft PowerPoint, Microsoft Access, Microsoft Outlook

        Experience

        05/2017 to 08/2017 Financial Analyst Intern Company Name － City , State - Augmented company profits by 25% by conducting a detailed financial analysis and refining the budgets and forecasts.
        - Analyzed company financial reports to make recommendations for revenue generation and cost reduction.
        - Reduced 30% costs by designing financial process tools, and implementing pricing strategies for process improvement.
        - Spearheaded and led due diligence for Acue Marmonite's international projects in India, identifying key risk factors and forecasting investment viability and educated the senior management about the project NPV.
        - Developed innovative financial tools to simplify Business Requirement Documentation (BRD's), which helped record-keeping, understanding client business and expanding client relationships.

        11/2015 to 07/2016 Manager Company Name － City - Retail Banking - Affluent Business.
        - Amplified the high net worth client portfolio from USD 16 million to USD 18 million in less than 9 months.
        - Recommended customized product portfolios to high net worth clients through financial planning and investment analysis resulting in average client portfolio growth up to 27%.
        - Administered regulatory and procedural compliance to ensure adherence to proper accounting procedures.
        - Advised clients about global trade, designing customer centric propositions for hedging and mitigating risk.

        09/2013 to 10/2015 Senior Advance Wealth Manager Company Name － City - Retail Banking, and Wealth Management.
        - Increased total portfolio value by USD 5 million, making it the largest in the region.
        - Assessed client's financial objectives and risk profiles, identified investment opportunities, and prepared customized recommendations for asset allocation.
        - Exhibited leadership capabilities by supporting, training and mentoring a team of wealth managers.
        - Achieved highest personal loan sales figures for the year 2014 within the region.

        04/2012 to 08/2013 Deputy Manager Company Name － City - Enhanced portfolio value from USD 0.65 million to USD 1.05 million by acquiring new clients in the region.
        - Boosted portfolio growth by 18% by analysing high net worth client portfolios, and advising tailed investment solutions.
        - Exceeded bank's budgeted portfolio growth expectations by 34%.
        - Carried out non-resident operations in the branch and implemented the retail Foreign Exchange (FX) Rated in TOP 40 mortgage sales performers award PAN INDIA within 5 months of joining Axis Bank.
        - Fast-tracked to the position of Senior Wealth Manager within 15 months of joining HSBC.
        - Received 'Dynamo' award for outstanding performance and commitment to fairness and integrity (HSBC).
        - Ranked first among wealth managers in the HSBC Delhi region (Aug '14).
        - Received 'Outstanding Performer' award.
        - Ranked first for following Compliance and AML Practices for Operational Excellence in HSBC (2014).

        Education and Training

        Dec 2017 Master of Business Administration : Financial Analysis and Investments University of Connecticut School of Business － City , State Financial Analysis and Investments STEM - qualifying for 36 months OPT)
        *Vice President - Marketing & Finance for UConn Graduate Consulting Club
        *Student Consultant and Team Lead to CT based Start-up
        *Winner of the Cigna Strategic Investment Case Challenge

        Jun 2010 Bachelor of Arts : Economics Sri Venkateswara College, University of Delhi － City India Economics

        Skills

        accounting, Analytical skills, Banking, budgets, Business Analysis, Consultant, Consulting, Corporate Finance, cost reduction, client, clients, designing, Documentation, due diligence, senior management, Fast, Finance, Financial, financial analysis, Financial Planning & Analysis, Financial Consulting, financial planning, financial reports, Financial Reporting, Forecasting, Foreign Exchange, Funds, Insurance, investment analysis, Investments, leadership, Team Lead, Market Research, Marketing, mentoring, Microsoft Access, Microsoft Excel, Microsoft Office, Microsoft Outlook, Microsoft PowerPoint, pricing strategies, process improvement, Product Management, Project Management, Quantitative Analysis, Quickbooks, Real Estate, record-keeping, Requirement, Retail, Risk Management, sales, Strategy, Strategic, Wealth Management
        >>>""",
                "steps": [
                    {
                        "module": "Planner LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are the Planner LLM.\nTask: extract structured fields from the user's prompt AND propose a short task list.\nReturn ONLY valid JSON with these keys:\n{\n  \"task\": \"RESUME_TAILOR\" | \"EMAIL_ANALYZE\" | \"UNKNOWN\",\n  \"application_id\": string,\n  \"job_title\": string,\n  \"cv_text\": string,\n  \"jd_text\": string,\n  \"email_text\": string,\n  \"task_list\": [string, ...]\n}\nRules:\n- If a field is missing, return an empty string for it.\n- task_list must be 3-7 short items.\n- For RESUME_TAILOR: include in the task_list steps like parsing CV/JD, scoring/matching, ATS-aligned tips, market skills retrieval, and storing APPLICATION_ID.\n- For EMAIL_ANALYZE: task_list should include short steps such as parsing the email, loading application context if APPLICATION_ID exists, identifying the email intent, retrieving relevant HR/technical/rejection-related resources only if needed, and generating next steps plus a suggested reply.\n- Do not include any extra keys or commentary.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK: RESUME_TAILOR\nJOB_TITLE: Data Analyst Intern\nCV:\n<<<\nName: Leen Khamis\nEducation: B.Sc. in Data Science and Engineering, Technion\nSkills: Python, SQL, Pandas, Tableau, Excel, Data Visualization\nProjects:\n- Built an interactive Tableau dashboard to analyze customer retention trends from sales data.\n- Used Python and Pandas to clean and analyze survey data and present insights.\nExperience:\n- Student Assistant: prepared weekly reports and summarized data for academic staff.\n>>>\nJOB_DESCRIPTION:\n<<<\nWe are looking for a Data Analyst Intern to support reporting and business analysis.\nRequirements:\n- Strong SQL and Excel skills\n- Experience with dashboards and data visualization\n- Ability to analyze datasets and communicate findings clearly\n- Familiarity with Python is an advantage\n>>>"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHEt5t6bM95SQst5JDmpZWANEAIS2",
                            "created": 1773001175,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "{\n  \"task\": \"RESUME_TAILOR\",\n  \"application_id\": \"\",\n  \"job_title\": \"Data Analyst Intern\",\n  \"cv_text\": \"Name: Leen Khamis\\nEducation: B.Sc. in Data Science and Engineering, Technion\\nSkills: Python, SQL, Pandas, Tableau, Excel, Data Visualization\\nProjects:\\n- Built an interactive Tableau dashboard to analyze customer retention trends from sales data.\\n- Used Python and Pandas to clean and analyze survey data and present insights.\\nExperience:\\n- Student Assistant: prepared weekly reports and summarized data for academic staff.\",\n  \"jd_text\": \"We are looking for a Data Analyst Intern to support reporting and business analysis.\\nRequirements:\\n- Strong SQL and Excel skills\\n- Experience with dashboards and data visualization\\n- Ability to analyze datasets and communicate findings clearly\\n- Familiarity with Python is an advantage\",\n  \"email_text\": \"\",\n  \"task_list\": [\n    \"Parse CV and JD to extract skills, experience, and requirements\",\n    \"Score/match CV to JD and identify gaps and high-impact opportunities\",\n    \"Retrieve market/role-specific keywords and skills for Data Analyst Intern\",\n    \"Provide ATS-aligned tips and rewrite bullets to emphasize SQL, Excel, dashboards, and Python\",\n    \"Store application_id and package tailored resume + short pitch for submission\"\n  ]\n}",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 611,
                                "prompt_tokens": 405,
                                "total_tokens": 1016,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 320,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "module": "Executor LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You tailor resumes to a job description.\nHard rules:\n1) Use ONLY facts found in the CV text. Do NOT invent companies, dates, skills, projects, or metrics.\n2) Do NOT ask questions and do NOT offer follow-up help.\n3) Do NOT add any extra section titles, summaries, checklists, examples, or closing remarks.\n4) Your answer must end immediately after the common-skills section content (bullets or the Not available line). The server will append APPLICATION_ID.\n5) MARKET_COMMON_SKILLS is awareness-only. Never claim the candidate has a skill unless it appears in the CV.\n6) If MARKET_COMMON_SKILLS is missing, '(Not available)', or if the retrieved skills_list clearly does NOT match the JOB_TITLE domain (for example: JOB_TITLE is empty or nonsensical, or the top_match role/skills are for a very different profession), you MUST output the common-skills section as:\nHere are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\nCommon skills for this role is Not available\nand then STOP.\n\nOUTPUT FORMAT (MUST FOLLOW EXACTLY):\nThank you for providing the relevant information. Below is the analysis explanation:\n\nMatch score: <0-100>/100 - <short explanation>\n\nHere are the strengths between your CV and the job description:\n- <one or more bullets>\n- Strengths bullets MUST be direct overlaps with the JD (requirements or nice-to-have).\n- Each bullet must mention a JD keyword/requirement AND the matching CV fact.\n- Do NOT list general CV facts (e.g., education, Excel, PowerPoint) unless the JD explicitly asks for them.\n- If there are zero direct overlaps, output exactly ONE bullet in this section:\n- No direct strengths were identified between your CV and the job description based on the provided CV text.\n\nHere are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:\n<a prioritized numbered list with as many strong tips as needed>\n\nHere are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\n- <zero or more skills>\n\nAdditional constraints:\n- Strengths must be JD-aligned matches only (CV ∩ JD). If none, use the single 'No direct strengths...' bullet.\n- The only section headers allowed are EXACTLY these three lines:\n  Here are the strengths between your CV and the job description:\n  Here are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:\n  Here are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\n- For the common-skills bullets: when MARKET_COMMON_SKILLS is valid and clearly in-domain, you may select ONLY those skill names from MARKET_COMMON_SKILLS.skills_list that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain (even if they do not appear explicitly in the CV or JD) and skip clearly unrelated or overly niche items. Do NOT add any skills that are not from MARKET_COMMON_SKILLS.skills_list and do NOT rename skill names.\nIn the tips section, you may briefly suggest de-emphasizing or removing CV items that are clearly unrelated to the JD (e.g., unrelated hobbies), but only if those items explicitly appear in the CV text.- If REVISION_INSTRUCTIONS is provided, revise your previous output accordingly while keeping this exact structure.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK: RESUME_TAILOR\nTASK_LIST:\n- Parse CV and JD to extract skills, experience, and requirements\n- Score/match CV to JD and identify gaps and high-impact opportunities\n- Retrieve market/role-specific keywords and skills for Data Analyst Intern\n- Provide ATS-aligned tips and rewrite bullets to emphasize SQL, Excel, dashboards, and Python\n- Store application_id and package tailored resume + short pitch for submission\n\nJOB_TITLE: Data Analyst Intern\nCV:\n<<<\nName: Leen Khamis\nEducation: B.Sc. in Data Science and Engineering, Technion\nSkills: Python, SQL, Pandas, Tableau, Excel, Data Visualization\nProjects:\n- Built an interactive Tableau dashboard to analyze customer retention trends from sales data.\n- Used Python and Pandas to clean and analyze survey data and present insights.\nExperience:\n- Student Assistant: prepared weekly reports and summarized data for academic staff.\n>>>\nJOB_DESCRIPTION:\n<<<\nWe are looking for a Data Analyst Intern to support reporting and business analysis.\nRequirements:\n- Strong SQL and Excel skills\n- Experience with dashboards and data visualization\n- Ability to analyze datasets and communicate findings clearly\n- Familiarity with Python is an advantage\n>>>\n\n\nMARKET_COMMON_SKILLS:\n- query_title: Data Analyst Intern\n- top_match: data analytics intern summer (score=0.755, n_posts=2)\n- skills_list: mathematics, intellectual curiosity, engineering, finance, analytics, data analysis, sql, problem solving, teamwork, snowflake, excel, economics, r, computer science, tableau, python, equal opportunity employer, communication, paid, benefits, statistics, artificial intelligence, mentoring, machine learning, attention to detail\n"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHEtEPO4NJeoRsEzRHyXTAGKMjwm0",
                            "created": 1773001184,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "Thank you for providing the relevant information. Below is the analysis explanation:\n\nMatch score: 90/100 - CV lists the core technical requirements (SQL, Excel, Tableau/data visualization, Python/Pandas) and shows relevant projects (Tableau dashboard on sales/customer retention; Python/Pandas survey analysis) plus weekly reporting experience; missing quantification of impact and explicit examples of SQL usage or database environments.\n\nHere are the strengths between your CV and the job description:\n- Strong SQL and Excel skills — CV Skills list includes \"SQL\" and \"Excel\".\n- Experience with dashboards and data visualization — CV Projects: \"Built an interactive Tableau dashboard to analyze customer retention trends from sales data\" and Skills: \"Tableau, Data Visualization\".\n- Ability to analyze datasets and communicate findings clearly — CV Project: \"Used Python and Pandas to clean and analyze survey data and present insights\" and Experience: \"prepared weekly reports and summarized data for academic staff\".\n- Familiarity with Python — CV Skills list includes \"Python\" and the survey project used Python and Pandas.\n\nHere are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:\n1. Put a short skills-first header or reorder Skills to list SQL, Excel, Tableau, Python (and Pandas) first so ATS and hiring managers immediately see core requirements.\n2. Expand the Tableau project bullet to highlight scope and outcome using only facts you can support: mention the data source (sales data), the objective (customer retention trends), the dashboard type (interactive), and any improvements to reporting or decision-making if available.\n3. For the Python/Pandas project, rephrase to clarify your analytical actions and outputs: e.g., \"cleaned and analyzed survey data using Python and Pandas and presented insights\" — add the specific types of analyses or visualizations you performed if you can support them.\n4. Add concise examples of SQL-related work (if you performed any): state the kinds of queries or tasks (joins, aggregations, reporting queries) and the context (datasets or reporting) rather than inventing database names.\n5. Emphasize reporting and business-analysis language from the JD: include the phrases \"reporting\" and \"business analysis\" near your Student Assistant bullet and projects to improve ATS alignment (e.g., \"prepared weekly reports for academic staff supporting reporting and analysis\").\n6. Quantify workload and cadence where possible using existing facts: keep \"weekly reports\" but, if true, add number of stakeholders or frequency impact (e.g., supported X academic staff) only if you can verify it.\n7. Reorder content so that the most relevant project (Tableau dashboard) appears above the Student Assistant entry to foreground visualization and dashboard experience.\n8. Keep technical tool names exact (SQL, Python, Pandas, Tableau, Excel) to match ATS keyword matching; avoid broad paraphrases that might reduce keyword hits.\n\nHere are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\n- sql\n- excel\n- tableau\n- python\n- analytics\n- data analysis\n- communication\n- problem solving\n- statistics\n- teamwork\n- attention to detail",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 2519,
                                "prompt_tokens": 1076,
                                "total_tokens": 3595,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 1856,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "module": "Replan LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are the Replan LLM.\nGoal: decide if the draft is good enough to finalize, or if a revision is required.\nReturn ONLY valid JSON with these keys:\n{\n  \"is_solved\": true|false,\n  \"needs_reflect\": true|false,\n  \"rationale\": string,\n  \"preserve\": [string, ...],\n  \"executor_instructions\": string,\n  \"final_response\": string\n}\n\nFORMAT CONTRACT (MUST MATCH EXECUTOR EXACTLY):\nA) The very first line MUST be exactly:\nThank you for providing the relevant information. Below is the analysis explanation:\nB) The next required line MUST start with 'Match score:' and include '/100'. This is NOT a section header; it is a single required line.\nC) The ONLY allowed section header lines are EXACTLY these three lines, and they MUST appear in this exact order:\n   Here are the strengths between your CV and the job description:\n   Here are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:\n   Here are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\nD) No other section headers or extra titles are allowed.\nE) The document MUST end immediately after the common-skills section content.\n   If common skills are unavailable, the common-skills section MUST be exactly:\n   Here are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\n   Common skills for this role is Not available\n   and then STOP (no trailing text).\nF) Common-skills items must be copied exactly from MARKET_COMMON_SKILLS.skills_list (no renaming, no casing changes). Do NOT request capitalization/normalization of skill names.\nG) Do NOT request removing the opening line if it matches A.\n\nRules:\n- If is_solved=true:\n  - final_response MUST contain the final user-facing answer.\n  - needs_reflect MUST be false.\n  - executor_instructions MUST be empty.\n- If is_solved=false:\n  - final_response MUST be empty.\n- Set needs_reflect=true ONLY for worst-case situations:\n  A) Hallucination risk (invented dates/availability/platform/personal details; invented skills not in CV; invented company/project).\n  B) Contradictions (two deadlines; conflicting intent; next steps contradict email).\n  C) Unclear intent that changes the whole output.\n  D) Severe format failure where minimal edits are unreliable.\n- Otherwise set needs_reflect=false and provide concrete executor_instructions (minimal edits) for the Executor.\n- When deciding is_solved for normal drafts (no worst-case condition):\n  - Treat the draft as good enough (is_solved=true, needs_reflect=false) if it satisfies the FORMAT CONTRACT and there is no clear hallucination or contradiction.\n  - Do NOT request a revision only for minor style or wording issues.\n  - If there are small but clear structural/format issues you can describe precisely (e.g., missing one of the three exact header lines, extra text after the common-skills section, or the match score line missing '/100'), set is_solved=false and needs_reflect=false and provide a short executor_instructions checklist with minimal edits only.\n- If REFLECTION_JSON is provided:\n  - Set needs_reflect=false and convert must_fix into an ordered executor_instructions list.\n  - Include up to 5 preserve items based on pros.\n- No extra keys, no markdown, no commentary outside the JSON.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK_KIND: RESUME_TAILOR\nCONTEXT_HINT:\n<<<\nJOB_TITLE: Data Analyst Intern\nCV_SNIPPET: Name: Leen Khamis Education: B.Sc. in Data Science and Engineering, Technion Skills: Python, SQL, Pandas, Tableau, Excel, Data Visualization Projects: - Built an interactive Tableau dashboard to analyze customer retention trends from sales data. - Used Python and Pandas to clean and analyze survey data and present insights. Experience: - Student Assistant: prepared weekly reports and summarized data for academic staff.\nJD_SNIPPET: We are looking for a Data Analyst Intern to support reporting and business analysis. Requirements: - Strong SQL and Excel skills - Experience with dashboards and data visualization - Ability to analyze datasets and communicate findings clearly - Familiarity with Python is an advantage\nFORMAT_REMINDER: Use the fixed headers/lines exactly; end after common skills.\n\n>>>\nDRAFT_RESPONSE:\n<<<\nThank you for providing the relevant information. Below is the analysis explanation:\n\nMatch score: 90/100 - CV lists the core technical requirements (SQL, Excel, Tableau/data visualization, Python/Pandas) and shows relevant projects (Tableau dashboard on sales/customer retention; Python/Pandas survey analysis) plus weekly reporting experience; missing quantification of impact and explicit examples of SQL usage or database environments.\n\nHere are the strengths between your CV and the job description:\n- Strong SQL and Excel skills — CV Skills list includes \"SQL\" and \"Excel\".\n- Experience with dashboards and data visualization — CV Projects: \"Built an interactive Tableau dashboard to analyze customer retention trends from sales data\" and Skills: \"Tableau, Data Visualization\".\n- Ability to analyze datasets and communicate findings clearly — CV Project: \"Used Python and Pandas to clean and analyze survey data and present insights\" and Experience: \"prepared weekly reports and summarized data for academic staff\".\n- Familiarity with Python — CV Skills list includes \"Python\" and the survey project used Python and Pandas.\n\nHere are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:\n1. Put a short skills-first header or reorder Skills to list SQL, Excel, Tableau, Python (and Pandas) first so ATS and hiring managers immediately see core requirements.\n2. Expand the Tableau project bullet to highlight scope and outcome using only facts you can support: mention the data source (sales data), the objective (customer retention trends), the dashboard type (interactive), and any improvements to reporting or decision-making if available.\n3. For the Python/Pandas project, rephrase to clarify your analytical actions and outputs: e.g., \"cleaned and analyzed survey data using Python and Pandas and presented insights\" — add the specific types of analyses or visualizations you performed if you can support them.\n4. Add concise examples of SQL-related work (if you performed any): state the kinds of queries or tasks (joins, aggregations, reporting queries) and the context (datasets or reporting) rather than inventing database names.\n5. Emphasize reporting and business-analysis language from the JD: include the phrases \"reporting\" and \"business analysis\" near your Student Assistant bullet and projects to improve ATS alignment (e.g., \"prepared weekly reports for academic staff supporting reporting and analysis\").\n6. Quantify workload and cadence where possible using existing facts: keep \"weekly reports\" but, if true, add number of stakeholders or frequency impact (e.g., supported X academic staff) only if you can verify it.\n7. Reorder content so that the most relevant project (Tableau dashboard) appears above the Student Assistant entry to foreground visualization and dashboard experience.\n8. Keep technical tool names exact (SQL, Python, Pandas, Tableau, Excel) to match ATS keyword matching; avoid broad paraphrases that might reduce keyword hits.\n\nHere are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\n- sql\n- excel\n- tableau\n- python\n- analytics\n- data analysis\n- communication\n- problem solving\n- statistics\n- teamwork\n- attention to detail\n>>>\n"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHEtYdciI5L5omplgZuAS71HWcawP",
                            "created": 1773001204,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "{\n  \"is_solved\": true,\n  \"needs_reflect\": false,\n  \"rationale\": \"The draft adheres to the required FORMAT CONTRACT (opening line, Match score line, the three exact headers in order, and ends immediately after the common-skills section). It accurately compares the CV to the job description without introducing hallucinations or contradictions and gives practical, actionable tips to improve ATS alignment and relevance for the Data Analyst Intern role.\",\n  \"preserve\": [\n    \"Strong listing of core technical requirements (SQL, Excel, Tableau, Python/Pandas)\",\n    \"Tableau dashboard project describing customer retention trends\",\n    \"Python/Pandas project describing cleaning, analysis, and presentation of insights\",\n    \"Student Assistant weekly reporting experience\",\n    \"Explicit recommendation to keep exact tool names for ATS matching\"\n  ],\n  \"executor_instructions\": \"\",\n  \"final_response\": \"Thank you for providing the relevant information. Below is the analysis explanation:\\n\\nMatch score: 90/100 - CV lists the core technical requirements (SQL, Excel, Tableau/data visualization, Python/Pandas) and shows relevant projects (Tableau dashboard on sales/customer retention; Python/Pandas survey analysis) plus weekly reporting experience; missing quantification of impact and explicit examples of SQL usage or database environments.\\n\\nHere are the strengths between your CV and the job description:\\n- Strong SQL and Excel skills — CV Skills list includes \\\"SQL\\\" and \\\"Excel\\\".\\n- Experience with dashboards and data visualization — CV Projects: \\\"Built an interactive Tableau dashboard to analyze customer retention trends from sales data\\\" and Skills: \\\"Tableau, Data Visualization\\\".\\n- Ability to analyze datasets and communicate findings clearly — CV Project: \\\"Used Python and Pandas to clean and analyze survey data and present insights\\\" and Experience: \\\"prepared weekly reports and summarized data for academic staff\\\".\\n- Familiarity with Python — CV Skills list includes \\\"Python\\\" and the survey project used Python and Pandas.\\n\\nHere are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:\\n1. Put a short skills-first header or reorder Skills to list SQL, Excel, Tableau, Python (and Pandas) first so ATS and hiring managers immediately see core requirements.\\n2. Expand the Tableau project bullet to highlight scope and outcome using only facts you can support: mention the data source (sales data), the objective (customer retention trends), the dashboard type (interactive), and any improvements to reporting or decision-making if available.\\n3. For the Python/Pandas project, rephrase to clarify your analytical actions and outputs: e.g., \\\"cleaned and analyzed survey data using Python and Pandas and presented insights\\\" — add the specific types of analyses or visualizations you performed if you can support them.\\n4. Add concise examples of SQL-related work (if you performed any): state the kinds of queries or tasks (joins, aggregations, reporting queries) and the context (datasets or reporting) rather than inventing database names.\\n5. Emphasize reporting and business-analysis language from the JD: include the phrases \\\"reporting\\\" and \\\"business analysis\\\" near your Student Assistant bullet and projects to improve ATS alignment (e.g., \\\"prepared weekly reports for academic staff supporting reporting and analysis\\\").\\n6. Quantify workload and cadence where possible using existing facts: keep \\\"weekly reports\\\" but, if true, add number of stakeholders or frequency impact (e.g., supported X academic staff) only if you can verify it.\\n7. Reorder content so that the most relevant project (Tableau dashboard) appears above the Student Assistant entry to foreground visualization and dashboard experience.\\n8. Keep technical tool names exact (SQL, Python, Pandas, Tableau, Excel) to match ATS keyword matching; avoid broad paraphrases that might reduce keyword hits.\\n\\nHere are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:\\n- sql\\n- excel\\n- tableau\\n- python\\n- analytics\\n- data analysis\\n- communication\\n- problem solving\\n- statistics\\n- teamwork\\n- attention to detail\"\n}",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 1382,
                                "prompt_tokens": 1589,
                                "total_tokens": 2971,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 512,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "prompt": """TASK: EMAIL_ANALYZE 
                APPLICATION_ID: 361887fc-844d-4b3c-b10f-331d57fea976 EMAIL: 
                <<< 
                Hi Leen, 

                Thank you for applying to the Data Analyst Intern position. We would like to invite you to a 30-minute HR interview next week. Please reply with your availability for Sunday through Tuesday. 

                Best, 
                Recruiting Team 
                >>>""",
                "full_response": """1) Email Intent:
                Interview invitation

                2) Required Actions:
                - Reply with your availability for Sunday through Tuesday (specific time windows).
                - Ask/confirm the interview time zone and platform (e.g., Zoom, Teams) if not provided.
                - Prepare concise examples from your CV (dashboard project, Python/Pandas data cleaning, reporting experience) to discuss.
                - Be ready for common HR screening questions (growth, motivation, career fit, teamwork).

                3) Here are the next steps:
                - Reply promptly with specific availability windows for Sunday–Tuesday and request the meeting platform and time zone.
                - Be ready to describe your Tableau dashboard (goal, data used, key insight) and your experience using SQL, Excel, and Python to analyze and communicate findings.
                - Use the STAR format (Situation, Task, Action, Result) for behavioral answers; keep each example to ~1–2 minutes.
                - Likely HR questions and brief guidance:
                  - What kind of growth opportunities are you looking for? — Say you aim to grow into a more strategic/senior data role and want opportunities to learn more advanced analytics and mentorship responsibilities.
                  - Why do you want to work at our company? — Briefly state what attracts you (the role’s responsibilities, company mission, or learning opportunities) and tie it to your background and goals.
                  - What skills do you hope to develop in your next role? — Mention strengthening SQL/advanced Excel, dashboarding, and applied business analysis; connect to your projects.
                  - How does this role fit into your career path? — Explain how this internship builds towards your long-term aim of taking on senior analytical responsibilities and mentoring.
                  - What role do you usually play in group settings? — Give a short example showing collaboration, communication, and a positive contribution to team outcomes.

                4) Here is an example reply you can adapt:
                - Hi Recruiting Team,
                  Thank you for the invitation. I’m available for a 30-minute HR interview at the following times (local time):
                  • Sunday: 10:00–12:00
                  • Monday: 14:00–16:00
                  • Tuesday: 09:00–11:00
                  Please let me know which slot works best and which platform/time zone you’ll use. I look forward to speaking with you.
                  Best regards,
                  Leen Khamis""",
                "steps": [
                    {
                        "module": "Planner LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are the Planner LLM.\nTask: extract structured fields from the user's prompt AND propose a short task list.\nReturn ONLY valid JSON with these keys:\n{\n  \"task\": \"RESUME_TAILOR\" | \"EMAIL_ANALYZE\" | \"UNKNOWN\",\n  \"application_id\": string,\n  \"job_title\": string,\n  \"cv_text\": string,\n  \"jd_text\": string,\n  \"email_text\": string,\n  \"task_list\": [string, ...]\n}\nRules:\n- If a field is missing, return an empty string for it.\n- task_list must be 3-7 short items.\n- For RESUME_TAILOR: include in the task_list steps like parsing CV/JD, scoring/matching, ATS-aligned tips, market skills retrieval, and storing APPLICATION_ID.\n- For EMAIL_ANALYZE: task_list should include short steps such as parsing the email, loading application context if APPLICATION_ID exists, identifying the email intent, retrieving relevant HR/technical/rejection-related resources only if needed, and generating next steps plus a suggested reply.\n- Do not include any extra keys or commentary.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK: EMAIL_ANALYZE\nAPPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b\nEMAIL:\n<<<\nHi Leen,\n\nThank you for applying to the Data Analyst Intern position.\nWe would like to invite you to a 30-minute HR interview next week.\nPlease reply with your availability for Sunday through Tuesday.\n\nBest,\nRecruiting Team\n>>>"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHF7c1rd6G3oGKeDWxvxD1E51I7cd",
                            "created": 1773002076,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "{\n  \"task\": \"EMAIL_ANALYZE\",\n  \"application_id\": \"880cc503-e92c-4188-9cf6-6567e1ac4b5b\",\n  \"job_title\": \"Data Analyst Intern\",\n  \"cv_text\": \"\",\n  \"jd_text\": \"\",\n  \"email_text\": \"Hi Leen,\\n\\nThank you for applying to the Data Analyst Intern position.\\nWe would like to invite you to a 30-minute HR interview next week.\\nPlease reply with your availability for Sunday through Tuesday.\\n\\nBest,\\nRecruiting Team\",\n  \"task_list\": [\n    \"Parse the email to extract meeting length, sender, and requested scheduling window\",\n    \"Load application context for APPLICATION_ID 880cc503-e92c-4188-9cf6-6567e1ac4b5b if available\",\n    \"Identify email intent as scheduling a 30-minute HR interview and determine urgency\",\n    \"Retrieve relevant resources only if needed (HR interview tips, common questions, calendar availability formats)\",\n    \"Generate next steps and draft a concise reply offering specific availability and optional timezone preference\"\n  ]\n}",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 569,
                                "prompt_tokens": 327,
                                "total_tokens": 896,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 320,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "module": "Executor LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You analyze recruiter emails within a single job-application context.\nYou will be given JOB_TITLE, CV, JOB_DESCRIPTION, EMAIL, and sometimes extra retrieval blocks.\n\nFirst, detect email_intent as one of: rejection | Interview invitation | Request for info | Follow up | Other.\nThen follow EXACTLY ONE format below.\n\nFORMAT 1 — Non-rejection only:\nUse this format ONLY if email_intent is Interview invitation, Request for info, Follow up, or Other.\nReturn EXACTLY these sections in this EXACT order:\n1) Email Intent:\n\n2) Required Actions:\n   - bullets only\n\n3) Here are the next steps: (bullets; context-aware using JD+CV, but do not invent facts)\n   - Provide bullets.\n\n4) Here is an example reply you can adapt:\n   - short and professional\n   - this is an example reply the user can adapt\n   - Do not include Application ID\n   - must directly address the recruiter’s request when possible\n   - if the recruiter asks for availability, you may include a short illustrative availability reply with plausible sample time slots\nIMPORTANT NOTE: If email_intent is Interview invitation, apply these rules inside next_steps only:\n- Use INTERVIEW_TYPE provided in the prompt (technical | hr | unclear). Do not guess a different type.\n- If INTERVIEW_TYPE is technical and TECH_PREP_LINKS is provided, include those links as bullet points.\n- If INTERVIEW_TYPE is hr and HR_SCREENING_RAG is provided, include 3-5 likely HR questions with brief answer guidance as bullet points.\n- If INTERVIEW_TYPE is unclear, focus first on clarifying the interview format, duration, platform, and expectations; keep any prep advice broad and role-relevant.\nFORMAT 2 — Rejection:\nUse this format ONLY if email_intent is rejection.\nReturn EXACTLY these sections in this EXACT order:\nA) We are sorry to hear that you got rejected.\n\nB) If MARKET_COMMON_SKILLS is provided and MARKET_COMMON_SKILLS.skills_list is non-empty, then output exactly this line:\nConfirm if you have the following commonly requested skills for this role (or consider developing them for future applications):\nC) Only if line B is shown, list the skills as bullets (skill names only).\n   - Use only skill names from MARKET_COMMON_SKILLS.skills_list.\n   - You may include only the skills that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain, and skip unrelated or overly niche items.\n   - Do not add, expand, normalize, or rename skills, and do not claim the candidate lacks them.\n   - If MARKET_COMMON_SKILLS is missing, empty, or skills_list is empty, omit both line B and the skill bullets entirely.\n\nD) Here are the next steps:\n   - Provide bullets.\n\nE) Here is an example reply you can adapt:\n   - Provide the reply text.\n   - Do not include Application ID\nDo NOT output Email Intent, Required Actions, numbering, or any extra label.\n\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK: EMAIL_ANALYZE\nAPPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b\nJOB_TITLE: Data Analyst Intern\nINTERVIEW_TYPE: hr\nCV:\n<<<\nName: Leen Khamis\nEducation: B.Sc. in Data Science and Engineering, Technion\nSkills: Python, SQL, Pandas, Tableau, Excel, Data Visualization\nProjects:\n- Built an interactive Tableau dashboard to analyze customer retention trends from sales data.\n- Used Python and Pandas to clean and analyze survey data and present insights.\nExperience:\n- Student Assistant: prepared weekly reports and summarized data for academic staff.\n>>>\nJOB_DESCRIPTION:\n<<<\nWe are looking for a Data Analyst Intern to support reporting and business analysis.\nRequirements:\n- Strong SQL and Excel skills\n- Experience with dashboards and data visualization\n- Ability to analyze datasets and communicate findings clearly\n- Familiarity with Python is an advantage\n>>>\nEMAIL:\n<<<\nHi Leen,\n\nThank you for applying to the Data Analyst Intern position.\nWe would like to invite you to a 30-minute HR interview next week.\nPlease reply with your availability for Sunday through Tuesday.\n\nBest,\nRecruiting Team\n>>>\n\nHR_SCREENING_RAG:\n- Q: What kind of growth opportunities are you looking for?\n  Guidance: My long-term goal is to grow into a senior role where I can contribute more strategically and mentor others. This role brings me closer to that. What kind of growth opportunities are you looking for?\n- Q: Why do you want to work at our company?\n  Guidance: I'm motivated by challenges and the opportunity to grow both personally and professionally. Why do you want to work at our company?\n- Q: What skills do you hope to develop in your next role?\n  Guidance: My long-term goal is to grow into a senior role where I can contribute more strategically and mentor others. This role brings me closer to that. What skills do you hope to develop in your next role?\n- Q: How does this role fit into your career path?\n  Guidance: My long-term goal is to grow into a senior role where I can contribute more strategically and mentor others. This role brings me closer to that. How does this role fit into your career path?\n- Q: What role do you usually play in group settings?\n  Guidance: I believe communication and mutual respect are key to successful collaboration. In one project, we achieved X because of great teamwork. What role do you usually play in group settings?\n"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHF7mMGVX0QiCUMDZP6ujetnWrLr0",
                            "created": 1773002086,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "1) Email Intent:\nInterview invitation\n\n2) Required Actions:\n- Reply with your availability for Sunday through Tuesday (specific time windows).\n- Ask/confirm the interview time zone and platform (e.g., Zoom, Teams) if not provided.\n- Prepare concise examples from your CV (dashboard project, Python/Pandas data cleaning, reporting experience) to discuss.\n- Be ready for common HR screening questions (growth, motivation, career fit, teamwork).\n\n3) Here are the next steps:\n- Reply promptly with specific availability windows for Sunday–Tuesday and request the meeting platform and time zone.\n- Be ready to describe your Tableau dashboard (goal, data used, key insight) and your experience using SQL, Excel, and Python to analyze and communicate findings.\n- Use the STAR format (Situation, Task, Action, Result) for behavioral answers; keep each example to ~1–2 minutes.\n- Likely HR questions and brief guidance:\n  - What kind of growth opportunities are you looking for? — Say you aim to grow into a more strategic/senior data role and want opportunities to learn more advanced analytics and mentorship responsibilities.\n  - Why do you want to work at our company? — Briefly state what attracts you (the role’s responsibilities, company mission, or learning opportunities) and tie it to your background and goals.\n  - What skills do you hope to develop in your next role? — Mention strengthening SQL/advanced Excel, dashboarding, and applied business analysis; connect to your projects.\n  - How does this role fit into your career path? — Explain how this internship builds towards your long-term aim of taking on senior analytical responsibilities and mentoring.\n  - What role do you usually play in group settings? — Give a short example showing collaboration, communication, and a positive contribution to team outcomes.\n\n4) Here is an example reply you can adapt:\n- Hi Recruiting Team,\n  Thank you for the invitation. I’m available for a 30-minute HR interview at the following times (local time):\n  • Sunday: 10:00–12:00\n  • Monday: 14:00–16:00\n  • Tuesday: 09:00–11:00\n  Please let me know which slot works best and which platform/time zone you’ll use. I look forward to speaking with you.\n  Best regards,\n  Leen Khamis",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 1516,
                                "prompt_tokens": 1136,
                                "total_tokens": 2652,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 1024,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 1024
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "module": "Replan LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are the Replan LLM.\nDecide whether the email-analysis draft can be finalized or must be revised.\nReturn ONLY valid JSON with these keys:\n{\n  \"is_solved\": true|false,\n  \"needs_reflect\": true|false,\n  \"rationale\": string,\n  \"preserve\": [string, ...],\n  \"executor_instructions\": string,\n  \"final_response\": string\n}\n\nCheck the draft against EXACTLY ONE expected format.\n\nFORMAT 1 — Non-rejection:\nRequired sections in this EXACT order:\n1) Email Intent\n2) Required Actions\n3) Here are the next steps:\n4) Here is an example reply you can adapt:\nRules:\n- Email Intent must indicate one of: Interview invitation | Request for info | Follow up | Other.\n- If and ONLY if Email Intent is exactly 'Interview invitation':\n  - Use INTERVIEW_TYPE from CONTEXT_HINT.\n  - If INTERVIEW_TYPE is technical AND CONTEXT_HINT has HAS_TECH_PREP_LINKS: True, then Here are the next steps: MUST include the URLs listed in TECH_PREP_LINKS_BLOCK as bullet items.\n  - If any URL from TECH_PREP_LINKS_BLOCK is missing from next steps, set is_solved=false.\n  - If INTERVIEW_TYPE is hr AND CONTEXT_HINT has HAS_HR_SCREENING_RAG: True, then Here are the next steps: MUST include 3–5 likely HR questions with brief answer-structure guidance.\n  - If INTERVIEW_TYPE is unclear, next steps must prioritize clarifying interview format/platform/duration before specific prep.\n- If Email Intent is 'Request for info', 'Follow up', or 'Other', DO NOT apply any Interview invitation rules.\n- In particular, for 'Request for info', do NOT require clarifying interview format/platform/duration unless the recruiter email explicitly mentions an interview.\n- Here are the next steps: should contain bullets.\n- Here is an example reply you can adapt: should be short and professional.\n- Ignore minor punctuation/numbering differences in labels.\n- No extra top-level sections or closing remarks.\n\nFORMAT 2 — Rejection:\nUse only when the draft is a rejection-format draft.\nRequired sections in this order:\n1) We are sorry to hear that you got rejected.\n2) Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications):\n3) skill bullets only\n4) Here are the next steps:\n5) next-step bullets\n6) Here is an example reply you can adapt:\n7) reply text\nRules:\n- Show both Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications): and the skill-bullets section ONLY if MARKET_COMMON_SKILLS.skills_list exists and is non-empty.\n- If MARKET_COMMON_SKILLS.skills_list is missing or empty, omit both Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications): and the skill bullets, and continue directly with Here are the next steps:.\n- If Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications): appears, it must be followed only by skill bullets from MARKET_COMMON_SKILLS.skills_list.\n- The list may include only skills that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain, and skip unrelated or overly niche items.\n- Do not add, rename, expand, or normalize skills.\n- Do not add extra prose before, between, or after these parts.\n\nDecision rules:\n- Use CONTEXT_HINT to know which format is expected.\n- Judge rejection drafts by FORMAT B.\n- Judge all other drafts by FORMAT A.\n- Apply interview-specific validation ONLY when the draft's Email Intent is exactly 'Interview invitation'.\n- If CONTEXT_HINT includes SUGGESTED_REPLY_IS_EXAMPLE: True, treat suggested_reply as an illustrative sample. Do not mark plausible sample availability slots, dates, greetings, or signatures as hallucinations if they are clearly presented as example content rather than user facts.\n- Treat details as grounded if they are supported by the provided CV, JOB_DESCRIPTION, EMAIL, or CONTEXT_HINT; do not mark them as hallucinations merely because they are absent from the email text alone.\n- If the draft satisfies the expected format and has no clear hallucination or contradiction, set is_solved=true.\nOutput rules:\n- If is_solved=true: final_response must contain the final answer, needs_reflect must be false, and executor_instructions must be empty.\n- If is_solved=false: final_response must be empty.\n- If REFLECTION_JSON is provided: set needs_reflect=false, convert must_fix into ordered executor_instructions, and include up to 5 preserve items from pros.\n- No extra keys, no markdown, no commentary outside the JSON.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK_KIND: EMAIL_ANALYZE\nCONTEXT_HINT:\n<<<\nAPPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b\nJOB_TITLE: Data Analyst Intern\nINTERVIEW_TYPE: hr\nHAS_TECH_PREP_LINKS: False\nHAS_HR_SCREENING_RAG: True\nTECH_PREP_LINKS_BLOCK:\n\nCV_SNIPPET: Name: Leen Khamis Education: B.Sc. in Data Science and Engineering, Technion Skills: Python, SQL, Pandas, Tableau, Excel, Data Visualization Projects: - Built an interactive Tableau dashboard to analyze customer retention trends from sales data. - Used Python and Pandas to clean and analyze survey data and present insights. Experience: - Student Assistant: prepared weekly reports and summarized data for academic staff.\nJD_SNIPPET: We are looking for a Data Analyst Intern to support reporting and business analysis. Requirements: - Strong SQL and Excel skills - Experience with dashboards and data visualization - Ability to analyze datasets and communicate findings clearly - Familiarity with Python is an advantage\nEMAIL_SNIPPET: Hi Leen, Thank you for applying to the Data Analyst Intern position. We would like to invite you to a 30-minute HR interview next week. Please reply with your availability for Sunday through Tuesday. Best, Recruiting Team\nEXPECT_REJECTION_SPECIAL: False\nSUGGESTED_REPLY_IS_EXAMPLE: True\n\n>>>\nDRAFT_RESPONSE:\n<<<\n1) Email Intent:\nInterview invitation\n\n2) Required Actions:\n- Reply with your availability for Sunday through Tuesday (specific time windows).\n- Ask/confirm the interview time zone and platform (e.g., Zoom, Teams) if not provided.\n- Prepare concise examples from your CV (dashboard project, Python/Pandas data cleaning, reporting experience) to discuss.\n- Be ready for common HR screening questions (growth, motivation, career fit, teamwork).\n\n3) Here are the next steps:\n- Reply promptly with specific availability windows for Sunday–Tuesday and request the meeting platform and time zone.\n- Be ready to describe your Tableau dashboard (goal, data used, key insight) and your experience using SQL, Excel, and Python to analyze and communicate findings.\n- Use the STAR format (Situation, Task, Action, Result) for behavioral answers; keep each example to ~1–2 minutes.\n- Likely HR questions and brief guidance:\n  - What kind of growth opportunities are you looking for? — Say you aim to grow into a more strategic/senior data role and want opportunities to learn more advanced analytics and mentorship responsibilities.\n  - Why do you want to work at our company? — Briefly state what attracts you (the role’s responsibilities, company mission, or learning opportunities) and tie it to your background and goals.\n  - What skills do you hope to develop in your next role? — Mention strengthening SQL/advanced Excel, dashboarding, and applied business analysis; connect to your projects.\n  - How does this role fit into your career path? — Explain how this internship builds towards your long-term aim of taking on senior analytical responsibilities and mentoring.\n  - What role do you usually play in group settings? — Give a short example showing collaboration, communication, and a positive contribution to team outcomes.\n\n4) Here is an example reply you can adapt:\n- Hi Recruiting Team,\n  Thank you for the invitation. I’m available for a 30-minute HR interview at the following times (local time):\n  • Sunday: 10:00–12:00\n  • Monday: 14:00–16:00\n  • Tuesday: 09:00–11:00\n  Please let me know which slot works best and which platform/time zone you’ll use. I look forward to speaking with you.\n  Best regards,\n  Leen Khamis\n>>>\n"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHF7yRh70lf9f2rkzEcMj8wL5lOyM",
                            "created": 1773002098,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "{\n  \"is_solved\": true,\n  \"needs_reflect\": false,\n  \"rationale\": \"The draft follows FORMAT 1 in the exact required order, labels 'Interview invitation' correctly, and uses INTERVIEW_TYPE (HR) to include 3–5 likely HR questions with brief answer-structure guidance as required. Bulleted next steps are present, the example reply is short and professional, and there are no extra top-level sections or contradictions with the provided context.\",\n  \"preserve\": [\n    \"Reply with your availability for Sunday through Tuesday (specific time windows).\",\n    \"Ask/confirm the interview time zone and platform (e.g., Zoom, Teams) if not provided.\",\n    \"Prepare concise examples from your CV (dashboard project, Python/Pandas data cleaning, reporting experience) to discuss.\",\n    \"Be ready for common HR screening questions (growth, motivation, career fit, teamwork).\",\n    \"Example reply with specific availability slots and request for platform/time zone.\"\n  ],\n  \"executor_instructions\": \"\",\n  \"final_response\": \"1) Email Intent:\\nInterview invitation\\n\\n2) Required Actions:\\n- Reply with your availability for Sunday through Tuesday (specific time windows).\\n- Ask/confirm the interview time zone and platform (e.g., Zoom, Teams) if not provided.\\n- Prepare concise examples from your CV (dashboard project, Python/Pandas data cleaning, reporting experience) to discuss.\\n- Be ready for common HR screening questions (growth, motivation, career fit, teamwork).\\n\\n3) Here are the next steps:\\n- Reply promptly with specific availability windows for Sunday–Tuesday and request the meeting platform and time zone.\\n- Be ready to describe your Tableau dashboard (goal, data used, key insight) and your experience using SQL, Excel, and Python to analyze and communicate findings.\\n- Use the STAR format (Situation, Task, Action, Result) for behavioral answers; keep each example to ~1–2 minutes.\\n- Likely HR questions and brief guidance:\\n  - What kind of growth opportunities are you looking for? — Say you aim to grow into a more strategic/senior data role and want opportunities to learn more advanced analytics and mentorship responsibilities.\\n  - Why do you want to work at our company? — Briefly state what attracts you (the role’s responsibilities, company mission, or learning opportunities) and tie it to your background and goals.\\n  - What skills do you hope to develop in your next role? — Mention strengthening SQL/advanced Excel, dashboarding, and applied business analysis; connect to your projects.\\n  - How does this role fit into your career path? — Explain how this internship builds towards your long-term aim of taking on senior analytical responsibilities and mentoring.\\n  - What role do you usually play in group settings? — Give a short example showing collaboration, communication, and a positive contribution to team outcomes.\\n\\n4) Here is an example reply you can adapt:\\n- Hi Recruiting Team,\\n  Thank you for the invitation. I’m available for a 30-minute HR interview at the following times (local time):\\n  • Sunday: 10:00–12:00\\n  • Monday: 14:00–16:00\\n  • Tuesday: 09:00–11:00\\n  Please let me know which slot works best and which platform/time zone you’ll use. I look forward to speaking with you.\\n  Best regards,\\n  Leen Khamis\"\n}",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 1888,
                                "prompt_tokens": 1780,
                                "total_tokens": 3668,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 1152,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "prompt": """TASK: EMAIL_ANALYZE
            APPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b
            EMAIL:
            <<<
            Subject: Technical Interview Invitation

            Hi Leen,

            Thank you for applying to the Data Analyst Student role. We would like to invite you to a technical interview next week.
            Please send your availability by Friday.
            The interview will include SQL and Python questions.

            Best,
            Recruiting Team
            >>>""",
                "full_response": """1) Email Intent:
            Interview invitation

            2) Required Actions:
               - Reply with your availability by Friday (give several time slots across different days).
               - Ask/confirm interview logistics: remote or in-person, platform (Zoom/Teams), expected duration, and any materials or screen-sharing requirements.
               - Prepare for SQL and Python technical questions and have examples from your CV/projects ready to discuss.
               - Review key SQL, Python (pandas), and Excel topics relevant to the role.

            3) Here are the next steps:
               - Prioritize SQL practice: joins, aggregations, GROUP BY, window functions, subqueries, and writing correct, efficient queries on sample datasets.
               - Review Python/pandas tasks: data cleaning, merging, groupby/aggregation, reshaping data, and common functions you used in your projects.
               - Rehearse explaining your Tableau dashboard project and the survey data analysis: objective, data sources, cleaning steps, key findings, and how your work impacted decisions.
               - Refresh Excel skills the JD emphasizes: pivot tables, lookup functions, basic formulas and data summarization (these may be discussed even in a technical interview).
               - Use the provided prep resources for hands-on practice:
                 - https://datalemur.com/
                 - https://www.interviewquery.com/
                 - https://www.coursera.org/articles/data-analytics-interview-questions
               - Prepare 2–3 concise stories from your Student Assistant and projects that show problem, approach, tools (SQL/Python/Tableau/Excel), and results.
               - If you don’t know the interview length or platform yet, ask when you reply and request any sample formats (coding test, live whiteboard, take-home) so you can prepare accordingly.

            4) Here is an example reply you can adapt:
               - Hi Recruiting Team,
                 Thank you for the invitation — I’m excited to interview for the Data Analyst Student role. I’m available next week at the following times:
                 - Monday 9:00–11:00 AM
                 - Wednesday 2:00–4:00 PM
                 - Friday 10:00–12:00 PM
                 If none of these work, I can be flexible — please let me know your preferred time. Could you also confirm whether the interview will be remote or in-person, the expected duration, and which platform you’ll use? I’ll prepare for SQL and Python technical questions and can share examples from my Tableau and pandas projects during the interview.
                 Best regards,
                 Leen Khamis""",
                "steps": [
                    {
                        "module": "Planner LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are the Planner LLM.\nTask: extract structured fields from the user's prompt AND propose a short task list.\nReturn ONLY valid JSON with these keys:\n{\n  \"task\": \"RESUME_TAILOR\" | \"EMAIL_ANALYZE\" | \"UNKNOWN\",\n  \"application_id\": string,\n  \"job_title\": string,\n  \"cv_text\": string,\n  \"jd_text\": string,\n  \"email_text\": string,\n  \"task_list\": [string, ...]\n}\nRules:\n- If a field is missing, return an empty string for it.\n- task_list must be 3-7 short items.\n- For RESUME_TAILOR: include in the task_list steps like parsing CV/JD, scoring/matching, ATS-aligned tips, market skills retrieval, and storing APPLICATION_ID.\n- For EMAIL_ANALYZE: task_list should include short steps such as parsing the email, loading application context if APPLICATION_ID exists, identifying the email intent, retrieving relevant HR/technical/rejection-related resources only if needed, and generating next steps plus a suggested reply.\n- Do not include any extra keys or commentary.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK: EMAIL_ANALYZE\nAPPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b\nEMAIL:\n<<<\nSubject: Technical Interview Invitation\n\nHi Leen,\n\nThank you for applying to the Data Analyst Student role. We would like to invite you to a technical interview next week.\nPlease send your availability by Friday.\nThe interview will include SQL and Python questions.\n\nBest,\nRecruiting Team\n>>>"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHFDHw4FGZayC3v27FFXGoH8ZI4lZ",
                            "created": 1773002427,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "{\n  \"task\": \"EMAIL_ANALYZE\",\n  \"application_id\": \"880cc503-e92c-4188-9cf6-6567e1ac4b5b\",\n  \"job_title\": \"Data Analyst Student\",\n  \"cv_text\": \"\",\n  \"jd_text\": \"\",\n  \"email_text\": \"Subject: Technical Interview Invitation\\n\\nHi Leen,\\n\\nThank you for applying to the Data Analyst Student role. We would like to invite you to a technical interview next week.\\nPlease send your availability by Friday.\\nThe interview will include SQL and Python questions.\\n\\nBest,\\nRecruiting Team\",\n  \"task_list\": [\n    \"Parse the email: extract sender, subject, deadline (by Friday), interview topics (SQL, Python) and requested action (send availability).\",\n    \"Load application context using APPLICATION_ID 880cc503-e92c-4188-9cf6-6567e1ac4b5b to retrieve candidate/job history if available.\",\n    \"Identify email intent: technical interview invitation and request for availability confirmation.\",\n    \"Retrieve relevant resources only if needed: scheduling/HR guidelines and technical prep materials for SQL and Python interview questions.\",\n    \"Generate next steps and a suggested reply: propose availability options, confirm interview duration/format, ask any clarifying logistics, and provide brief preparation notes.\"\n  ]\n}",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 678,
                                "prompt_tokens": 336,
                                "total_tokens": 1014,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 384,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "module": "Executor LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You analyze recruiter emails within a single job-application context.\nYou will be given JOB_TITLE, CV, JOB_DESCRIPTION, EMAIL, and sometimes extra retrieval blocks.\n\nFirst, detect email_intent as one of: rejection | Interview invitation | Request for info | Follow up | Other.\nThen follow EXACTLY ONE format below.\n\nFORMAT 1 — Non-rejection only:\nUse this format ONLY if email_intent is Interview invitation, Request for info, Follow up, or Other.\nReturn EXACTLY these sections in this EXACT order:\n1) Email Intent:\n\n2) Required Actions:\n   - bullets only\n\n3) Here are the next steps: (bullets; context-aware using JD+CV, but do not invent facts)\n   - Provide bullets.\n\n4) Here is an example reply you can adapt:\n   - short and professional\n   - this is an example reply the user can adapt\n   - Do not include Application ID\n   - must directly address the recruiter’s request when possible\n   - if the recruiter asks for availability, you may include a short illustrative availability reply with plausible sample time slots\nIMPORTANT NOTE: If email_intent is Interview invitation, apply these rules inside next_steps only:\n- Use INTERVIEW_TYPE provided in the prompt (technical | hr | unclear). Do not guess a different type.\n- If INTERVIEW_TYPE is technical and TECH_PREP_LINKS is provided, include those links as bullet points.\n- If INTERVIEW_TYPE is hr and HR_SCREENING_RAG is provided, include 3-5 likely HR questions with brief answer guidance as bullet points.\n- If INTERVIEW_TYPE is unclear, focus first on clarifying the interview format, duration, platform, and expectations; keep any prep advice broad and role-relevant.\nFORMAT 2 — Rejection:\nUse this format ONLY if email_intent is rejection.\nReturn EXACTLY these sections in this EXACT order:\nA) We are sorry to hear that you got rejected.\n\nB) If MARKET_COMMON_SKILLS is provided and MARKET_COMMON_SKILLS.skills_list is non-empty, then output exactly this line:\nConfirm if you have the following commonly requested skills for this role (or consider developing them for future applications):\nC) Only if line B is shown, list the skills as bullets (skill names only).\n   - Use only skill names from MARKET_COMMON_SKILLS.skills_list.\n   - You may include only the skills that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain, and skip unrelated or overly niche items.\n   - Do not add, expand, normalize, or rename skills, and do not claim the candidate lacks them.\n   - If MARKET_COMMON_SKILLS is missing, empty, or skills_list is empty, omit both line B and the skill bullets entirely.\n\nD) Here are the next steps:\n   - Provide bullets.\n\nE) Here is an example reply you can adapt:\n   - Provide the reply text.\n   - Do not include Application ID\nDo NOT output Email Intent, Required Actions, numbering, or any extra label.\n\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK: EMAIL_ANALYZE\nAPPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b\nJOB_TITLE: Data Analyst Student\nINTERVIEW_TYPE: technical\nCV:\n<<<\nName: Leen Khamis\nEducation: B.Sc. in Data Science and Engineering, Technion\nSkills: Python, SQL, Pandas, Tableau, Excel, Data Visualization\nProjects:\n- Built an interactive Tableau dashboard to analyze customer retention trends from sales data.\n- Used Python and Pandas to clean and analyze survey data and present insights.\nExperience:\n- Student Assistant: prepared weekly reports and summarized data for academic staff.\n>>>\nJOB_DESCRIPTION:\n<<<\nWe are looking for a Data Analyst Intern to support reporting and business analysis.\nRequirements:\n- Strong SQL and Excel skills\n- Experience with dashboards and data visualization\n- Ability to analyze datasets and communicate findings clearly\n- Familiarity with Python is an advantage\n>>>\nEMAIL:\n<<<\nSubject: Technical Interview Invitation\n\nHi Leen,\n\nThank you for applying to the Data Analyst Student role. We would like to invite you to a technical interview next week.\nPlease send your availability by Friday.\nThe interview will include SQL and Python questions.\n\nBest,\nRecruiting Team\n>>>\n\nTECH_PREP_LINKS:\n- https://datalemur.com/\n- https://www.interviewquery.com/\n- https://www.coursera.org/articles/data-analytics-interview-questions\n"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHFDRh2TRJMBaknnyAcq8G3ptpMGq",
                            "created": 1773002437,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "1) Email Intent:\nInterview invitation\n\n2) Required Actions:\n   - Reply with your availability by Friday (give several time slots across different days).\n   - Ask/confirm interview logistics: remote or in-person, platform (Zoom/Teams), expected duration, and any materials or screen-sharing requirements.\n   - Prepare for SQL and Python technical questions and have examples from your CV/projects ready to discuss.\n   - Review key SQL, Python (pandas), and Excel topics relevant to the role.\n\n3) Here are the next steps:\n   - Prioritize SQL practice: joins, aggregations, GROUP BY, window functions, subqueries, and writing correct, efficient queries on sample datasets.\n   - Review Python/pandas tasks: data cleaning, merging, groupby/aggregation, reshaping data, and common functions you used in your projects.\n   - Rehearse explaining your Tableau dashboard project and the survey data analysis: objective, data sources, cleaning steps, key findings, and how your work impacted decisions.\n   - Refresh Excel skills the JD emphasizes: pivot tables, lookup functions, basic formulas and data summarization (these may be discussed even in a technical interview).\n   - Use the provided prep resources for hands-on practice:\n     - https://datalemur.com/\n     - https://www.interviewquery.com/\n     - https://www.coursera.org/articles/data-analytics-interview-questions\n   - Prepare 2–3 concise stories from your Student Assistant and projects that show problem, approach, tools (SQL/Python/Tableau/Excel), and results.\n   - If you don’t know the interview length or platform yet, ask when you reply and request any sample formats (coding test, live whiteboard, take-home) so you can prepare accordingly.\n\n4) Here is an example reply you can adapt:\n   - Hi Recruiting Team,\n     Thank you for the invitation — I’m excited to interview for the Data Analyst Student role. I’m available next week at the following times:\n     - Monday 9:00–11:00 AM\n     - Wednesday 2:00–4:00 PM\n     - Friday 10:00–12:00 PM\n     If none of these work, I can be flexible — please let me know your preferred time. Could you also confirm whether the interview will be remote or in-person, the expected duration, and which platform you’ll use? I’ll prepare for SQL and Python technical questions and can share examples from my Tableau and pandas projects during the interview.\n     Best regards,\n     Leen Khamis",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_results": {
                                            "hate": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "protected_material_code": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "protected_material_text": {
                                                "filtered": False,
                                                "detected": False
                                            },
                                            "self_harm": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "sexual": {
                                                "filtered": False,
                                                "severity": "safe"
                                            },
                                            "violence": {
                                                "filtered": False,
                                                "severity": "safe"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 1620,
                                "prompt_tokens": 921,
                                "total_tokens": 2541,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 1088,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 0
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "module": "Replan LLM",
                        "prompt": {
                            "model": "RPRTHPB-gpt-5-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are the Replan LLM.\nDecide whether the email-analysis draft can be finalized or must be revised.\nReturn ONLY valid JSON with these keys:\n{\n  \"is_solved\": true|false,\n  \"needs_reflect\": true|false,\n  \"rationale\": string,\n  \"preserve\": [string, ...],\n  \"executor_instructions\": string,\n  \"final_response\": string\n}\n\nCheck the draft against EXACTLY ONE expected format.\n\nFORMAT 1 — Non-rejection:\nRequired sections in this EXACT order:\n1) Email Intent\n2) Required Actions\n3) Here are the next steps:\n4) Here is an example reply you can adapt:\nRules:\n- Email Intent must indicate one of: Interview invitation | Request for info | Follow up | Other.\n- If and ONLY if Email Intent is exactly 'Interview invitation':\n  - Use INTERVIEW_TYPE from CONTEXT_HINT.\n  - If INTERVIEW_TYPE is technical AND CONTEXT_HINT has HAS_TECH_PREP_LINKS: True, then Here are the next steps: MUST include the URLs listed in TECH_PREP_LINKS_BLOCK as bullet items.\n  - If any URL from TECH_PREP_LINKS_BLOCK is missing from next steps, set is_solved=false.\n  - If INTERVIEW_TYPE is hr AND CONTEXT_HINT has HAS_HR_SCREENING_RAG: True, then Here are the next steps: MUST include 3–5 likely HR questions with brief answer-structure guidance.\n  - If INTERVIEW_TYPE is unclear, next steps must prioritize clarifying interview format/platform/duration before specific prep.\n- If Email Intent is 'Request for info', 'Follow up', or 'Other', DO NOT apply any Interview invitation rules.\n- In particular, for 'Request for info', do NOT require clarifying interview format/platform/duration unless the recruiter email explicitly mentions an interview.\n- Here are the next steps: should contain bullets.\n- Here is an example reply you can adapt: should be short and professional.\n- Ignore minor punctuation/numbering differences in labels.\n- No extra top-level sections or closing remarks.\n\nFORMAT 2 — Rejection:\nUse only when the draft is a rejection-format draft.\nRequired sections in this order:\n1) We are sorry to hear that you got rejected.\n2) Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications):\n3) skill bullets only\n4) Here are the next steps:\n5) next-step bullets\n6) Here is an example reply you can adapt:\n7) reply text\nRules:\n- Show both Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications): and the skill-bullets section ONLY if MARKET_COMMON_SKILLS.skills_list exists and is non-empty.\n- If MARKET_COMMON_SKILLS.skills_list is missing or empty, omit both Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications): and the skill bullets, and continue directly with Here are the next steps:.\n- If Confirm if you have the following commonly requested skills for this role (or consider developing them for future applications): appears, it must be followed only by skill bullets from MARKET_COMMON_SKILLS.skills_list.\n- The list may include only skills that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain, and skip unrelated or overly niche items.\n- Do not add, rename, expand, or normalize skills.\n- Do not add extra prose before, between, or after these parts.\n\nDecision rules:\n- Use CONTEXT_HINT to know which format is expected.\n- Judge rejection drafts by FORMAT B.\n- Judge all other drafts by FORMAT A.\n- Apply interview-specific validation ONLY when the draft's Email Intent is exactly 'Interview invitation'.\n- If CONTEXT_HINT includes SUGGESTED_REPLY_IS_EXAMPLE: True, treat suggested_reply as an illustrative sample. Do not mark plausible sample availability slots, dates, greetings, or signatures as hallucinations if they are clearly presented as example content rather than user facts.\n- Treat details as grounded if they are supported by the provided CV, JOB_DESCRIPTION, EMAIL, or CONTEXT_HINT; do not mark them as hallucinations merely because they are absent from the email text alone.\n- If the draft satisfies the expected format and has no clear hallucination or contradiction, set is_solved=true.\nOutput rules:\n- If is_solved=true: final_response must contain the final answer, needs_reflect must be false, and executor_instructions must be empty.\n- If is_solved=false: final_response must be empty.\n- If REFLECTION_JSON is provided: set needs_reflect=false, convert must_fix into ordered executor_instructions, and include up to 5 preserve items from pros.\n- No extra keys, no markdown, no commentary outside the JSON.\n"
                                },
                                {
                                    "role": "user",
                                    "content": "TASK_KIND: EMAIL_ANALYZE\nCONTEXT_HINT:\n<<<\nAPPLICATION_ID: 880cc503-e92c-4188-9cf6-6567e1ac4b5b\nJOB_TITLE: Data Analyst Student\nINTERVIEW_TYPE: technical\nHAS_TECH_PREP_LINKS: True\nHAS_HR_SCREENING_RAG: False\nTECH_PREP_LINKS_BLOCK:\nTECH_PREP_LINKS:\n- https://datalemur.com/\n- https://www.interviewquery.com/\n- https://www.coursera.org/articles/data-analytics-interview-questions\nCV_SNIPPET: Name: Leen Khamis Education: B.Sc. in Data Science and Engineering, Technion Skills: Python, SQL, Pandas, Tableau, Excel, Data Visualization Projects: - Built an interactive Tableau dashboard to analyze customer retention trends from sales data. - Used Python and Pandas to clean and analyze survey data and present insights. Experience: - Student Assistant: prepared weekly reports and summarized data for academic staff.\nJD_SNIPPET: We are looking for a Data Analyst Intern to support reporting and business analysis. Requirements: - Strong SQL and Excel skills - Experience with dashboards and data visualization - Ability to analyze datasets and communicate findings clearly - Familiarity with Python is an advantage\nEMAIL_SNIPPET: Subject: Technical Interview Invitation Hi Leen, Thank you for applying to the Data Analyst Student role. We would like to invite you to a technical interview next week. Please send your availability by Friday. The interview will include SQL and Python questions. Best, Recruiting Team\nEXPECT_REJECTION_SPECIAL: False\nSUGGESTED_REPLY_IS_EXAMPLE: True\n\n>>>\nDRAFT_RESPONSE:\n<<<\n1) Email Intent:\nInterview invitation\n\n2) Required Actions:\n   - Reply with your availability by Friday (give several time slots across different days).\n   - Ask/confirm interview logistics: remote or in-person, platform (Zoom/Teams), expected duration, and any materials or screen-sharing requirements.\n   - Prepare for SQL and Python technical questions and have examples from your CV/projects ready to discuss.\n   - Review key SQL, Python (pandas), and Excel topics relevant to the role.\n\n3) Here are the next steps:\n   - Prioritize SQL practice: joins, aggregations, GROUP BY, window functions, subqueries, and writing correct, efficient queries on sample datasets.\n   - Review Python/pandas tasks: data cleaning, merging, groupby/aggregation, reshaping data, and common functions you used in your projects.\n   - Rehearse explaining your Tableau dashboard project and the survey data analysis: objective, data sources, cleaning steps, key findings, and how your work impacted decisions.\n   - Refresh Excel skills the JD emphasizes: pivot tables, lookup functions, basic formulas and data summarization (these may be discussed even in a technical interview).\n   - Use the provided prep resources for hands-on practice:\n     - https://datalemur.com/\n     - https://www.interviewquery.com/\n     - https://www.coursera.org/articles/data-analytics-interview-questions\n   - Prepare 2–3 concise stories from your Student Assistant and projects that show problem, approach, tools (SQL/Python/Tableau/Excel), and results.\n   - If you don’t know the interview length or platform yet, ask when you reply and request any sample formats (coding test, live whiteboard, take-home) so you can prepare accordingly.\n\n4) Here is an example reply you can adapt:\n   - Hi Recruiting Team,\n     Thank you for the invitation — I’m excited to interview for the Data Analyst Student role. I’m available next week at the following times:\n     - Monday 9:00–11:00 AM\n     - Wednesday 2:00–4:00 PM\n     - Friday 10:00–12:00 PM\n     If none of these work, I can be flexible — please let me know your preferred time. Could you also confirm whether the interview will be remote or in-person, the expected duration, and which platform you’ll use? I’ll prepare for SQL and Python technical questions and can share examples from my Tableau and pandas projects during the interview.\n     Best regards,\n     Leen Khamis\n>>>\n"
                                }
                            ]
                        },
                        "response": {
                            "id": "chatcmpl-DHFDeihHC5IZjPCBaWvHR3kgehT1v",
                            "created": 1773002450,
                            "model": "gpt-5-mini-2025-08-07",
                            "object": "chat.completion",
                            "choices": [
                                {
                                    "finish_reason": "stop",
                                    "index": 0,
                                    "message": {
                                        "content": "{\n  \"is_solved\": true,\n  \"needs_reflect\": false,\n  \"rationale\": \"The draft matches FORMAT 1 exactly: it contains the required four sections in the correct order, the Email Intent is 'Interview invitation' and INTERVIEW_TYPE is technical with HAS_TECH_PREP_LINKS True, and the 'Here are the next steps:' section includes all three TECH_PREP_LINKS as bullet items. The required actions and example reply are appropriate and grounded in the provided email, CV, and job description.\",\n  \"preserve\": [\n    \"Email Intent: Interview invitation\",\n    \"Reply with your availability by Friday (give several time slots across different days).\",\n    \"Ask/confirm interview logistics: remote or in-person, platform (Zoom/Teams), expected duration, and any materials or screen-sharing requirements.\",\n    \"Use the provided prep resources for hands-on practice: https://datalemur.com/ https://www.interviewquery.com/ https://www.coursera.org/articles/data-analytics-interview-questions\",\n    \"Example reply starting: Hi Recruiting Team, Thank you for the invitation — I’m excited to interview for the Data Analyst Student role.\"\n  ],\n  \"executor_instructions\": \"\",\n  \"final_response\": \"1) Email Intent:\\nInterview invitation\\n\\n2) Required Actions:\\n   - Reply with your availability by Friday (give several time slots across different days).\\n   - Ask/confirm interview logistics: remote or in-person, platform (Zoom/Teams), expected duration, and any materials or screen-sharing requirements.\\n   - Prepare for SQL and Python technical questions and have examples from your CV/projects ready to discuss.\\n   - Review key SQL, Python (pandas), and Excel topics relevant to the role.\\n\\n3) Here are the next steps:\\n   - Prioritize SQL practice: joins, aggregations, GROUP BY, window functions, subqueries, and writing correct, efficient queries on sample datasets.\\n   - Review Python/pandas tasks: data cleaning, merging, groupby/aggregation, reshaping data, and common functions you used in your projects.\\n   - Rehearse explaining your Tableau dashboard project and the survey data analysis: objective, data sources, cleaning steps, key findings, and how your work impacted decisions.\\n   - Refresh Excel skills the JD emphasizes: pivot tables, lookup functions, basic formulas and data summarization (these may be discussed even in a technical interview).\\n   - Use the provided prep resources for hands-on practice:\\n     - https://datalemur.com/\\n     - https://www.interviewquery.com/\\n     - https://www.coursera.org/articles/data-analytics-interview-questions\\n   - Prepare 2–3 concise stories from your Student Assistant and projects that show problem, approach, tools (SQL/Python/Tableau/Excel), and results.\\n   - If you don’t know the interview length or platform yet, ask when you reply and request any sample formats (coding test, live whiteboard, take-home) so you can prepare accordingly.\\n\\n4) Here is an example reply you can adapt:\\n   - Hi Recruiting Team,\\n     Thank you for the invitation — I’m excited to interview for the Data Analyst Student role. I’m available next week at the following times:\\n     - Monday 9:00–11:00 AM\\n     - Wednesday 2:00–4:00 PM\\n     - Friday 10:00–12:00 PM\\n     If none of these work, I can be flexible — please let me know your preferred time. Could you also confirm whether the interview will be remote or in-person, the expected duration, and which platform you’ll use? I’ll prepare for SQL and Python technical questions and can share examples from my Tableau and pandas projects during the interview.\\n     Best regards,\\n     Leen Khamis\"\n}",
                                        "role": "assistant"
                                    },
                                    "provider_specific_fields": {
                                        "content_filter_result": {
                                            "error": {
                                                "code": "content_filter_error",
                                                "message": "The contents are not filtered"
                                            }
                                        }
                                    }
                                }
                            ],
                            "usage": {
                                "completion_tokens": 1712,
                                "prompt_tokens": 1869,
                                "total_tokens": 3581,
                                "completion_tokens_details": {
                                    "accepted_prediction_tokens": 0,
                                    "audio_tokens": 0,
                                    "reasoning_tokens": 896,
                                    "rejected_prediction_tokens": 0
                                },
                                "prompt_tokens_details": {
                                    "audio_tokens": 0,
                                    "cached_tokens": 1024
                                }
                            },
                            "prompt_filter_results": [
                                {
                                    "prompt_index": 0,
                                    "content_filter_results": {
                                        "hate": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "jailbreak": {
                                            "filtered": False,
                                            "detected": False
                                        },
                                        "self_harm": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "sexual": {
                                            "filtered": False,
                                            "severity": "safe"
                                        },
                                        "violence": {
                                            "filtered": False,
                                            "severity": "safe"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


BASE_DIR = Path(__file__).resolve().parents[1]


@app.get("/api/model_architecture", response_class=FileResponse)
def model_architecture():
    png_path = BASE_DIR / "static" / "model_architecture.png"
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="model_architecture.png not found in /static")
    return FileResponse(png_path, media_type="image/png")


@app.post("/api/execute")
async def execute(req: ExecuteRequest):
    try:
        if not req.prompt or not req.prompt.strip():
            return {
                "status": "error",
                "error": "Empty prompt. Expected TASK: RESUME_TAILOR with CV and JOB_DESCRIPTION, or TASK: EMAIL_ANALYZE with EMAIL.",
                "response": None,
                "steps": []
            }

        trace = Trace()
        decision = route(req.prompt)

        if decision == "resume":
            text = await resume_flow.run(req.prompt, trace)
            return {"status": "ok", "error": None, "response": text, "steps": trace.steps}

        if decision == "email":
            text = await email_flow.run(req.prompt, trace)
            return {"status": "ok", "error": None, "response": text, "steps": trace.steps}

        return {
            "status": "error",
            "error": (
                "Unsupported or malformed prompt. Expected one of:\n"
                "1) TASK: RESUME_TAILOR with JOB_TITLE, CV, and JOB_DESCRIPTION\n"
                "2) TASK: EMAIL_ANALYZE with EMAIL (APPLICATION_ID optional)"
            ),
            "response": None,
            "steps": []
        }

    except Exception as e:
        return {"status": "error", "error": str(e), "response": None, "steps": []}