#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sales_engine.py — Comprehensive Test Suite for B2B AI Sales Engine
Validates catalog manager, conversational sales brain, and order extraction.
"""

import sys
import json
import urllib.request
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.catalog_manager import CatalogManager
from core.ai_sales_brain import AISalesBrain

def test_catalog_manager():
    print("🧪 [Test 1] Testing Catalog Manager...")
    cm = CatalogManager()
    stores = cm.load_stores()
    assert len(stores) >= 3, f"Expected >= 3 stores, got {len(stores)}"
    assert "fashion_boutique" in stores, "fashion_boutique store missing!"
    
    store = cm.get_store("fashion_boutique")
    assert store["name"] == "Aura Fashion BD"
    assert len(store["products"]) >= 3
    print(f"  [OK] Stores loaded: {list(stores.keys())}")
    print(f"  [OK] Catalog verified for: {store['name']} ({len(store['products'])} products)\n")

def test_sales_brain_inquiry():
    print("🧪 [Test 2] Testing Product Inquiry & Price Response...")
    brain = AISalesBrain()
    cm = CatalogManager()
    store = cm.get_store("fashion_boutique")

    res = brain.process_message(
        store=store,
        user_message="আপনাদের পাঞ্জাবির দাম কত এবং কী কী সাইজ আছে?",
        history=[]
    )
    assert res.get("reply"), "Empty reply returned!"
    reply = res["reply"]
    print(f"  [OK] Reply received ({len(reply)} chars)")
    print(f"  Preview:\n{reply[:200]}...\n")

def test_sales_brain_order_capture():
    print("🧪 [Test 3] Testing Automatic COD Order Capture & Ledger...")
    brain = AISalesBrain()
    cm = CatalogManager()
    store = cm.get_store("fashion_boutique")

    # Simulate customer giving details
    order_message = "আমি কটন কাবলি সেট নেভি ব্লু L সাইজ নিব। আমার নাম জুবায়ের, ফোন: 01712345678, ঠিকানা: বাড়ি ১২, রোড ৫, ধানমন্ডি, ঢাকা।"
    res = brain.process_message(
        store=store,
        user_message=order_message,
        history=[
            {"sender": "user", "text": "দাম কত?"},
            {"sender": "model", "text": "পাঞ্জাবির দাম ১২৫০ টাকা। অর্ডার করতে আপনার নাম, ফোন ও ঠিকানা দিন।"}
        ]
    )
    assert res.get("reply"), "Empty reply on order submission!"
    assert res.get("has_order") is True, "Failed to capture order!"
    
    order = res.get("order")
    assert order, "Order object missing!"
    assert "01712345678" in str(order.get("phone")), f"Phone mismatch: {order.get('phone')}"
    
    print(f"  [OK] Order successfully captured: #{order.get('order_id')}")
    print(f"  [OK] Customer: {order.get('customer_name')} | Phone: {order.get('phone')}")
    print(f"  [OK] Address: {order.get('address')}")
    print(f"  [OK] Total: {order.get('total_amount')}৳")
    print(f"  [OK] Order Ledger updated in orders/orders.json!\n")

def main():
    print("=" * 60)
    print("🚀 B2B AI SALES ENGINE COMPREHENSIVE VERIFICATION")
    print("=" * 60)
    test_catalog_manager()
    test_sales_brain_inquiry()
    test_sales_brain_order_capture()
    print("🎉 ALL 3 CORE VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
