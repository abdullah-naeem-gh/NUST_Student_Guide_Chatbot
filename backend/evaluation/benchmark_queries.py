"""Benchmark queries with manually identified relevant chunk ids (Phase 5)."""

from __future__ import annotations

from typing import TypedDict


class BenchmarkQuery(TypedDict):
    """One benchmark query with a ground-truth relevant set."""

    query: str
    relevant_chunk_ids: list[str]
    category: str


# Notes:
# - These relevant_chunk_ids were selected by first retrieving candidates via TF-IDF,
#   then verifying the chunk text in `data/chunks/chunks.json`.
BENCHMARK: list[BenchmarkQuery] = [
    # GPA / academic standing
    {
        "query": "Under what conditions is an undergraduate student considered academically deficient (probation/warning triggers)?",
        "relevant_chunk_ids": [
            "chunk_000128",
            "chunk_000129",
            "chunk_000130",
            "chunk_000145",
            "chunk_000146",
            "chunk_000147",
            "chunk_000156",
            "chunk_000157",
        ],
        "category": "gpa",
    },
    {
        "query": "How are Semester GPA and CGPA reported/approved in the official results?",
        "relevant_chunk_ids": [
            "chunk_000013",
            "chunk_000126",
            "chunk_000127",
            "chunk_000144",
            "chunk_000145",
        ],
        "category": "gpa",
    },
    # Attendance / absence (mapped to missed exams & eligibility language present in corpus)
    {
        "query": "What is the policy when a student misses the mid semester examination due to acceptable reasons (make-up timing)?",
        "relevant_chunk_ids": ["chunk_000011", "chunk_000012", "chunk_000125", "chunk_000142", "chunk_000143"],
        "category": "attendance",
    },
    {
        "query": "What is the policy when a student misses the end semester examination due to acceptable reasons (make-up timing/limits)?",
        "relevant_chunk_ids": ["chunk_000011", "chunk_000012", "chunk_000125", "chunk_000142", "chunk_000143"],
        "category": "attendance",
    },
    # Course repetition
    {
        "query": "Can a student repeat a course to clear an F/XF or improve the grade, and how are old vs new grades shown/used in CGPA?",
        "relevant_chunk_ids": ["chunk_000019", "chunk_000132", "chunk_000133", "chunk_000150", "chunk_000161"],
        "category": "course_repetition",
    },
    {
        "query": "What is the maximum number of courses a student may repeat during the degree (per the policy)?",
        "relevant_chunk_ids": ["chunk_000020"],
        "category": "course_repetition",
    },
    # Graduation / award of degree
    {
        "query": "What are the conditions for award of an undergraduate degree (completion of prescribed requirements and minimum criteria)?",
        "relevant_chunk_ids": ["chunk_000128"],
        "category": "graduation",
    },
    {
        "query": "What minimum CGPA is mentioned for successful completion of degree programs (as stated in the handbook grading section)?",
        "relevant_chunk_ids": ["chunk_000010", "chunk_000154"],
        "category": "graduation",
    },
    # Fees
    {
        "query": "When is tuition fee payable in the semester system, and what does the fee structure annex specify?",
        "relevant_chunk_ids": ["chunk_000179", "chunk_000222"],
        "category": "fees",
    },
    {
        "query": "What happens if a student does not deposit dues/fee on time (restrictions/penalties such as 25% fee to keep registration intact)?",
        "relevant_chunk_ids": ["chunk_000180", "chunk_000181"],
        "category": "fees",
    },
    # Disciplinary policy
    {
        "query": "What does the code of conduct say about enforcement and disciplinary action/penalties for misconduct?",
        "relevant_chunk_ids": ["chunk_000077", "chunk_000078", "chunk_000201", "chunk_000202", "chunk_000204"],
        "category": "disciplinary",
    },
    # Thesis / FYP
    {
        "query": "What are the rules for thesis evaluation and defence (committee, external evaluation, and defence scheduling)?",
        "relevant_chunk_ids": ["chunk_000041", "chunk_000042", "chunk_000045"],
        "category": "thesis_fyp",
    },
    # Grading scale
    {
        "query": "What is the grading scale and grade points (e.g., 4.00, 3.50, 3.00 ...) used for percentage marks?",
        "relevant_chunk_ids": ["chunk_000010", "chunk_000123", "chunk_000138"],
        "category": "grading_scale",
    },
    # Leave / deferment policy (closest in corpus)
    {
        "query": "What is the deferment policy during a degree (conditions and the 25% tuition fee rule during deferment)?",
        "relevant_chunk_ids": ["chunk_000050", "chunk_000134", "chunk_000151"],
        "category": "leave_policy",
    },
    # Examination rules
    {
        "query": "What are the examination rules about unfair means and exam conduct (warnings, forbidden material, seating, start rules)?",
        "relevant_chunk_ids": ["chunk_000008", "chunk_000009", "chunk_000119", "chunk_000120", "chunk_000121"],
        "category": "examination_rules",
    },
]

