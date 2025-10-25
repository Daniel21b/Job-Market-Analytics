def count_keyword_matches(text, keyword_patterns):
    """Count number of keyword pattern matches in text"""
    if pd.isna(text):
        return 0
    
    text_lower = str(text).lower()
    matches = 0
    
    for pattern in keyword_patterns:
        if re.search(pattern, text_lower):
            matches += 1
    
    return matches


def calculate_ai_ml_score(role, description):
    """Calculate AI/ML relevance score (0-100)"""
    score = 0
    
    role_matches = count_keyword_matches(role, AI_ML_KEYWORDS['role_titles'])
    score += role_matches * 30
    
    tech_matches = count_keyword_matches(role, AI_ML_KEYWORDS['technologies'])
    tech_matches += count_keyword_matches(description, AI_ML_KEYWORDS['technologies']) * 0.3
    score += min(tech_matches * 10, 20)
    
    task_matches = count_keyword_matches(role, AI_ML_KEYWORDS['tasks'])
    task_matches += count_keyword_matches(description, AI_ML_KEYWORDS['tasks']) * 0.2
    score += min(task_matches * 8, 20)
    
    return min(score, 100)


def calculate_it_score(role, description):
    """Calculate General IT relevance score (0-100)"""
    score = 0
    
    role_matches = count_keyword_matches(role, GENERAL_IT_KEYWORDS['role_titles'])
    score += role_matches * 25
    
    web_matches = count_keyword_matches(role, GENERAL_IT_KEYWORDS['web_technologies'])
    web_matches += count_keyword_matches(description, GENERAL_IT_KEYWORDS['web_technologies']) * 0.3
    score += min(web_matches * 8, 15)
    
    backend_matches = count_keyword_matches(role, GENERAL_IT_KEYWORDS['backend_technologies'])
    backend_matches += count_keyword_matches(description, GENERAL_IT_KEYWORDS['backend_technologies']) * 0.3
    score += min(backend_matches * 8, 15)
    
    devops_matches = count_keyword_matches(role, GENERAL_IT_KEYWORDS['devops_technologies'])
    devops_matches += count_keyword_matches(description, GENERAL_IT_KEYWORDS['devops_technologies']) * 0.3
    score += min(devops_matches * 8, 15)
    
    return min(score, 100)


def is_non_tech_role(role, description):
    """Check if role is clearly non-technical"""
    combined_text = f"{role} {description}"
    matches = count_keyword_matches(combined_text, NON_TECH_KEYWORDS)
    return matches > 0


def is_hybrid_role(role, description):
    """Check if role shows hybrid AI/ML + IT characteristics"""
    combined_text = f"{role} {description}"
    matches = count_keyword_matches(combined_text, HYBRID_INDICATORS)
    return matches > 0


def categorize_job_role(role, description):
    """
    Categorize a job into one of four categories:
    - 'AI/ML': Primarily AI/Machine Learning roles
    - 'General IT': Software engineering, DevOps, web development, etc.
    - 'Hybrid': Roles with both AI/ML and IT components
    - 'Non-Tech': Non-technical roles
    """
    if is_non_tech_role(role, description):
        return 'Non-Tech'
    
    ai_score = calculate_ai_ml_score(role, description)
    it_score = calculate_it_score(role, description)
    
    has_hybrid_indicators = is_hybrid_role(role, description)
    
    AI_THRESHOLD = 30
    IT_THRESHOLD = 25
    HYBRID_MIN_THRESHOLD = 15
    
    if ai_score >= AI_THRESHOLD and it_score >= IT_THRESHOLD:
        return 'Hybrid'
    
    if ai_score >= AI_THRESHOLD:
        if has_hybrid_indicators and it_score >= HYBRID_MIN_THRESHOLD:
            return 'Hybrid'
        return 'AI/ML'
    
    if it_score >= IT_THRESHOLD:
        if has_hybrid_indicators and ai_score >= HYBRID_MIN_THRESHOLD:
            return 'Hybrid'
        return 'General IT'
    
    if ai_score > 0 or it_score > 0:
        if ai_score > it_score:
            return 'AI/ML'
        else:
            return 'General IT'
    
    return 'Non-Tech'


