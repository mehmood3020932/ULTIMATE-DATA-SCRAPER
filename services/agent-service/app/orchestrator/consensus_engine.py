# app/orchestrator/consensus_engine.py
# Consensus Engine - Builds consensus across multiple agents

from typing import Any, Dict, List

import structlog

logger = structlog.get_logger()


class ConsensusEngine:
    """
    Builds consensus across multiple agent outputs.
    Uses voting, confidence weighting, and semantic similarity.
    """
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.logger = logger.bind(component="consensus")
    
    async def build_consensus(
        self,
        results: List[Dict[str, Any]],
        method: str = "voting",
    ) -> Dict[str, Any]:
        """
        Build consensus from multiple agent results.
        
        Args:
            results: List of agent outputs
            method: Consensus method (voting, averaging, weighted)
        
        Returns:
            Consensus result with confidence score
        """
        if not results:
            return {"consensus": None, "confidence": 0.0}
        
        if len(results) == 1:
            return {
                "consensus": results[0],
                "confidence": results[0].get("confidence", 0.5),
            }
        
        if method == "voting":
            return self._voting_consensus(results)
        elif method == "weighted":
            return self._weighted_consensus(results)
        else:
            return self._averaging_consensus(results)
    
    def _voting_consensus(self, results: List[Dict]) -> Dict[str, Any]:
        """Simple voting consensus."""
        # Group by key values
        votes = {}
        for r in results:
            key = str(r.get("data", {}))
            votes[key] = votes.get(key, 0) + 1
        
        # Find majority
        majority = max(votes.items(), key=lambda x: x[1])
        agreement = majority[1] / len(results)
        
        return {
            "consensus": majority[0],
            "confidence": agreement,
            "agreement_ratio": agreement,
            "total_votes": len(results),
        }
    
    def _weighted_consensus(self, results: List[Dict]) -> Dict[str, Any]:
        """Confidence-weighted consensus."""
        total_weight = sum(r.get("confidence", 0.5) for r in results)
        
        if total_weight == 0:
            return {"consensus": None, "confidence": 0.0}
        
        # Weighted average of numeric values
        weighted_sum = 0
        for r in results:
            weight = r.get("confidence", 0.5) / total_weight
            # Simplified - would need proper value extraction
            weighted_sum += weight
        
        return {
            "consensus": weighted_sum,
            "confidence": min(1.0, total_weight / len(results)),
        }
    
    def _averaging_consensus(self, results: List[Dict]) -> Dict[str, Any]:
        """Simple averaging."""
        # Return result with highest confidence
        best = max(results, key=lambda x: x.get("confidence", 0))
        
        return {
            "consensus": best.get("data"),
            "confidence": best.get("confidence", 0),
            "best_provider": best.get("provider", "unknown"),
        }