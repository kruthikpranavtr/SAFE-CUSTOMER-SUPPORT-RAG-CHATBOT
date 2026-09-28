import re
from enum import Enum
from typing import Tuple, List, Optional

class ConversationIntent(str, Enum):
    GREETING = "GREETING"
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
                # If only greeting words or polite general greeting up to 7 words without specific topic
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
