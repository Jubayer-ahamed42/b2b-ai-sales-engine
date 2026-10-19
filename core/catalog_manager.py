#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
catalog_manager.py — Multi-Tenant Store & Product Catalog Engine
Manages stores, product inventories, and dynamic client onboarding.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
STORES_FILE = BASE_DIR / "catalogs" / "stores.json"

class CatalogManager:
    def __init__(self, stores_file: Path = STORES_FILE):
        self.stores_file = stores_file
        self.stores_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.stores_file.exists():
            self._save_stores({})

    def load_stores(self) -> Dict[str, Any]:
        """Loads all store configurations."""
        try:
            with open(self.stores_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("stores", {})
        except Exception:
            return {}

    def _save_stores(self, stores: Dict[str, Any]) -> bool:
        """Saves store configurations to JSON file."""
        try:
            with open(self.stores_file, "w", encoding="utf-8") as f:
                json.dump({"stores": stores}, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get_store(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a store by ID."""
        stores = self.load_stores()
        return stores.get(store_id) or stores.get("fashion_boutique")

    def list_stores(self) -> List[Dict[str, Any]]:
        """Returns lightweight list of stores for UI selection."""
        stores = self.load_stores()
        store_list = []
        for s_id, s_data in stores.items():
            store_list.append({
                "id": s_id,
                "name": s_data.get("name", s_id),
                "category": s_data.get("category", ""),
                "tagline": s_data.get("tagline", ""),
                "avatar": s_data.get("avatar", "🛍️"),
                "brand_color": s_data.get("brand_color", "#4f46e5"),
                "product_count": len(s_data.get("products", []))
            })
        return store_list

    def add_store(self, store_data: Dict[str, Any]) -> str:
        """Dynamically adds or updates a client store."""
        stores = self.load_stores()
        store_id = store_data.get("id") or store_data.get("name", "").lower().replace(" ", "_")
        store_data["id"] = store_id
        stores[store_id] = store_data
        self._save_stores(stores)
        return store_id
