from typing import List
from backend.app.conversation.intent_detector import ConversationIntent

class SuggestionsEngine:
    """
    SECTION 46 — SMART FOLLOW-UP SUGGESTIONS
    Generates domain-grounded follow-up suggestion chips based on the
    detected intent, active topic, and response status.
    """

    SUGGESTIONS_BY_INTENT = {
        ConversationIntent.GREETING: [
            "How long do I have to request a refund?",
            "How long does standard shipping take?",
            "What does the 1-year warranty cover?"
        ],
        ConversationIntent.REFUND: [
            "How do I submit a refund request?",
            "What if my item arrived damaged?",
            "Speak to a human representative"
        ],
        ConversationIntent.RETURN: [
            "What is the condition requirement for returns?",
            "Are return shipping labels prepaid?",
            "Contact human support"
        ],
        ConversationIntent.DELIVERY: [
            "Do you offer express shipping options?",
            "What is the shipping fee for orders under $50?",
            "How do I track my delivery?"
        ],
        ConversationIntent.CANCELLATION: [
            "What is the cancellation window?",
            "Can I cancel an order that has already shipped?",
            "Speak with human support"
        ],
        ConversationIntent.WARRANTY: [
            "What is the warranty for refurbished laptops?",
            "Does warranty cover accidental liquid spills?",
            "How do I initiate a warranty claim?"
        ],
        ConversationIntent.PRODUCT_INFO: [
            "Can I upgrade the RAM with standard tools?",
            "What charger is included in the box?",
            "What is the return window for laptops?"
        ],
        ConversationIntent.ORDER_STATUS: [
            "How long does ground delivery take?",
            "What if my package is delayed?",
            "Speak with human support"
        ],
        ConversationIntent.COMPLAINT: [
            "Transfer me to a live supervisor",
            "What is the refund policy for damaged goods?",
            "Submit a formal support ticket"
        ],
        ConversationIntent.HUMAN_SUPPORT: [
            "Connect me with a support specialist",
            "What are your live support operating hours?",
            "Browse knowledge base documents"
        ]
    }

    SUGGESTIONS_TA = {
        ConversationIntent.GREETING: [
            "பணம் திரும்பப் பெறுவதற்கான விதிமுறைகள் என்ன?",
            "டெலிவரி எத்தனை நாட்களில் வரும்?",
            "வாரண்டி கால அளவு என்ன?"
        ],
        ConversationIntent.REFUND: [
            "சேதமடைந்த பொருளைத் திருப்ப முடியுமா?",
            "ரீஃபண்ட் பெற எத்தனை நாட்கள் ஆகும்?",
            "மனித ஆதரவு குழுவைத் தொடர்பு கொள்ளவும்"
        ],
        ConversationIntent.DELIVERY: [
            "எக்ஸ்பிரஸ் ஷிப்பிங் வசதி உள்ளதா?",
            "இலவச டெலிவரிக்கு குறைந்தபட்ச தொகை என்ன?",
            "ஆர்டரை டிராக் செய்வது எப்படி?"
        ]
    }

    @classmethod
    def get_suggestions(
        cls, 
        intent: ConversationIntent, 
        requires_human: bool = False,
        status: str = "SUPPORTED",
        language: str = "en"
    ) -> List[str]:
        """
        Returns 2 to 3 contextual, domain-accurate suggestion chips.
        """
        if language == "ta":
            tamil_list = cls.SUGGESTIONS_TA.get(intent)
            if tamil_list:
                return tamil_list
            return [
                "ரீஃபண்ட் பாலிசி என்ன?",
                "ஷிப்பிங் விவரங்கள் என்ன?",
                "மனித ஆதரவு குழுவைத் தொடர்பு கொள்ளவும்"
            ]

        if requires_human or status == "ABSTAINED":
            return [
                "Connect with a human representative",
                "Review Refund Policy document",
                "Check delivery timelines"
            ]

        suggestions = cls.SUGGESTIONS_BY_INTENT.get(intent)
        if suggestions:
            return suggestions

        return [
            "How long do I have to request a refund?",
            "How long does standard delivery take?",
            "Contact human support"
        ]
