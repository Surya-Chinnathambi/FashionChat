import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from difflib import SequenceMatcher
import os

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb

# optional SQLAlchemy imports if you pass a DB session
from sqlalchemy.orm import Session
from sqlalchemy import func

# import your Product model if you want DB-backed results
try:
    from models import Product
except Exception:
    Product = None  # graceful if models are unavailable in some contexts

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Advanced HybridSearchService (backwards-compatible)
    - Primary: ChromaDB semantic search
    - Secondary: Postgres authoritative fetch & filter (if db_session supplied)
    - Tertiary: In-memory search fallback
    API kept identical:
      - add_products(products: List[Dict])
      - search_products(query: str, filters: Optional[Dict]=None, limit: int=10) -> List[Dict]
      - get_stats()
      - delete_product(product_id)
    Constructor accepts optional db_session (SQLAlchemy Session) to enable Postgres joins/filters.
    """

    def __init__(self, use_embeddings: bool = True, db_session: Optional[Session] = None):
        self.use_embeddings = use_embeddings
        self.db_session: Optional[Session] = db_session

        # in-memory store
        self.products: List[Dict[str, Any]] = []
        self.indexed_text: Dict[str, Dict[str, Any]] = {}

        # embedding model
        if self.use_embeddings:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("✅ Initialized MiniLM-L6 semantic embeddings")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load embeddings, disabling: {e}")
                self.model = None
                self.use_embeddings = False
        else:
            self.model = None

        # chroma connection params via env
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", 8005))

        self.chroma_client = None
        self.chroma_collection = None
        try:
            # using HTTP client to match your previous code (works with Docker HTTP API)
            self.chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            # get_or_create collection 'products' (metadata and embeddings expected)
            self.chroma_collection = self.chroma_client.get_or_create_collection("products")
            logger.info(f"✅ Connected to ChromaDB at {chroma_host}:{chroma_port}")
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to ChromaDB, falling back to in-memory: {e}")
            self.chroma_client = None
            self.chroma_collection = None

        logger.info("HybridSearchService initialized")

    # ---------------------- PRODUCT LOADING ----------------------
    def add_products(self, products: List[Dict[str, Any]]) -> None:
        """Add products to both ChromaDB (if available) and in-memory index"""
        if not products:
            return

        for product in products:
            if "id" not in product:
                logger.warning("Product missing 'id' field, skipping: %s", product)
                continue

            searchable_text = self._create_searchable_text(product)
            embedding_vector = None
            if self.use_embeddings and self.model:
                try:
                    embedding_vector = self.model.encode([searchable_text], normalize_embeddings=True)[0].tolist()
                except Exception as e:
                    logger.error("Embedding generation failed for product %s: %s", product.get("id"), e)
                    embedding_vector = None

            # --- In-memory index (store enriched product) ---
            product_entry = {
                **product,
                "_searchable_text": searchable_text.lower(),
                "_keywords": self._extract_keywords(searchable_text),
                "_embedding": embedding_vector,
            }

            # update or append
            existing_index = None
            for i, existing_product in enumerate(self.products):
                if str(existing_product.get("id")) == str(product["id"]):
                    existing_index = i
                    break
            if existing_index is not None:
                self.products[existing_index] = product_entry
            else:
                self.products.append(product_entry)

            self.indexed_text[str(product["id"])] = product_entry

            # --- Chroma Index (if connected and embedding present) ---
            if self.chroma_collection and embedding_vector:
                try:
                    # store whole product as metadata so we can read authoritative fields if DB is not available
                    self.chroma_collection.upsert(
                        ids=[str(product["id"])],
                        documents=[searchable_text],
                        metadatas=[product],
                        embeddings=[embedding_vector]
                    )
                except Exception as e:
                    logger.warning("⚠️ Failed to upsert product %s into Chroma: %s", product["id"], e)

        logger.info("✅ Added/updated %d products", len(products))

    # ---------------------- SEARCH ----------------------
    def search_products(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search
         1. Try Chroma (semantic recall) => candidate ids
         2. If db_session available: fetch Product rows for those ids and apply filters (authoritative)
            else use Chroma metadatas or in-memory entries
         3. If Chroma unavailable or returns no results, fallback to in-memory search
        Returns list of product dicts (fields consistent with Product model or metadata)
        """
        if not query or not query.strip():
            return []

        filters = filters or {}

        # --- step 0: compute query embedding if possible ---
        query_embedding = None
        if self.use_embeddings and self.model:
            try:
                query_embedding = self.model.encode([query], normalize_embeddings=True)[0].tolist()
            except Exception as e:
                logger.error("Query embedding failed: %s", e)
                query_embedding = None
                # degrade gracefully: keep use_embeddings flag but avoid embedding path
                self.use_embeddings = False

        # --- step 1: try chroma candidates ---
        chroma_candidate_ids: List[str] = []
        chroma_scores_map: Dict[str, float] = {}
        chroma_metadatas: Dict[str, Dict[str, Any]] = {}

        if self.chroma_collection and query_embedding:
            try:
                res = self.chroma_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max(limit * 3, 24),
                    include=["distances", "metadatas"]  # ✅ FIXED: removed "ids"
                )
                ids_list = res.get("ids", [[]])[0]
                distances = res.get("distances", [[]])[0]
                metadatas = res.get("metadatas", [[]])[0] if res.get("metadatas") else [None] * len(ids_list)

                for i, raw_id in enumerate(ids_list):
                    pid = str(raw_id)
                    chroma_candidate_ids.append(pid)
                    # convert distance -> similarity (safe)
                    try:
                        dist = float(distances[i])
                        sim = max(0.0, 1.0 - dist)
                    except Exception:
                        sim = 0.0
                    chroma_scores_map[pid] = sim
                    if i < len(metadatas):
                        chroma_metadatas[pid] = metadatas[i] or {}
                logger.info("✅ Chroma returned %d candidates", len(chroma_candidate_ids))
            except Exception as e:
                logger.warning("⚠️ Chroma query failed, falling back: %s", e)
                chroma_candidate_ids = []
                chroma_scores_map = {}
                chroma_metadatas = {}


        # --- step 2: If we have chroma ids and a DB session, fetch authoritative rows and apply filters ---
        final_results: List[Dict[str, Any]] = []
        seen_ids: Set[str] = set()

        if chroma_candidate_ids and self.db_session and Product is not None:
            try:
                # convert candidate id strings to integers where possible
                candidate_int_ids = [int(pid) for pid in chroma_candidate_ids if str(pid).isdigit()]

                # Build SQL query with IN candidate set and apply filters (authoritative)
                q = self.db_session.query(Product).filter(Product.id.in_(candidate_int_ids))

                # apply filters (category, brand, color, price range, size)
                if filters.get("category"):
                    q = q.filter(func.lower(Product.category).ilike(f"%{filters['category'].lower()}%"))
                if filters.get("brand"):
                    q = q.filter(func.lower(Product.brand).ilike(f"%{filters['brand'].lower()}%"))
                if filters.get("color"):
                    q = q.filter(func.lower(Product.color).ilike(f"%{filters['color'].lower()}%"))
                if filters.get("size"):
                    q = q.filter(func.lower(Product.size).ilike(f"%{filters['size'].lower()}%"))
                if filters.get("min_price") is not None:
                    q = q.filter(Product.price >= float(filters["min_price"]))
                if filters.get("max_price") is not None:
                    q = q.filter(Product.price <= float(filters["max_price"]))

                # Keep Chroma ranking order using CASE by mapping id->position
                # Simple approach: fetch all then order in Python by chroma order
                rows = q.all()
                id_to_row = {str(r.id): r for r in rows}
                for pid in chroma_candidate_ids:
                    if pid in id_to_row:
                        r = id_to_row[pid]
                        final_results.append(self._product_row_to_dict(r, chroma_scores_map.get(pid)))
                        seen_ids.add(pid)

                logger.info("✅ Postgres returned %d filtered candidates from Chroma set", len(final_results))
            except Exception as e:
                logger.error("Error fetching products from Postgres: %s", e, exc_info=True)

        # --- step 3: If we have chroma ids but no DB session, use chroma metadata (or fall back to in-memory) ---
        if chroma_candidate_ids and not final_results:
            for pid in chroma_candidate_ids:
                if pid in seen_ids:
                    continue
                meta = chroma_metadatas.get(pid) or {}
                # if meta has expected fields, include; otherwise skip and leave to in-memory
                product_repr = self._metadata_to_product_dict(pid, meta, chroma_scores_map.get(pid))
                final_results.append(product_repr)
                seen_ids.add(pid)

            if final_results:
                logger.info("✅ Using Chroma metadatas to build product results (no DB session).")

        # --- step 4: If still empty or not enough results, run in-memory fallback (or DB LIKE search if db_session available) ---
        if (not final_results) or (len(final_results) < limit):
            needed = limit - len(final_results)
            fallback_results = []

            # Prefer DB-backed text search (ILIKE on name/description) if DB is available
            if self.db_session and Product is not None:
                try:
                    q = self.db_session.query(Product).filter(Product.is_active.is_(True))
                    # apply same filters
                    if filters.get("category"):
                        q = q.filter(func.lower(Product.category).ilike(f"%{filters['category'].lower()}%"))
                    if filters.get("brand"):
                        q = q.filter(func.lower(Product.brand).ilike(f"%{filters['brand'].lower()}%"))
                    if filters.get("color"):
                        q = q.filter(func.lower(Product.color).ilike(f"%{filters['color'].lower()}%"))
                    if filters.get("min_price") is not None:
                        q = q.filter(Product.price >= float(filters["min_price"]))
                    if filters.get("max_price") is not None:
                        q = q.filter(Product.price <= float(filters["max_price"]))

                    # lightweight ILIKE on name/description using query tokens
                    tokens = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
                    if tokens:
                        ilike_clauses = []
                        for t in tokens:
                            pattern = f"%{t}%"
                            ilike_clauses.append(func.lower(Product.name).ilike(pattern))
                            ilike_clauses.append(func.lower(Product.description).ilike(pattern))
                        # combine OR
                        from sqlalchemy import or_
                        q = q.filter(or_(*ilike_clauses))

                    # exclude already seen ids
                    if seen_ids:
                        exclude_ints = [int(x) for x in seen_ids if str(x).isdigit()]
                        if exclude_ints:
                            q = q.filter(~Product.id.in_(exclude_ints))

                    rows = q.limit(needed).all()
                    for r in rows:
                        fallback_results.append(self._product_row_to_dict(r, None))
                        seen_ids.add(str(r.id))
                    if fallback_results:
                        logger.info("✅ DB backfill returned %d rows", len(fallback_results))
                except Exception as e:
                    logger.warning("DB backfill failed: %s", e)

            # If DB backfill didn't provide enough, run in-memory fallback
            if len(fallback_results) < needed:
                in_memory_needed = needed - len(fallback_results)
                mem = self._in_memory_search(query, filters, limit=in_memory_needed, exclude_ids=seen_ids)
                fallback_results.extend(mem)
                if mem:
                    logger.info("✅ In-memory fallback returned %d rows", len(mem))

            final_results.extend(fallback_results)

        # --- step 5: final ranking and trimming ---
        # Try to sort by similarity_score (higher better). Note: Chroma returned similarity in [0..1] if computed earlier.
        def score_key(item: Dict[str, Any]) -> float:
            s = item.get("similarity_score")
            try:
                if s is None:
                    return 0.0
                return float(s)
            except Exception:
                return 0.0

        final_results.sort(key=score_key, reverse=True)

        # Ensure consistent shape: convert ids to str/int as original code expected
        return final_results[:limit]

    # ---------------------- HELPERS ----------------------
    def _create_searchable_text(self, product: Dict[str, Any]) -> str:
        parts: List[str] = []
        for key in ["name", "description", "category", "brand", "color", "size"]:
            if product.get(key):
                parts.append(str(product[key]))
        if product.get("tags"):
            if isinstance(product["tags"], list):
                parts.extend(product["tags"])
            elif isinstance(product["tags"], dict):
                parts.extend(str(v) for v in product["tags"].values())
            else:
                parts.append(str(product["tags"]))
        return " ".join(parts)

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r"\b\w+\b", text.lower())
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "this", "that", "these", "those",
        }
        return list(set([w for w in words if w not in stop_words and len(w) > 2]))

    def _calculate_similarity_score(self, query: str, product: Dict[str, Any]) -> float:
        searchable_text = product.get("_searchable_text", "")
        keywords = product.get("_keywords", [])
        if query in searchable_text:
            base_score = 0.8
        else:
            base_score = SequenceMatcher(None, query, searchable_text).ratio()
            if len(query) <= 3 and base_score < 0.3:
                base_score += 0.25
            elif len(query) <= 5 and base_score < 0.4:
                base_score += 0.15

        query_words = set(re.findall(r"\b\w+\b", query.lower()))
        matching_keywords = query_words.intersection(set(keywords))
        keyword_bonus = len(matching_keywords) / max(len(query_words), 1) * 0.3

        exact_match_bonus = 0
        if query in (product.get("category", "").lower()):
            exact_match_bonus += 0.4
        if query in (product.get("brand", "").lower()):
            exact_match_bonus += 0.3
        if query in (product.get("color", "").lower()):
            exact_match_bonus += 0.2
        if query in (product.get("name", "").lower()):
            exact_match_bonus += 0.5

        return min(base_score + keyword_bonus + exact_match_bonus, 1.0)

    def _matches_filters(self, product: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        try:
            if filters.get("category") and filters["category"].lower() not in product.get("category", "").lower():
                return False
            if filters.get("color") and filters["color"].lower() not in product.get("color", "").lower():
                return False
            if filters.get("brand") and filters["brand"].lower() not in product.get("brand", "").lower():
                return False
            if filters.get("min_price") is not None and product.get("price", 0) < filters["min_price"]:
                return False
            if filters.get("max_price") is not None and product.get("price", float("inf")) > filters["max_price"]:
                return False
            return True
        except Exception as e:
            logger.error("Filter check failed: %s", e)
            return False

    def _in_memory_search(self, query: str, filters: Dict[str, Any], limit: int = 10, exclude_ids: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """Run local in-memory search (existing behavior) and respect exclude_ids"""
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        exclude_ids = exclude_ids or set()

        for product in self.products:
            pid = str(product.get("id"))
            if pid in exclude_ids:
                continue

            base_score = 0.0
            if self.use_embeddings and product.get("_embedding") is not None and self.model:
                try:
                    prod_vec = np.array(product["_embedding"])
                    q_vec = np.array(self.model.encode([query], normalize_embeddings=True)[0])
                    denom = (np.linalg.norm(prod_vec) * np.linalg.norm(q_vec))
                    similarity = float(np.dot(prod_vec, q_vec) / denom) if denom > 0 else 0.0
                    base_score = similarity
                except Exception:
                    base_score = self._calculate_similarity_score(query_lower, product)
            else:
                base_score = self._calculate_similarity_score(query_lower, product)

            if filters and not self._matches_filters(product, filters):
                continue

            if (self.use_embeddings and base_score > 0.3) or (not self.use_embeddings and base_score > 0.2):
                results.append({
                    **{k: v for k, v in product.items() if not k.startswith("_")},
                    "similarity_score": base_score,
                })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]

    def _product_row_to_dict(self, row: Any, similarity_score: Optional[float]) -> Dict[str, Any]:
        """Convert SQLAlchemy Product row to dict shape used by the service"""
        try:
            return {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "price": float(row.price) if row.price is not None else None,
                "category": row.category,
                "color": row.color,
                "size": row.size,
                "brand": row.brand,
                "image_url": getattr(row, "image_url", None),
                "stock_quantity": getattr(row, "stock_quantity", None),
                "tags": getattr(row, "tags", None),
                "created_at": getattr(row, "created_at", None),
                "is_active": getattr(row, "is_active", True),
                "similarity_score": similarity_score,
            }
        except Exception as e:
            logger.error("Failed to convert product row to dict: %s", e)
            return {}

    def _metadata_to_product_dict(self, pid: str, meta: Dict[str, Any], similarity_score: Optional[float]) -> Dict[str, Any]:
        """Convert Chroma metadata into product-like dict"""
        try:
            product = {
                "id": int(pid) if str(pid).isdigit() else pid,
                "name": meta.get("name") or meta.get("title") or None,
                "description": meta.get("description") or None,
                "price": float(meta["price"]) if meta.get("price") is not None else None,
                "category": meta.get("category"),
                "color": meta.get("color"),
                "size": meta.get("size"),
                "brand": meta.get("brand"),
                "image_url": meta.get("image_url"),
                "stock_quantity": meta.get("stock_quantity"),
                "tags": meta.get("tags"),
                "created_at": meta.get("created_at"),
                "is_active": meta.get("is_active", True),
                "similarity_score": similarity_score,
            }
            return product
        except Exception as e:
            logger.error("Failed to convert metadata to dict: %s", e)
            return {"id": pid, "similarity_score": similarity_score}

    # ---------------------- MANAGEMENT ----------------------
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_products": len(self.products),
            "search_type": "hybrid (Chroma + Postgres + in-memory)" if self.use_embeddings else "simple_text_search",
            "chroma_enabled": self.chroma_collection is not None,
            "db_enabled": self.db_session is not None and Product is not None,
        }

    def delete_product(self, product_id: Any) -> None:
        """Delete product from in-memory index and Chroma (if connected)"""
        self.products = [p for p in self.products if str(p.get("id")) != str(product_id)]
        self.indexed_text.pop(str(product_id), None)
        if self.chroma_collection:
            try:
                self.chroma_collection.delete(ids=[str(product_id)])
            except Exception as e:
                logger.warning("⚠️ Failed to delete product %s from Chroma: %s", product_id, e)
        logger.info("🗑️ Deleted product %s", product_id)
