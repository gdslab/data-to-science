# B15 — Design Patterns Case Study: Data-to-Science (D2S)

## Team
| Roll Number | Name | Batch |
|-------------|------|-------|
| AM.sc.u4cse23321 | Harikrishna T P | CSE 2023 |

## Case Study Application
**Data-to-Science (D2S)** — Open-source geospatial research data management platform.
- GitHub: https://github.com/gdslab/data-to-science
- Stack: FastAPI + React + PostgreSQL + Celery

## Folder Structure
```
B15/
├── README.md
├── B15_Final_Report.pdf        ← Combined report (all parts)
├── data/
│   ├── patterns.csv            ← All pattern instances
│   ├── pattern_counts.csv      ← Pattern counts per part/snapshot
│   ├── cross_language.csv      ← Cross-language metrics
│   └── llm.csv                 ← LLM usage records
├── Part1/                      ← Design Pattern Discovery
│   ├── Part1_Report.pdf
│   ├── code/                   ← D2S source (symlink/copy)
│   ├── evidence/               ← Pattern evidence notes
│   └── llm/                    ← LLM prompts + outputs
├── Part2/                      ← Software Evolution (CH01/CH02/CH03)
│   ├── Part2_Evolution.pdf
│   ├── code/                   ← Evolved code
│   ├── evidence/
│   └── llm/
└── Part3/                      ← Cross-Language Analysis
    ├── Part3_CrossLang.pdf
    ├── code/java/              ← Java implementations
    ├── code/python/            ← Python implementations
    ├── code/js/                ← JavaScript implementations
    ├── code/cpp/               ← C++ implementations
    ├── test-cases/             ← Test specs and results
    ├── evidence/               ← Verification notes
    └── llm/                    ← LLM prompts + outputs
```

## How to Run
```bash
# Python
python3 B15/Part3/code/python/strategy.py
python3 B15/Part3/code/python/observer.py

# JavaScript
node B15/Part3/code/js/strategy.js
node B15/Part3/code/js/observer.js

# Java
cd B15/Part3/code/java && javac Strategy.java && java Strategy
cd B15/Part3/code/java && javac Observer.java && java Observer

# C++
cd B15/Part3/code/cpp && g++ -std=c++17 strategy.cpp -o s && ./s
cd B15/Part3/code/cpp && g++ -std=c++17 observer.cpp -o o && ./o
```
