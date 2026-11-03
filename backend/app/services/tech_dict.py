"""Tech keyword dictionary used by the compatibility score.

Each entry: canonical tech name -> (aliases found in job descriptions,
GitHub languages that count as evidence for it).

A framework maps to the language(s) it is written in, so "Django" in a JD is
satisfied by Python code in the user's repos, and "React" by JS/TS.
"""

TECH: dict[str, tuple[list[str], list[str]]] = {
    # ---- languages ----
    "Python": (["python", "py"], ["Python", "Jupyter Notebook"]),
    "JavaScript": (["javascript", "js", "ecmascript", "es6"], ["JavaScript"]),
    "TypeScript": (["typescript", "ts"], ["TypeScript"]),
    "Java": (["java", "j2ee", "jvm"], ["Java"]),
    "C++": (["c++", "cpp"], ["C++"]),
    "C": (["c programming", "ansi c", "embedded c"], ["C"]),
    "C#": (["c#", "csharp", ".net", "dotnet", "asp.net"], ["C#"]),
    "Go": (["golang", "go lang"], ["Go"]),
    "Rust": (["rust"], ["Rust"]),
    "Ruby": (["ruby"], ["Ruby"]),
    "PHP": (["php", "laravel"], ["PHP"]),
    "Swift": (["swift", "swiftui"], ["Swift"]),
    "Kotlin": (["kotlin"], ["Kotlin"]),
    "Dart": (["dart", "flutter"], ["Dart"]),
    "Scala": (["scala"], ["Scala"]),
    "R": (["r programming", "rstudio", "tidyverse", "ggplot"], ["R"]),
    "MATLAB": (["matlab", "simulink"], ["MATLAB"]),
    "SQL": (["sql", "mysql", "postgresql", "postgres", "sqlite", "pl/sql", "t-sql"], ["SQL", "PLpgSQL", "TSQL", "PLSQL"]),
    "Shell": (["bash", "shell scripting", "shell"], ["Shell", "PowerShell"]),
    "HTML/CSS": (["html", "css", "html5", "css3", "tailwind", "sass", "scss"], ["HTML", "CSS", "SCSS", "Sass"]),

    # ---- frameworks / libraries -> language ----
    "React": (["react", "reactjs", "react.js", "next.js", "nextjs", "redux"], ["JavaScript", "TypeScript"]),
    "Angular": (["angular", "angularjs"], ["TypeScript"]),
    "Vue": (["vue", "vuejs", "vue.js", "nuxt"], ["Vue", "JavaScript", "TypeScript"]),
    "Node.js": (["node", "nodejs", "node.js", "express.js", "expressjs", "nestjs"], ["JavaScript", "TypeScript"]),
    "Django": (["django"], ["Python"]),
    "Flask": (["flask"], ["Python"]),
    "FastAPI": (["fastapi"], ["Python"]),
    "Spring": (["spring boot", "springboot", "spring framework", "spring mvc", "hibernate"], ["Java", "Kotlin"]),
    "Machine Learning": (["machine learning", "ml", "scikit-learn", "sklearn", "xgboost", "lightgbm"], ["Python", "Jupyter Notebook", "R"]),
    "Deep Learning": (["deep learning", "pytorch", "tensorflow", "keras", "neural networks", "cnn", "transformers"], ["Python", "Jupyter Notebook"]),
    "Data Analysis": (["pandas", "numpy", "data analysis", "data analytics", "matplotlib", "seaborn"], ["Python", "Jupyter Notebook", "R"]),
    "Docker": (["docker", "dockerfile", "containers"], ["Dockerfile"]),
    "Terraform": (["terraform", "hcl"], ["HCL"]),
    "Android": (["android"], ["Kotlin", "Java"]),
    "iOS": (["ios"], ["Swift", "Objective-C"]),
    "Solidity": (["solidity", "smart contracts"], ["Solidity"]),
}


def build_patterns() -> list[tuple[str, str, list[str]]]:
    """(canonical, alias, languages) sorted longest alias first so
    'spring boot' wins over 'spring' and 'react.js' over 'react'."""
    rows = [(canon, alias, langs) for canon, (aliases, langs) in TECH.items() for alias in aliases]
    return sorted(rows, key=lambda r: len(r[1]), reverse=True)
