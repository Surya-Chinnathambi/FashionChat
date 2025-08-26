import logging
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class SimpleSearchService:
    """Simple text-based search service as a lightweight alternative to ChromaDB"""
    
    def __init__(self):
        """Initialize the simple search service"""
        self.products: List[Dict[str, Any]] = []
        self.indexed_text: Dict[str, Dict[str, Any]] = {}  # product_id -> searchable entry
        logger.info("SimpleSearchService initialized")
    
    def add_products(self, products: List[Dict[str, Any]]) -> None:
        """Add products to the search index"""
        try:
            if not products:
                return
            
            for product in products:
                if "id" not in product:
                    logger.warning("Product missing 'id' field, skipping: %s", product)
                    continue
                
                # Create searchable text for the product
                searchable_text = self._create_searchable_text(product)
                
                # Store product with searchable text
                product_entry = {
                    **product,
                    "_searchable_text": searchable_text.lower(),
                    "_keywords": self._extract_keywords(searchable_text),
                }
                
                # Update or add product
                existing_index = None
                for i, existing_product in enumerate(self.products):
                    if str(existing_product.get("id")) == str(product["id"]):
                        existing_index = i
                        break
                
                if existing_index is not None:
                    self.products[existing_index] = product_entry
                else:
                    self.products.append(product_entry)
                
                # Also keep in indexed_text dict
                self.indexed_text[str(product["id"])] = product_entry
            
            logger.debug("Added/updated %d products in search index", len(products))
            
        except Exception as e:
            logger.error("Error adding products to search index: %s", e, exc_info=True)
            raise
    
    def search_products(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products using text similarity"""
        try:
            if not query.strip():
                return []
            
            query_lower = query.lower()
            results: List[Dict[str, Any]] = []
            
            # Score each product
            for product in self.products:
                score = self._calculate_similarity_score(query_lower, product)
                
                # Apply filters
                if filters and not self._matches_filters(product, filters):
                    continue
                
                if score > 0.1:  # Minimum threshold
                    results.append({
                        **{k: v for k, v in product.items() if not k.startswith("_")},
                        "similarity_score": score,
                        "relevance_rank": 0,  # Will be set after sorting
                    })
            
            # Sort by score
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Set relevance ranks
            for i, result in enumerate(results):
                result["relevance_rank"] = i + 1
            
            # Limit results
            results = results[:limit]
            
            logger.info("Found %d products for query: '%s'", len(results), query)
            return results
            
        except Exception as e:
            logger.error("Error searching products: %s", e, exc_info=True)
            return []
    
    def _create_searchable_text(self, product: Dict[str, Any]) -> str:
        """Create searchable text from product data"""
        parts: List[str] = []
        
        # Core product info
        if product.get("name"):
            parts.append(product["name"])
        if product.get("description"):
            parts.append(product["description"])
        
        # Categorical info
        if product.get("category"):
            parts.append(product["category"])
        if product.get("brand"):
            parts.append(product["brand"])
        
        # Attributes
        if product.get("color"):
            parts.append(product["color"])
        if product.get("size"):
            parts.append(product["size"])
        
        # Tags if available
        if product.get("tags"):
            if isinstance(product["tags"], list):
                parts.extend(product["tags"])
            elif isinstance(product["tags"], dict):
                parts.extend(str(v) for v in product["tags"].values())
            else:
                parts.append(str(product["tags"]))
        
        return " ".join(str(part) for part in parts if part)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        words = re.findall(r"\b\w+\b", text.lower())
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "this", "that", "these", "those",
        }
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_similarity_score(self, query: str, product: Dict[str, Any]) -> float:
        """Calculate similarity score between query and product"""
        searchable_text = product.get("_searchable_text", "")
        keywords = product.get("_keywords", [])
        
        # Direct text match
        if query in searchable_text:
            base_score = 0.8
        else:
            # Use sequence matcher for similarity
            base_score = SequenceMatcher(None, query, searchable_text).ratio()
            
            # Boost for very short queries
            if len(query) <= 3 and base_score < 0.3:
                base_score += 0.25
            elif len(query) <= 5 and base_score < 0.4:
                base_score += 0.15
        
        # Keyword matching bonus
        query_words = set(re.findall(r"\b\w+\b", query.lower()))
        matching_keywords = query_words.intersection(set(keywords))
        keyword_bonus = len(matching_keywords) / max(len(query_words), 1) * 0.3
        
        # Category/brand/color exact match bonus
        exact_match_bonus = 0
        if query in (product.get("category", "").lower()):
            exact_match_bonus += 0.4
        if query in (product.get("brand", "").lower()):
            exact_match_bonus += 0.3
        if query in (product.get("color", "").lower()):
            exact_match_bonus += 0.2
        
        # Product name exact match
        if query in (product.get("name", "").lower()):
            exact_match_bonus += 0.5
        
        total_score = min(base_score + keyword_bonus + exact_match_bonus, 1.0)
        return total_score
    
    def _matches_filters(self, product: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if product matches the given filters"""
        try:
            if filters.get("category"):
                if product.get("category", "").lower() != filters["category"].lower():
                    return False
            
            if filters.get("color"):
                if product.get("color", "").lower() != filters["color"].lower():
                    return False
            
            if filters.get("brand"):
                if product.get("brand", "").lower() != filters["brand"].lower():
                    return False
            
            if filters.get("min_price") is not None:
                if product.get("price", 0) < filters["min_price"]:
                    return False
            
            if filters.get("max_price") is not None:
                if product.get("price", float("inf")) > filters["max_price"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Error checking filters: %s", e, exc_info=True)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index"""
        return {
            "total_products": len(self.products),
            "search_type": "simple_text_search",
        }
    
    def delete_product(self, product_id: Any) -> None:
        """Delete a product from the search index"""
        try:
            self.products = [p for p in self.products if str(p.get("id")) != str(product_id)]
            self.indexed_text.pop(str(product_id), None)
            logger.info("Deleted product %s from search index", product_id)
        except Exception as e:
            logger.error("Error deleting product %s: %s", product_id, e, exc_info=True)
