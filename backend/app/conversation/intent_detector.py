import re
from enum import Enum
from typing import Tuple, List, Optional

class ConversationIntent(str, Enum):
    GREETING = "GREETING"
    SMALLTALK_WELLBEING = "SMALLTALK_WELLBEING"
    BOT_IDENTITY = "BOT_IDENTITY"
    BOT_CAPABILITIES = "BOT_CAPABILITIES"
    GRATITUDE = "GRATITUDE"
    HELP_REQUEST = "HELP_REQUEST"
    FAREWELL = "FAREWELL"
    AFFIRMATION = "AFFIRMATION"
    COMPANY_INFO = "COMPANY_INFO"
    PRODUCT_INFO = "PRODUCT_INFO"
    ORDER_STATUS = "ORDER_STATUS"
    DELIVERY = "DELIVERY"
    RETURN = "RETURN"
    REFUND = "REFUND"
    CANCELLATION = "CANCELLATION"
    WARRANTY = "WARRANTY"
    PAYMENT = "PAYMENT"
    ACCOUNT = "ACCOUNT"
    COMPLAINT = "COMPLAINT"
    HUMAN_SUPPORT = "HUMAN_SUPPORT"
    CLARIFICATION_RESPONSE = "CLARIFICATION_RESPONSE"
    GENERAL_SUPPORT = "GENERAL_SUPPORT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"

