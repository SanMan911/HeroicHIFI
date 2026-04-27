import os
import uuid
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


async def generate_event_article(event_data: dict) -> str:
    api_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not api_key:
        return _fallback_article(event_data)
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"event-article-{uuid.uuid4()}",
            system_message="You are an eloquent writer for Heroic HIFI Foundation, an Indian NGO. Write beautiful, inspiring articles about volunteer events. Use vivid language, mention volunteers by name, and highlight the positive impact. Keep it 300-500 words. Write in English. Do not use markdown formatting - write plain text with paragraph breaks."
        ).with_model("gemini", "gemini-3-flash-preview")

        volunteers = ", ".join(event_data.get("volunteer_names", [])) or "dedicated volunteers"
        prompt = f"""Write an inspiring article about this volunteer event:

Event: {event_data.get('title', 'Community Drive')}
Mission: {event_data.get('mission', 'Community Service')}
Date: {event_data.get('date', '')}
Location: {event_data.get('location', '')}
Duration: {event_data.get('time_spent', '')}
Resources Used: {event_data.get('resources_spent', '')}
Summary: {event_data.get('summary', '')}
Outcome: {event_data.get('outcome', '')}
Issues Faced: {event_data.get('issues', 'None')}
Volunteers Who Participated: {volunteers}
Star Hero: {event_data.get('star_hero', 'the entire team')}

Write a beautiful narrative that celebrates the volunteers and the impact they made. Mention the Star Hero prominently. End with an inspiring call to action."""

        response = await chat.send_message(UserMessage(text=prompt))
        return response
    except Exception as e:
        logger.error(f"LLM article generation error: {e}")
        return _fallback_article(event_data)


def _fallback_article(event_data: dict) -> str:
    volunteers = ", ".join(event_data.get("volunteer_names", [])) or "our dedicated volunteers"
    star_hero = event_data.get("star_hero", "the entire team")
    return f"""On {event_data.get('date', 'a memorable day')}, Heroic HIFI Foundation organized "{event_data.get('title', 'a community drive')}" at {event_data.get('location', 'the community center')} under {event_data.get('mission', 'our mission')}.

{event_data.get('summary', 'The event was a great success.')}

Our amazing volunteers who made this possible: {volunteers}. Special recognition goes to our Star Hero of the event: {star_hero}, whose dedication and effort stood out.

Resources utilized: {event_data.get('resources_spent', 'Various resources')}. Time invested: {event_data.get('time_spent', 'Several hours')}.

Outcome: {event_data.get('outcome', 'The event achieved its goals successfully.')}

We are grateful for every volunteer who gave their time and energy. Together, we are making a difference. Join us in our next drive!"""
