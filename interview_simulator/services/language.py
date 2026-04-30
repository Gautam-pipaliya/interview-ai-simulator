SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "native_name": "English",
        "html_lang": "en",
        "speech_code": "en-US",
        "voice_hint": "English",
        "take_time": "Take your time and answer.",
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "html_lang": "hi",
        "speech_code": "hi-IN",
        "voice_hint": "Hindi",
        "take_time": "अपना समय लें और उत्तर दें।",
    },
    "gu": {
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "html_lang": "gu",
        "speech_code": "gu-IN",
        "voice_hint": "Gujarati",
        "take_time": "તમારો સમય લો અને જવાબ આપો.",
    },
    "mr": {
        "name": "Marathi",
        "native_name": "मराठी",
        "html_lang": "mr",
        "speech_code": "mr-IN",
        "voice_hint": "Marathi",
        "take_time": "तुमचा वेळ घ्या आणि उत्तर द्या.",
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "html_lang": "te",
        "speech_code": "te-IN",
        "voice_hint": "Telugu",
        "take_time": "మీ సమయం తీసుకుని సమాధానం ఇవ్వండి.",
    },
}


ROUND_CARDS = [
    {
        "key": "HR",
        "label": "HR Round",
        "short_label": "HR",
        "summary": "Communication, motivation, culture fit, strengths, weaknesses, and role alignment.",
        "accent": "coral",
    },
    {
        "key": "Aptitude",
        "label": "Aptitude Round",
        "short_label": "Aptitude",
        "summary": "Quantitative aptitude, reasoning, probability, speed, distance, and pattern logic.",
        "accent": "amber",
    },
    {
        "key": "Technical",
        "label": "Technical Round",
        "short_label": "Technical",
        "summary": "Programming, CS fundamentals, APIs, databases, systems, testing, and engineering tradeoffs.",
        "accent": "blue",
    },
    {
        "key": "Coding",
        "label": "Coding Round",
        "short_label": "Coding",
        "summary": "Problem solving with a code editor, syntax modes, starter snippets, and browser-side run support.",
        "accent": "green",
    },
]


ROUND_LABELS = {
    "en": {
        "HR": "HR Round",
        "Aptitude": "Aptitude Round",
        "Technical": "Technical Round",
        "Coding": "Coding Round",
        "Behavioral": "Behavioral Round",
        "All": "All Rounds",
    },
    "hi": {
        "HR": "एचआर राउंड",
        "Aptitude": "एप्टीट्यूड राउंड",
        "Technical": "टेक्निकल राउंड",
        "Coding": "कोडिंग राउंड",
        "Behavioral": "व्यवहारिक राउंड",
        "All": "सभी राउंड",
    },
    "gu": {
        "HR": "એચઆર રાઉન્ડ",
        "Aptitude": "એપ્ટિટ્યુડ રાઉન્ડ",
        "Technical": "ટેક્નિકલ રાઉન્ડ",
        "Coding": "કોડિંગ રાઉન્ડ",
        "Behavioral": "બિહેવિયરલ રાઉન્ડ",
        "All": "બધા રાઉન્ડ",
    },
    "mr": {
        "HR": "एचआर राउंड",
        "Aptitude": "अॅप्टिट्यूड राउंड",
        "Technical": "टेक्निकल राउंड",
        "Coding": "कोडिंग राउंड",
        "Behavioral": "वर्तनात्मक राउंड",
        "All": "सर्व राउंड",
    },
    "te": {
        "HR": "హెచ్ఆర్ రౌండ్",
        "Aptitude": "ఆప్టిట్యూడ్ రౌండ్",
        "Technical": "టెక్నికల్ రౌండ్",
        "Coding": "కోడింగ్ రౌండ్",
        "Behavioral": "బిహేవియరల్ రౌండ్",
        "All": "అన్ని రౌండ్లు",
    },
}


def normalize_language(language_code):
    candidate = str(language_code or "en").strip().lower()
    return candidate if candidate in SUPPORTED_LANGUAGES else "en"


def get_language_options():
    return [
        {
            "code": code,
            "name": meta["name"],
            "native_name": meta["native_name"],
            "speech_code": meta["speech_code"],
        }
        for code, meta in SUPPORTED_LANGUAGES.items()
    ]


def get_language_config(language_code):
    code = normalize_language(language_code)
    payload = dict(SUPPORTED_LANGUAGES[code])
    payload["code"] = code
    return payload


def get_round_label(category, language_code="en"):
    code = normalize_language(language_code)
    return ROUND_LABELS.get(code, ROUND_LABELS["en"]).get(category, category)


def get_ai_language_instruction(language_code):
    config = get_language_config(language_code)
    if config["code"] == "en":
        return "Write every prompt, option, answer key, explanation, and feedback in English."

    return (
        f"Write every prompt, option, answer key, explanation, and feedback in {config['name']} "
        f"({config['native_name']}). Keep programming language keywords unchanged when needed."
    )


def get_take_time_phrase(language_code):
    return get_language_config(language_code)["take_time"]


