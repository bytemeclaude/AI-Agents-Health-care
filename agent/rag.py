from utils.logger import get_logger

logger = get_logger(__name__)

class RAGChain:
    def __init__(self):
        logger.info("Initializing Robust Keyword Knowledge Base...")
        self.documents = [
            "Chest Pain Protocol: Immediate ECG. Consider ACS if radiation to arm. RED Priority.",
            "Fever Protocol: If > 40C or immunocompromised, RED. If > 38C and stable, GREEN.",
            "Headache Protocol: Thunderclap onset is RED (Subarachnoid Hemorrhage risk). Tension type is GREEN.",
            "Drug Interaction: Warfarin + Aspirin significantly increases bleeding risk. Monitor PT/INR.",
            "Shortness of Breath: If O2 < 92% or stridor, RED. If asthma history and mild wheeze, YELLOW."
        ]
        logger.info(f"Knowledge Base Indexed ({len(self.documents)} documents).")

    def retrieve(self, query: str, n_results: int = 1) -> list[str]:
        """
        Retrieves documents based on keyword overlap. 
        Simple, robust, and effective for "from scratch" demos.
        """
        query_words = set(query.lower().split())
        scored_docs = []
        
        for doc in self.documents:
            doc_words = set(doc.lower().split())
            # Calculate Jaccard similarity (intersection over union)
            intersection = query_words.intersection(doc_words)
            if not intersection:
                score = 0
            else:
                score = len(intersection) / len(query_words.union(doc_words))
            scored_docs.append((score, doc))
            
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N documents
        return [doc for score, doc in scored_docs[:n_results] if score > 0] or [self.documents[0]]