class IntentDetector:
    """
    Fast, deterministic intent classification engine supporting both
    English, Tamil, and Tanglish customer support queries.
    """

    GREETING_PATTERNS = [
        r'^\s*(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|howdy|greetings|hola)\b',
        r'^\s*(?:வணக்கம்|ஹலோ|ஹாய்)\b'
    ]

    WELLBEING_PATTERNS = [
        r'^\s*(?:how\s+are\s+you|how\s+r\s+u|how\'?s\s+it\s+going|how\s+are\s+you\s+doing|how\s+do\s+you\s+do|what\'?s\s+up|how\s+is\s+your\s+day)\b',
        r'^\s*(?:எப்படி\s+இருக்கிறீர்கள்|எப்படி\s+இருக்கீங்க|நலமா)\b'
    ]

    IDENTITY_PATTERNS = [
        r'\b(?:who\s+are\s+you|who\s+r\s+u|what\s+is\s+your\s+name|what\'?s\s+your\s+name|what\s+are\s+you|are\s+you\s+human|are\s+you\s+an?\s+ai|are\s+you\s+a\s+bot|are\s+you\s+a\s+robot|tell\s+me\s+about\s+yourself|introduce\s+yourself|who\s+made\s+you)\b',
        r'\b(?:நீங்கள்\s+யார்|உன்\s+பெயர்\s+என்ன|நீ\s+யார்|ரோபோவா)\b'
    ]

    CAPABILITIES_PATTERNS = [
        r'\b(?:what\s+can\s+you\s+do|what\s+can\s+you\s+help\s+(?:me\s+)?with|how\s+can\s+you\s+help(?:\s+me)?|what\s+are\s+your\s+(?:features|capabilities)|what\s+help\s+can\s+you\s+provide|what\s+can\s+i\s+ask\s+(?:you)?)\b',
        r'\b(?:உன்னால்\s+என்ன\s+செய்ய\s+முடியும்|என்ன\s+உதவி\s+செய்ய\s+முடியும்)\b'
    ]

    GRATITUDE_PATTERNS = [
        r'^\s*(?:thank\s+you|thanks|thank\s+u|thx|thanks\s+a\s+lot|thank\s+you\s+so\s+much|many\s+thanks|appreciate\s+it|much\s+appreciated)\b',
        r'^\s*(?:நன்றி|மிக்க\s+நன்றி|ரொம்ப\s+நன்றி)\b'
    ]

    HELP_REQUEST_PATTERNS = [
        r'^\s*(?:can\s+you\s+help\s+me|could\s+you\s+help\s+me|i\s+need\s+help|help\s+me|i\s+have\s+a\s+question|i\s+have\s+an?\s+issue|i\s+need\s+assistance|can\s+i\s+ask\s+a\s+question)\b',
        r'^\s*(?:உதவி\s+வேண்டும்|உதவ\s+முடியுமா|எனக்கு\s+ஒரு\s+கேள்வி\s+உள்ளது)\b'
    ]

    FAREWELL_PATTERNS = [
        r'^\s*(?:bye|goodbye|bye\s+bye|see\s+you|see\s+ya|talk\s+to\s+you\s+later|take\s+care|have\s+a\s+(?:good|nice|great)\s+day|good\s+night)\b',
        r'^\s*(?:போய்\s+வருகிறேன்|பை|வணக்கம்\s+மீண்டும்\s+பார்ப்போம்)\b'
    ]

    AFFIRMATION_PATTERNS = [
        r'^\s*(?:ok|okay|alright|cool|got\s+it|understood|sure|great|perfect|sounds\s+good|nice|all\s+good)\b',
        r'^\s*(?:சரி|புரிந்தது|நல்லது)\b'
    ]

    COMPANY_PATTERNS = [
        r'\b(?:tell\s+me\s+about\s+(?:the|your)\s+company|what\s+company\s+is\s+this|who\s+is\s+technova|about\s+technova|what\s+is\s+technova|company\s+overview)\b',
        r'\b(?:what\s+do\s+you\s+sell|what\s+products\s+do\s+you\s+(?:have|sell|offer)|what\s+do\s+you\s+offer|product\s+catalog|list\s+of\s+products|what\s+devices\s+do\s+you\s+have)\b',
        r'\b(?:என்ன\s+தயாரிப்புகள்|என்ன\s+விற்கிறீர்கள்|தயாரிப்பு\s+பட்டியல்)\b'
    ]

    INTENT_KEYWORDS = {
        ConversationIntent.HUMAN_SUPPORT: [
            r'\b(?:human|person|agent|representative|supervisor|support\s+team|live\s+agent)\b',
            r'\b(?:speak\s+with|talk\s+to|transfer\s+to)\s+(?:a\s+)?(?:human|person|agent)\b',
            r'\b(?:மனித\s+ஆதரவு|நேரடி\s+உதவி)\b'
        ],
        ConversationIntent.CANCELLATION: [
            r'\b(?:cancel|cancellation|cancelling|revoke\s+order)\b',
            r'\b(?:ரத்து|ஆர்டர்\s+ரத்து)\b'
        ],
        ConversationIntent.REFUND: [
            r'\b(?:refund|refunds|money\s+back|reimbursement|return\s+payment)\b',
            r'\b(?:ரீஃபண்ட்|ரிஃபண்ட்|பணம்\s+திரும்ப)\b'
        ],
        ConversationIntent.RETURN: [
            r'\b(?:return|returns|returning|send\s+back|rma|exchange)\b',
            r'\b(?:திருப்பி|பொருள்\s+திரும்புதல்)\b'
        ],
        ConversationIntent.DELIVERY: [
            r'\b(?:shipping|delivery|shipment|courier|transit|ground\s+shipping|express|overnight)\b',
            r'\b(?:டெலிவரி|ஷிப்பிங்|போக்குவரத்து)\b'
        ],
        ConversationIntent.ORDER_STATUS: [
            r'\b(?:track|tracking|order\s+status|where\s+is\s+my\s+order|order\s+update)\b',
            r'\b(?:ஆர்டர்\s+நிலை|ட்ராக்)\b'
        ],
        ConversationIntent.WARRANTY: [
            r'\b(?:warranty|guarantee|refurbished\s+warranty|coverage|repair|replacement)\b',
            r'\b(?:உத்தரவாதம்|வாரண்டி)\b'
        ],
        ConversationIntent.PRODUCT_INFO: [
            r'\b(?:spec|specs|specifications|novabook|ram|charger|battery|display|processor|hardware)\b',
            r'\b(?:விவரக்குறிப்பு|சார்ஜர்|பேட்டரி)\b'
        ],
        ConversationIntent.PAYMENT: [
            r'\b(?:payment|pay|credit\s+card|debit\s+card|paypal|cryptocurrency|crypto|bitcoin|billing)\b',
            r'\b(?:பணம்\s+செலுத்துதல்|கட்டணம்)\b'
        ],
        ConversationIntent.ACCOUNT: [
            r'\b(?:password|reset\s+password|login|account|profile|email\s+address|sign\s+in)\b',
            r'\b(?:கடவுச்சொல்|கணக்கு)\b'
        ],
        ConversationIntent.COMPLAINT: [
            r'\b(?:complaint|complain|fraud|dispute|damaged|broken|defective|poor\s+service)\b',
            r'\b(?:சேதமடைந்த|புகார்)\b'
        ]
    }

    # Out-of-scope triggers (coding, essays, general trivia)
    OUT_OF_SCOPE_PATTERNS = [
        r'\b(?:write\s+a\s+(?:python|javascript|code|script|essay|poem)|solve\s+math|quicksort|fibonacci)\b',
        r'\b(?:who\s+won\s+the|tell\s+me\s+a\s+joke|weather\s+in|recipe\s+for)\b'
    ]

    @classmethod
    def detect_intent(
        cls, 
        query: str, 
        previous_intent: Optional[str] = None,
        is_awaiting_clarification: bool = False
    ) -> Tuple[ConversationIntent, float]:
        """
        Detects primary user intent and confidence score (0.0 - 1.0).
        """
        query_lower = query.lower().strip()

        # Check pure greeting
        for p in cls.GREETING_PATTERNS:
            if re.search(p, query_lower):
                clean_words = re.findall(r'\b\w+\b', query_lower)
                has_specific_domain = any(
                    re.search(pat, query_lower) 
                    for intent in [
                        ConversationIntent.REFUND, 
                        ConversationIntent.RETURN, 
                        ConversationIntent.CANCELLATION,
                        ConversationIntent.DELIVERY, 
                        ConversationIntent.WARRANTY, 
                        ConversationIntent.ORDER_STATUS
                    ] 
                    for pat in cls.INTENT_KEYWORDS.get(intent, [])
                )
                if len(clean_words) <= 7 and not has_specific_domain:
                    return ConversationIntent.GREETING, 0.95

        # Check smalltalk wellbeing ("how are you?")
        for p in cls.WELLBEING_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.SMALLTALK_WELLBEING, 0.95

        # Check bot identity ("who are you?", "what is your name?")
        for p in cls.IDENTITY_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.BOT_IDENTITY, 0.95

        # Check bot capabilities ("what can you do?")
        for p in cls.CAPABILITIES_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.BOT_CAPABILITIES, 0.95

        # Check gratitude ("thank you", "thanks")
        for p in cls.GRATITUDE_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.GRATITUDE, 0.95

        # Check farewell ("bye", "goodbye")
        for p in cls.FAREWELL_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.FAREWELL, 0.95

        # Check simple affirmation ("ok", "got it", "cool")
        for p in cls.AFFIRMATION_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.AFFIRMATION, 0.95

        # Check general help request ("can you help me?", "i have a question")
        for p in cls.HELP_REQUEST_PATTERNS:
            if re.search(p, query_lower):
                has_specific_domain = any(
                    re.search(pat, query_lower) 
                    for intent in [
                        ConversationIntent.REFUND, 
                        ConversationIntent.RETURN, 
                        ConversationIntent.CANCELLATION,
                        ConversationIntent.DELIVERY, 
                        ConversationIntent.WARRANTY, 
                        ConversationIntent.ORDER_STATUS,
                        ConversationIntent.PRODUCT_INFO,
                        ConversationIntent.PAYMENT,
                        ConversationIntent.ACCOUNT
                    ] 
                    for pat in cls.INTENT_KEYWORDS.get(intent, [])
                )
                if not has_specific_domain:
                    return ConversationIntent.HELP_REQUEST, 0.95

        # Check company info ("tell me about your company", "who is technova")
        for p in cls.COMPANY_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.COMPANY_INFO, 0.95

        # Check out-of-scope
        for p in cls.OUT_OF_SCOPE_PATTERNS:
            if re.search(p, query_lower):
                return ConversationIntent.OUT_OF_SCOPE, 0.95

        # Check if user is responding to a clarification question
        if is_awaiting_clarification:
            return ConversationIntent.CLARIFICATION_RESPONSE, 0.90

        # Match domain patterns
        best_intent = ConversationIntent.UNKNOWN
        best_matches = 0

        for intent, patterns in cls.INTENT_KEYWORDS.items():
            matches = 0
            for pat in patterns:
                if re.search(pat, query_lower):
                    matches += 1
            if matches > best_matches:
                best_matches = matches
                best_intent = intent

        if best_matches > 0:
            confidence = min(0.60 + 0.15 * best_matches, 0.95)
            return best_intent, confidence

        # Fallback to previous intent if query is an elliptical follow-up
        if previous_intent and previous_intent in ConversationIntent._value2member_map_:
            elliptical_indicators = [
                r'^\s*(?:and|what\s+about|how\s+about|can\s+i|what\s+if|does\s+it|is\s+it)\b',
                r'^\s*(?:express|ground|overnight|damaged|refurbished|international)\b',
                r'^\s*(?:அப்படியானால்|மற்றும்|என்றால்)\b'
            ]
            for ep in elliptical_indicators:
                if re.search(ep, query_lower):
                    return ConversationIntent(previous_intent), 0.75

        return ConversationIntent.GENERAL_SUPPORT, 0.50