def localize_feedback(evaluation, language_code):
    code = normalize_language(language_code)
    if code == "en":
        return evaluation

    score = float(evaluation.get("score", 0.0) or 0.0)
    missing_keywords = list(evaluation.get("missing_keywords", []) or [])

    if code == "hi":
        if score >= 80:
            feedback = "बहुत अच्छा उत्तर। आपने मुख्य बातों को स्पष्ट तरीके से समझाया।"
        elif score >= 60:
            feedback = "अच्छा उत्तर। थोड़ा और उदाहरण और गहराई जोड़ें।"
        elif score >= 40:
            feedback = "औसत उत्तर। दिशा सही है, लेकिन कुछ महत्वपूर्ण बिंदु छूट गए।"
        else:
            feedback = "इस उत्तर में सुधार की जरूरत है। अपेक्षित बिंदुओं से इसे और जोड़ें।"
        if missing_keywords:
            feedback += " इन बिंदुओं को शामिल करें: " + ", ".join(missing_keywords[:5]) + "."
    elif code == "gu":
        if score >= 80:
            feedback = "ખૂબ સારું ઉત્તર. તમે મુખ્ય મુદ્દા સ્પષ્ટ રીતે સમજાવ્યા."
        elif score >= 60:
            feedback = "સારું ઉત્તર. થોડું વધુ ઉદાહરણ અને ઊંડાણ ઉમેરો."
        elif score >= 40:
            feedback = "સરેરાશ ઉત્તર. દિશા સારી છે, પણ કેટલાક મહત્વના મુદ્દા રહી ગયા."
        else:
            feedback = "આ ઉત્તરમાં સુધારાની જરૂર છે. અપેક્ષિત મુદ્દાઓ સાથે વધુ જોડો."
        if missing_keywords:
            feedback += " આ મુદ્દાઓ ઉમેરો: " + ", ".join(missing_keywords[:5]) + "."
    elif code == "mr":
        if score >= 80:
            feedback = "खूप चांगले उत्तर. तुम्ही मुख्य मुद्दे स्पष्टपणे मांडले."
        elif score >= 60:
            feedback = "चांगले उत्तर. थोडी अधिक उदाहरणे आणि सखोलता जोडा."
        elif score >= 40:
            feedback = "सरासरी उत्तर. दिशा योग्य आहे, पण काही महत्त्वाचे मुद्दे राहिले."
        else:
            feedback = "या उत्तरात सुधारणा आवश्यक आहे. अपेक्षित मुद्द्यांशी ते अधिक जोडा."
        if missing_keywords:
            feedback += " हे मुद्दे जोडा: " + ", ".join(missing_keywords[:5]) + "."
    else:
        if score >= 80:
            feedback = "చాలా మంచి సమాధానం. మీరు ప్రధాన అంశాలను స్పష్టంగా వివరించారు."
        elif score >= 60:
            feedback = "మంచి సమాధానం. మరికొన్ని ఉదాహరణలు మరియు లోతు జోడించండి."
        elif score >= 40:
            feedback = "సగటు సమాధానం. దిశ సరైనదే, కానీ కొన్ని ముఖ్యమైన అంశాలు మిస్సయ్యాయి."
        else:
            feedback = "ఈ సమాధానాన్ని మెరుగుపరచాలి. అంచనా అంశాలతో మరింతగా అనుసంధానించండి."
        if missing_keywords:
            feedback += " ఈ అంశాలను చేర్చండి: " + ", ".join(missing_keywords[:5]) + "."

    localized = dict(evaluation)
    localized["feedback"] = feedback
    return localized


def localize_mcq_feedback(*, selected, correct, ideal_answer, is_correct, language_code):
    code = normalize_language(language_code)
    if code == "en":
        if not selected:
            return f"No option selected. Correct answer: {correct}. {ideal_answer}"
        if is_correct:
            return f"Correct answer. {ideal_answer}"
        return f"Incorrect answer. Correct answer: {correct}. {ideal_answer}"

    selected = selected or ""
    correct = correct or ""
    ideal_answer = ideal_answer or ""

    if code == "hi":
        if not selected:
            return f"कोई विकल्प नहीं चुना गया। सही उत्तर: {correct}. {ideal_answer}"
        if is_correct:
            return f"सही उत्तर। {ideal_answer}"
        return f"गलत उत्तर। सही उत्तर: {correct}. {ideal_answer}"
    if code == "gu":
        if not selected:
            return f"કોઈ વિકલ્પ પસંદ થયો નથી. સાચો જવાબ: {correct}. {ideal_answer}"
        if is_correct:
            return f"સાચો જવાબ. {ideal_answer}"
        return f"ખોટો જવાબ. સાચો જવાબ: {correct}. {ideal_answer}"
    if code == "mr":
        if not selected:
            return f"कोणताही पर्याय निवडलेला नाही. बरोबर उत्तर: {correct}. {ideal_answer}"
        if is_correct:
            return f"बरोबर उत्तर. {ideal_answer}"
        return f"चुकीचे उत्तर. बरोबर उत्तर: {correct}. {ideal_answer}"

    if not selected:
        return f"ఎటువంటి ఎంపిక ఎంచుకోలేదు. సరైన సమాధానం: {correct}. {ideal_answer}"
    if is_correct:
        return f"సరైన సమాధానం. {ideal_answer}"
    return f"తప్పు సమాధానం. సరైన సమాధానం: {correct}. {ideal_answer}"
