"""Benchmark queries with manually identified relevant chunk ids (Phase 5)."""

from __future__ import annotations

from typing import TypedDict


class BenchmarkQuery(TypedDict):
    """One benchmark query with a ground-truth relevant set."""

    query: str
    relevant_chunk_ids: list[str]
    category: str


# Relevant chunk IDs were re-mapped after re-ingestion of both PDFs (April 2026).
# IDs follow the pattern <source_file_without_dot>_<index>.
BENCHMARK: list[BenchmarkQuery] = [
    # GPA / academic standing
    {
        "query": "Under what conditions is an undergraduate student considered academically deficient (probation/warning triggers)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000076",
            "UG_Handbook_pdf_000128",
            "UG_Handbook_pdf_000132",
            "UG_Handbook_pdf_000133",
            "UG_Handbook_pdf_000135",
            "UG_Handbook_pdf_000176",
        ],
        "category": "gpa",
    },
    {
        "query": "How are Semester GPA and CGPA reported/approved in the official results?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000062",
            "UG_Handbook_pdf_000129",
            "PG_Handbook_pdf_000068",
        ],
        "category": "gpa",
    },
    # Attendance / absence
    {
        "query": "What is the policy when a student misses the mid semester examination due to acceptable reasons (make-up timing)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000067",
            "UG_Handbook_pdf_000124",
            "UG_Handbook_pdf_000164",
            "PG_Handbook_pdf_000062",
            "PG_Handbook_pdf_000116",
        ],
        "category": "attendance",
    },
    {
        "query": "What is the policy when a student misses the end semester examination due to acceptable reasons (make-up timing/limits)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000067",
            "UG_Handbook_pdf_000125",
            "UG_Handbook_pdf_000166",
            "PG_Handbook_pdf_000062",
        ],
        "category": "attendance",
    },
    # Course repetition
    {
        "query": "Can a student repeat a course to clear an F/XF or improve the grade, and how are old vs new grades shown/used in CGPA?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000089",
            "UG_Handbook_pdf_000090",
            "UG_Handbook_pdf_000148",
            "UG_Handbook_pdf_000149",
            "UG_Handbook_pdf_000188",
            "PG_Handbook_pdf_000085",
            "PG_Handbook_pdf_000118",
        ],
        "category": "course_repetition",
    },
    {
        "query": "What is the maximum number of courses a student may repeat during the degree (per the policy)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000090",
            "PG_Handbook_pdf_000085",
            "PG_Handbook_pdf_000118",
            "PG_Handbook_pdf_000161",
        ],
        "category": "course_repetition",
    },
    # Graduation / award of degree
    {
        "query": "What are the conditions for award of an undergraduate degree (completion of prescribed requirements and minimum criteria)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000073",
            "UG_Handbook_pdf_000130",
            "UG_Handbook_pdf_000159",
        ],
        "category": "graduation",
    },
    {
        "query": "What minimum CGPA is mentioned for successful completion of degree programs (as stated in the handbook grading section)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000062",
            "UG_Handbook_pdf_000073",
            "UG_Handbook_pdf_000107",
            "UG_Handbook_pdf_000159",
            "PG_Handbook_pdf_000060",
        ],
        "category": "graduation",
    },
    # Fees
    {
        "query": "When is tuition fee payable in the semester system, and what does the fee structure annex specify?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000395",
            "UG_Handbook_pdf_000401",
            "PG_Handbook_pdf_000379",
        ],
        "category": "fees",
    },
    {
        "query": "What happens if a student does not deposit dues/fee on time (restrictions/penalties such as 25% fee to keep registration intact)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000153",
            "UG_Handbook_pdf_000243",
            "UG_Handbook_pdf_000245",
            "PG_Handbook_pdf_000128",
            "PG_Handbook_pdf_000224",
        ],
        "category": "fees",
    },
    # Disciplinary policy
    {
        "query": "What does the code of conduct say about enforcement and disciplinary action/penalties for misconduct?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000307",
            "UG_Handbook_pdf_000309",
            "UG_Handbook_pdf_000323",
            "PG_Handbook_pdf_000276",
            "PG_Handbook_pdf_000278",
        ],
        "category": "disciplinary",
    },
    # Thesis / FYP
    {
        "query": "What are the rules for thesis evaluation and defence (committee, external evaluation, and defence scheduling)?",
        "relevant_chunk_ids": [
            "PG_Handbook_pdf_000166",
            "PG_Handbook_pdf_000169",
            "PG_Handbook_pdf_000170",
            "PG_Handbook_pdf_000177",
        ],
        "category": "thesis_fyp",
    },
    # Grading scale
    {
        "query": "What is the grading scale and grade points (e.g., 4.00, 3.50, 3.00 ...) used for percentage marks?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000062",
            "UG_Handbook_pdf_000107",
            "UG_Handbook_pdf_000162",
            "PG_Handbook_pdf_000060",
        ],
        "category": "grading_scale",
    },
    # Leave / deferment policy
    {
        "query": "What is the deferment policy during a degree (conditions and the 25% tuition fee rule during deferment)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000153",
            "PG_Handbook_pdf_000173",
        ],
        "category": "leave_policy",
    },
    # Examination rules
    {
        "query": "What are the examination rules about unfair means and exam conduct (warnings, forbidden material, seating, start rules)?",
        "relevant_chunk_ids": [
            "UG_Handbook_pdf_000056",
            "UG_Handbook_pdf_000058",
            "UG_Handbook_pdf_000287",
            "PG_Handbook_pdf_000057",
            "PG_Handbook_pdf_000059",
            "PG_Handbook_pdf_000254",
        ],
        "category": "examination_rules",
    },
]
