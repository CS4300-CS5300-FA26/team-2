# For django signals
from django.db.models.signals import post_save
from django.dispatch import receiver

from listings.models import Listing
from .models import CredibilityScore

# For getting api key
import os
import re
from dotenv import load_dotenv
load_dotenv()

# For AI functionality
from openai import OpenAI


def parse_credibility_response(answer):
    
    # Ensure AI output in desired format
    match = re.fullmatch(
        r"\s*Reasons:\s*(.*?)\s*;\s*Final Score:\s*(\d{1,3})\s*",
        answer,
        flags=re.IGNORECASE,
    )
    
    # Error if AI outputs outside of desired format
    if match is None:
        raise ValueError(f"Invalid credibility response format: {answer!r}")

    # Splice the AI output
    reasoning = match.group(1).strip()
    score = int(match.group(2))
    
    # Error if AI outputs incorrectly
    if not reasoning:
        raise ValueError("Credibility reasoning must not be empty")
    if len(reasoning) > 256:
        raise ValueError("Credibility reasoning must be 256 characters or fewer")
    if not 1 <= score <= 100:
        raise ValueError(f"Credibility score must be between 1 and 100: {score}")

    return reasoning, score


'''
https://docs.djangoproject.com/en/6.1/ref/signals/
signals are apparently how you can create an instance of a paired model when the original model is created
'''
@receiver(post_save, sender=Listing)
def create_credscore(sender, instance, created, raw=False, **kwargs):
    '''
    create_credscore - Runs upon instance of listing being created to create a credibility score attached to it.
    Calls AI from key to read the listing object, generate a score, and put it's reasoning in the reasoning attribute
    '''
    if not created or raw:
        return

    # Create instance of model
    client = OpenAI(
        api_key = os.environ["OPENAI_API_KEY"]
    )
    
    # Give model listing to judge
    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[{"role": "user", "content": 
            f"""You will give this job listing a score from 1-100 for our website. 
            Base the score off of how credible the job listing seems. 
            Give a few main 1-5 word reasons within 256 characters.
            Keep in mind that for the listing Django model, the only attributes are the job title, company name, and listing creation time.
            Do not expect job descriptions, or anything other than what is supplied by the model.
            Give your response in this format, as the response will be spliced in code, no other fluff: 
            'Reasons: [256 or less characters of 1-5 word reasons]; Final Score: [number score 1-100]'. 
            This is the job listing -> Title: {instance.title}; Company: {instance.company}; 
            When created: {instance.created_at}"""}]
    )
    
    # Get response
    answer = response.choices[0].message.content
    try:
        reasoning, score = parse_credibility_response(answer)
    except ValueError:
        # CredibilityScore will become N/A
        return
    
    # Create the object
    CredibilityScore.objects.create(
        listing=instance,
        score=score,
        reasoning=reasoning,
    )