"""
AI Agent for consolidating similar topics to maintain high recall using Gemini
"""
import google.generativeai as genai
import json
import os
from typing import List, Dict, Set
from dotenv import load_dotenv

load_dotenv()


class TopicConsolidator:
    def __init__(self):
        """
        Initialize the topic consolidator agent
        """
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel(
            os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        )
        self.topic_mapping = {}  # Maps variant topics to canonical topics
        self.canonical_topics = set()  # Set of canonical topic names

        # Generation config for consistent output
        self.generation_config = {
            'temperature': float(os.getenv('TEMPERATURE', '0.3')),  # Lower temp for consistency
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': int(os.getenv('MAX_OUTPUT_TOKENS', '8192')),
        }

    def consolidate_topics(self, new_topics: Set[str]) -> Dict[str, str]:
        """
        Consolidate new topics with existing canonical topics using agentic reasoning

        Args:
            new_topics: Set of newly extracted topics

        Returns:
            Dictionary mapping each new topic to its canonical form
        """
        if not new_topics:
            return {}

        mapping = {}

        # If we have no canonical topics yet, process all at once
        if not self.canonical_topics:
            mapping = self._create_initial_taxonomy(list(new_topics))
            self._update_taxonomy(mapping)
            return mapping

        # Otherwise, map new topics to existing canonical topics using agent reasoning
        for topic in new_topics:
            # Check if already mapped
            if topic in self.topic_mapping:
                mapping[topic] = self.topic_mapping[topic]
            else:
                # Find canonical topic for this new topic
                canonical = self._find_canonical_topic(topic)
                mapping[topic] = canonical
                self.topic_mapping[topic] = canonical
                self.canonical_topics.add(canonical)

        return mapping

    def _create_initial_taxonomy(self, topics: List[str]) -> Dict[str, str]:
        """
        Create initial taxonomy from first batch of topics with agentic reasoning
        """
        if not topics:
            return {}

        prompt = f"""You are an expert AI agent specialized in creating consistent topic taxonomies for app reviews. Your task is to act as an intelligent agent that:
1. Analyzes all topics to understand their semantic meaning
2. Identifies topics that refer to the same underlying issue/request
3. Reasons about which topics should be merged
4. Decides on clear canonical names for merged topics

AGENTIC REASONING PROCESS:
- For each topic, understand what issue/request it represents
- Compare topics semantically (not just lexically)
- Group topics that discuss the same problem (e.g., "delivery guy rude", "delivery partner impolite", "rude delivery person" all mean the same)
- Choose the clearest canonical name for each group
- Be conservative - only merge topics that clearly mean the same thing

CRITICAL RULES:
1. Merge topics that refer to the same issue/request (e.g., "Delivery guy rude", "Delivery partner behaved badly" → "Delivery partner rude")
2. Use clear, concise canonical names that product teams understand
3. Be conservative - only merge topics that are CLEARLY the same
4. Preserve important distinctions (e.g., "Food cold" vs "Food stale" are different issues)
5. Use consistent terminology (prefer "Delivery partner" over "Delivery guy")

REASONING EXAMPLE:
Topics: ["Delivery guy was rude", "Delivery partner behaved badly", "Food arrived cold"]
Agent reasoning:
- "Delivery guy was rude" and "Delivery partner behaved badly" both describe delivery partner behavior issues → Merge to "Delivery partner rude"
- "Food arrived cold" is a different issue about food temperature → Keep as "Food cold"
Decision: Create 2 canonical topics

Topics to consolidate:
{chr(10).join(f"- {topic}" for topic in topics)}

Respond with ONLY a JSON object mapping each original topic to its canonical form:
{{
  "original topic 1": "canonical topic 1",
  "original topic 2": "canonical topic 1",
  "original topic 3": "canonical topic 2",
  ...
}}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            response_text = response.text.strip()

            # Clean JSON formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            mapping = json.loads(response_text)
            return mapping

        except Exception as e:
            print(f"Error in initial taxonomy creation: {e}")
            # Return identity mapping on error
            return {topic: topic for topic in topics}

    def _find_canonical_topic(self, new_topic: str) -> str:
        """
        Find the canonical topic for a new topic using agentic reasoning
        """
        if not self.canonical_topics:
            return new_topic

        canonical_list = list(self.canonical_topics)

        prompt = f"""You are an expert AI agent for topic consolidation and taxonomy management.

AGENTIC TASK:
Given a new topic and existing canonical topics, you must:
1. Analyze the semantic meaning of the new topic
2. Compare it against all existing canonical topics
3. Reason about whether it matches any existing topic
4. Make a decision: merge with existing OR create new canonical topic

REASONING PROCESS:
- Understand what issue/request the new topic represents
- For each existing canonical topic, ask: "Do these refer to the same underlying issue?"
- Consider variations in wording but same meaning (e.g., "rude" vs "impolite" vs "behaved badly")
- Be conservative - only match if they CLEARLY mean the same thing
- If no clear match, the new topic becomes a new canonical topic

CRITICAL RULES:
1. Match only if the topics clearly refer to the same issue/request
2. Consider semantic similarity, not just word overlap
3. When in doubt, create a new canonical topic (better to have separate topics than incorrect merging)
4. Preserve important distinctions

DECISION EXAMPLES:
Example 1:
New: "Delivery person was impolite"
Existing: ["Delivery partner rude", "Food cold"]
Reasoning: "Impolite" and "rude" describe the same behavior issue → MATCH
Decision: "Delivery partner rude"

Example 2:
New: "App is slow"
Existing: ["App crashes", "Payment failed"]
Reasoning: "Slow" is different from "crashes" (performance vs stability) → NO MATCH
Decision: "App is slow" (new canonical topic)

New topic: "{new_topic}"

Existing canonical topics:
{chr(10).join(f"- {topic}" for topic in canonical_list)}

Respond with ONLY the canonical topic name (either an existing one or the new topic as-is). Do not include any explanation, just the topic name:"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            canonical = response.text.strip().strip('"\'')

            # Validate the response is one of the canonical topics or the new topic
            if canonical in self.canonical_topics or canonical == new_topic:
                return canonical
            else:
                # If AI returned something unexpected, default to new topic
                print(f"Warning: Unexpected canonical topic '{canonical}', using new topic '{new_topic}'")
                return new_topic

        except Exception as e:
            print(f"Error finding canonical topic: {e}")
            return new_topic

    def _update_taxonomy(self, mapping: Dict[str, str]):
        """
        Update internal taxonomy with new mappings
        """
        for original, canonical in mapping.items():
            self.topic_mapping[original] = canonical
            self.canonical_topics.add(canonical)

    def apply_mapping(self, extraction_results: List[Dict]) -> List[Dict]:
        """
        Apply topic mapping to extraction results

        Args:
            extraction_results: Results from TopicExtractor

        Returns:
            Results with topics mapped to canonical forms
        """
        mapped_results = []

        for result in extraction_results:
            mapped_topics = [
                self.topic_mapping.get(topic, topic)
                for topic in result['topics']
            ]

            mapped_results.append({
                'review_id': result['review_id'],
                'topics': mapped_topics,
                'content': result.get('content', ''),
                'reasoning': result.get('reasoning', '')
            })

        return mapped_results

    def get_topic_mapping(self) -> Dict[str, str]:
        """Get the current topic mapping dictionary"""
        return self.topic_mapping.copy()

    def get_canonical_topics(self) -> Set[str]:
        """Get the set of canonical topics"""
        return self.canonical_topics.copy()