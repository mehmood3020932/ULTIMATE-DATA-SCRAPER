# app/llm/consensus.py
# LLM Consensus - Multiple LLM agreement

from typing import Any, Dict, List


class LLMConsensus:
    """
    Builds consensus across multiple LLM providers.
    """
    
    def __init__(self):
        self.similarity_threshold = 0.8
    
    async def get_consensus(
        self,
        responses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Determine consensus across LLM responses.
        
        Args:
            responses: List of responses from different providers
        
        Returns:
            Consensus result with metadata
        """
        if len(responses) < 2:
            return {
                "consensus": responses[0]["content"] if responses else None,
                "confidence": 1.0 if responses else 0.0,
                "method": "single",
            }
        
        # Extract content
        contents = [r["content"] for r in responses]
        
        # Simple string similarity (in production, use embeddings)
        from difflib import SequenceMatcher
        
        similarities = []
        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                sim = SequenceMatcher(None, contents[i], contents[j]).ratio()
                similarities.append(sim)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Select best response (highest confidence or most common)
        best_response = max(responses, key=lambda x: x.get("confidence", 0.5))
        
        return {
            "consensus": best_response["content"],
            "confidence": avg_similarity,
            "agreement_score": avg_similarity,
            "providers_agreed": len([s for s in similarities if s > 0.7]),
            "method": "similarity",
        }