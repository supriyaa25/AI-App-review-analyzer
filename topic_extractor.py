"""
AI Agent for extracting topics from reviews using Gemini
"""
import google.generativeai as genai
import json
import os
from typing import List, Dict, Set
from dotenv import load_dotenv

load_dotenv()


class TopicExtractor:
    def __init__(self, seed_topics: List[str] = None):
        """
        Initialize the topic extractor agent

        Args:
            seed_topics: Optional list of seed topics to guide extraction
        """
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel(
            os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        )
        self.seed_topics = seed_topics or []

        # Generation config for consistent output
        self.generation_config = {
            'temperature': float(os.getenv('TEMPERATURE', '0.7')),
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': int(os.getenv('MAX_OUTPUT_TOKENS', '8192')),
        }

    def extract_topics_from_batch(self, reviews: List[Dict]) -> List[Dict]:
        """
        Extract topics from a batch of reviews using AI agent

        Args:
            reviews: List of review dictionaries with 'content' field

        Returns:
            List of dictionaries with review_id and extracted topics
        """
        if not reviews:
            return []

        # Process in smaller chunks to avoid token limits
        chunk_size = 30
        all_results = []

        for i in range(0, len(reviews), chunk_size):
            chunk = reviews[i:i + chunk_size]
            results = self._process_chunk(chunk)
            all_results.extend(results)

        return all_results

    def _process_chunk(self, reviews: List[Dict]) -> List[Dict]:
        """Process a chunk of reviews with agentic reasoning"""

        # Prepare the prompt with agentic instructions
        reviews_text = ""
        for idx, review in enumerate(reviews):
            reviews_text += f"Review {idx + 1}: {review['content']}\n\n"

        seed_topics_text = ""
        if self.seed_topics:
            seed_topics_text = f"\n\nSeed topics for reference (you can use these or create new ones based on your analysis):\n" + "\n".join(f"- {topic}" for topic in self.seed_topics)

        prompt = f"""You are an expert AI agent specialized in analyzing app reviews. Your task is to act as an intelligent agent that:
1. Carefully reads and understands each review
2. Identifies actionable topics (issues, requests, feedback)
3. Reasons about topic categorization
4. Makes decisions about topic naming consistency

AGENTIC REASONING PROCESS:
- Think step-by-step about what each review is discussing
- Consider the user's intent and emotion
- Decide if this is an issue, feature request, or feedback
- Choose clear, consistent topic names that product teams can act on

GUIDELINES:
1. Extract topics that represent issues, feature requests, complaints, or feedback
2. Be specific but concise (e.g., "Delivery partner rude" not just "delivery")
3. Use consistent naming conventions (always use the same term for similar concepts)
4. One review can have multiple topics
5. If a review has no clear actionable topic, return an empty list for that review
6. Focus on topics that are actionable for product/engineering teams{seed_topics_text}

REASONING EXAMPLE:
Review: "The delivery guy was extremely rude and the food arrived cold"
Agent reasoning: This review mentions two distinct issues:
- Issue 1: Delivery partner behavior → Topic: "Delivery partner rude"
- Issue 2: Food temperature → Topic: "Food cold"
Decision: Extract both topics

Reviews to analyze:
{reviews_text}

Respond with ONLY a JSON array where each element corresponds to a review (in order) and contains the topics found:
[
  {{"review_index": 1, "topics": ["topic1", "topic2"], "reasoning": "brief reason"}},
  {{"review_index": 2, "topics": ["topic3"], "reasoning": "brief reason"}},
  ...
]"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            response_text = response.text.strip()

            # Parse JSON response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            results = json.loads(response_text)

            # Match results back to review IDs
            output = []
            for i, review in enumerate(reviews):
                matching_result = next((r for r in results if r['review_index'] == i + 1), None)
                if matching_result:
                    output.append({
                        'review_id': review.get('reviewId', f"review_{i}"),
                        'topics': matching_result['topics'],
                        'content': review['content'],
                        'reasoning': matching_result.get('reasoning', '')
                    })

            return output

        except Exception as e:
            print(f"Error in topic extraction: {e}")
            # Return empty topics on error
            return [{'review_id': review.get('reviewId', f"review_{i}"), 'topics': [], 'content': review['content'], 'reasoning': 'error'}
                    for i, review in enumerate(reviews)]

    def get_all_unique_topics(self, extraction_results: List[Dict]) -> Set[str]:
        """
        Get all unique topics from extraction results

        Args:
            extraction_results: Results from extract_topics_from_batch

        Returns:
            Set of unique topic strings
        """
        all_topics = set()
        for result in extraction_results:
            all_topics.update(result['topics'])
        return all_topics