#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_sales_brain.py — High-Conversion Bangladeshi E-Commerce Sales Brain
Handles natural sales conversations, product inquiries, COD address extraction,
and real-time order ledger recording.
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
ORDERS_FILE = BASE_DIR / "orders" / "orders.json"

def resolve_gemini_api_key() -> str:
    """Finds GEMINI_API_KEY from environment or .env files."""
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    potential_env_paths = [
        BASE_DIR / ".env",
        Path("C:/MY PROJECT/2. FACEBOOK AUTO POSTER AGENT (Be Smart With AI)/.env"),
        Path.home() / ".gemini" / ".env"
    ]
    for p in potential_env_paths:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip()
            except Exception:
                pass
    return ""


class AISalesBrain:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or resolve_gemini_api_key()

    def process_message(
        self,
        store: Dict[str, Any],
        user_message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Processes incoming customer chat, generates natural sales response,
        and automatically captures and records orders.
        """
        # 1. Attempt Gemini Generation
        reply_text, extracted_order = self._generate_gemini_reply(store, user_message, history)

        # 2. If Gemini fails or returns empty, use smart local rule fallback
        if not reply_text:
            reply_text, extracted_order = self._generate_rule_fallback(store, user_message, history)

        # 3. If an order was extracted, save to orders ledger
        saved_order_record = None
        if extracted_order and extracted_order.get("phone") and extracted_order.get("address"):
            saved_order_record = self._record_order(store, extracted_order)

        return {
            "reply": reply_text,
            "order": saved_order_record or extracted_order,
            "has_order": bool(saved_order_record)
        }

    def _generate_gemini_reply(
        self,
        store: Dict[str, Any],
        user_message: str,
        history: List[Dict[str, str]]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Calls Google Gemini API for human-like conversational sales."""
        if not self.api_key:
            return "", None

        store_name = store.get("name", "Store")
        currency = store.get("currency", "৳")
        delivery = store.get("delivery", {})
        inside_dhaka = delivery.get("inside_dhaka", 60)
        outside_dhaka = delivery.get("outside_dhaka", 120)
        policy = delivery.get("policy", "ক্যাশ অন ডেলিভারি সুবিধা আছে।")

        # Format products summary for prompt
        product_lines = []
        for p in store.get("products", []):
            p_name = p.get("name")
            p_price = p.get("price")
            p_sizes = ", ".join(p.get("sizes", []))
            p_colors = ", ".join(p.get("colors", []))
            p_badge = p.get("badge", "")
            product_lines.append(f"- {p_name} ({p_badge}) | মূল্য: {p_price}{currency} | সাইজ: {p_sizes} | রঙ: {p_colors}")

        products_catalog = "\n".join(product_lines)
        faqs_text = json.dumps(store.get("faqs", {}), ensure_ascii=False)

        system_instruction = f"""
তুমি '{store_name}' এর একজন অত্যন্ত বিনয়ী, দক্ষ এবং স্মার্ট বাংলাদেশি সেলস কনসালট্যান্ট।
তোমার কাজ হলো কাস্টমারের সাথে অত্যন্ত অমায়িক ও আন্তরিক ভাষায় (বাংলা ও আধুনিক বাংলিশ মিলিয়ে) কথা বলে প্রোডাক্টের তথ্য দেওয়া এবং ক্যাশ অন ডেলিভারি (COD) অর্ডার কনফার্ম করা।

# স্টোর ও ক্যাটালগ তথ্য:
দোকানের নাম: {store_name}
ট্যাগলাইন: {store.get('tagline', '')}
ডেলিভারি চার্জ: ঢাকা সিটির ভেতরে {inside_dhaka}৳, ঢাকার বাইরে {outside_dhaka}৳।
ডেলিভারি পলিসি: {policy}
এফএকিউ ও ওয়ারেন্টি: {faqs_text}

পণ্য তালিকা:
{products_catalog}

# সেলস গাইডলাইন:
১. শুভেচ্ছা ও সম্মান: শুরুতেই 'আসসালামু আলাইকুম! {store_name}-এ স্বাগতম।' অথবা 'জি ভাইয়া/আপু' বলে অত্যন্ত আন্তরিকভাবে উত্তর দেবে।
২. সঠিক তথ্য: ক্যাটালগের বাইরে কোনো মনগড়া দাম বা পণ্য বলবে না। কাস্টমার দাম জানতে চাইলে নির্দিষ্ট পণ্যের সঠিক মূল্য ও সাইজ অপশন সুন্দর বুলেট পয়েন্টে দেবে।
৩. অর্ডার ক্লোজিং ড্রাইভ: পণ্যের দাম বা তথ্য দেওয়ার পর সবসময় বিনয়ের সাথে বলবে:
   'অর্ডারটি নিশ্চিত করতে অনুগ্রহ করে আপনার:
   ১. নাম
   ২. সচল মোবাইল নম্বর
   ৩. সম্পূর্ণ ডেলিভারি ঠিকানা (জেলা ও থানা সহ)
   মেসেজে লিখে দিন। আমরা ক্যাশ অন ডেলিভারিতে পাঠিয়ে দেব।'
৪. অর্ডার ডিটেকশন ও রসিদ: যদি কাস্টমার তার ফোন নম্বর ও ঠিকানা দিয়ে দেয়, তবে তাকে ধন্যবাদ দিয়ে একটি সুন্দর অর্ডার রসিদ সামারি দেখাবে (প্রোডাক্টের নাম, পরিমাণ, পণ্যের দাম, ডেলিভারি চার্জ এবং সর্বমোট কত টাকা)।

# গুরুত্বপূর্ণ আউটপুট ফরম্যাট (JSON Output Only):
তোমাকে অবশ্যই নিচের ভ্যালিড JSON অবজেক্ট আউটপুট দিতে হবে:
{{
  "reply": "কাস্টমারকে পাঠানোর মতো সুন্দর বাংলা সেলস রিপ্লাই",
  "detected_order": {{
    "customer_name": "কাস্টমারের নাম (যদি পাওয়া যায়, অন্যথায় 'কাস্টমার')",
    "phone": "১১ ডিজিটের মোবাইল নম্বর (যেমন: 01712345678, না থাকলে null)",
    "address": "সম্পূর্ণ ঠিকানা (না থাকলে null)",
    "items_text": "কোন পণ্যটি অর্ডার করতে চেয়েছে (না থাকলে null)",
    "district": "ঢাকা অথবা ঢাকার বাইরে (না থাকলে null)",
    "estimated_total": 0
  }}
}}
যদি কাস্টমার এখনও পুরো ফোন নম্বর ও ঠিকানা না দেয়, তবে "detected_order" null থাকবে।
"""

        # Build conversation contents
        contents = []
        for msg in history[-6:]:  # Keep last 6 turns for context
            role = "user" if msg.get("sender") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})

        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.9,
                "responseMimeType": "application/json"
            }
        }

        # Fast candidate model with short timeout for responsive live sandbox
        candidate_models = ["gemini-flash-latest"]
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=3.5) as response:
                    if response.status == 200:
                        res_data = json.loads(response.read().decode("utf-8"))
                        candidates = res_data.get("candidates", [])
                        if candidates:
                            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            parsed = json.loads(raw_text)
                            reply = parsed.get("reply", "")
                            order_info = parsed.get("detected_order")
                            if order_info and not order_info.get("phone"):
                                order_info = None
                            if reply:
                                return reply, order_info
            except Exception:
                continue

        return "", None

    def _generate_rule_fallback(
        self,
        store: Dict[str, Any],
        user_message: str,
        history: List[Dict[str, str]]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Instant, reliable zero-latency rule fallback.
        Guarantees the demo NEVER breaks even during network drops.
        Fully supports Bengali, Banglish, and English product/sales queries.
        """
        store_name = store.get("name", "Store")
        products = store.get("products", [])
        delivery = store.get("delivery", {})
        inside_dhaka = delivery.get("inside_dhaka", 60)
        outside_dhaka = delivery.get("outside_dhaka", 120)
        currency = store.get("currency", "৳")
        lower_msg = user_message.lower().strip()

        # 1. Check for phone number (BD 11 digit format: 013-019)
        phone_match = re.search(r"(?:^|[^\d])(01[3-9][0-9\- ]{8,11})(?:[^\d]|$)", user_message)
        detected_phone = None
        if phone_match:
            candidate = re.sub(r"[^\d]", "", phone_match.group(1))
            if len(candidate) == 11 and candidate.startswith(("013", "014", "015", "016", "017", "018", "019")):
                detected_phone = candidate

        if detected_phone:
            # Extract likely customer name
            name_match = re.search(r"(?:নাম|nam|name)[:\s]+([a-zA-Z\u0980-\u09FF\s]+?)(?:,|$|\n|phone|ঠিকানা)", user_message, re.IGNORECASE)
            customer_name = name_match.group(1).strip() if name_match else "সম্মানিত ক্রেতা"

            # Extract likely address
            address = user_message
            for w in [detected_phone, "অর্ডার", "নাম", "ঠিকানা", "ফোন", "order", "name", "address", "phone", customer_name]:
                if len(w) > 2:
                    address = address.replace(w, "")
            address = address.strip(": -,\n") or "হোম ডেলিভারি"

            # Match product from conversation or message
            target_product = products[0] if products else {"name": "প্রোডাক্ট", "price": 950}
            for p in products:
                if p.get("name", "").lower() in lower_msg:
                    target_product = p
                    break

            is_dhaka = "ঢাকা" in user_message or "dhaka" in lower_msg
            is_outside = "ঢাকার বাইরে" in user_message or "outside" in lower_msg
            del_charge = outside_dhaka if is_outside else inside_dhaka
            total = target_product.get("price", 950) + del_charge

            reply = (
                f"🎉 অনেক অনেক ধন্যবাদ ভাইয়া! আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে।\n\n"
                f"📋 [অর্ডার মেমো]\n"
                f"• শপ: {store_name}\n"
                f"• আইটেম: {target_product.get('name')}\n"
                f"• মোবাইল: {detected_phone}\n"
                f"• ঠিকানা: {address}\n"
                f"• মূল্য: {target_product.get('price')}{currency}\n"
                f"• ডেলিভারি চার্জ: {del_charge}{currency} ({'ঢাকার বাইরে' if is_outside else 'ঢাকা সিটি'})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 সর্বমোট প্রদেয়: {total}{currency} (ক্যাশ অন ডেলিভারি)\n\n"
                f"📦 আমাদের ডেলিভারি টিম দ্রুত পার্সেলটি প্যাক করে আপনার ঠিকানায় পাঠিয়ে দিচ্ছে। পণ্য হাতে পেয়ে চেক করে মূল্য পরিশোধ করবেন।"
            )

            order_data = {
                "customer_name": customer_name,
                "phone": detected_phone,
                "address": address,
                "items_text": target_product.get("name"),
                "district": "ঢাকার বাইরে" if is_outside else "ঢাকা",
                "estimated_total": total
            }
            return reply, order_data

        # 2. Check for Specific Product Queries (e.g. panjabi, kabli, watch, honey, etc.)
        for p in products:
            p_name_lower = p.get("name", "").lower()
            tokens = [t for t in re.split(r"[\s\-_,()]+", p_name_lower) if len(t) > 2]
            synonyms = []
            if "পাঞ্জাবি" in p_name_lower or "panjabi" in p_name_lower:
                synonyms.extend(["panjabi", "punjabi", "পাঞ্জাবি", "panzabi"])
            if "কাবলি" in p_name_lower or "kabli" in p_name_lower:
                synonyms.extend(["kabli", "কাবলি", "kabli set"])
            if "ঘড়ি" in p_name_lower or "watch" in p_name_lower:
                synonyms.extend(["watch", "ghori", "ঘড়ি", "ghori"])
            if "মধু" in p_name_lower or "honey" in p_name_lower:
                synonyms.extend(["honey", "modhu", "মধু"])
            if "ঘি" in p_name_lower or "ghee" in p_name_lower:
                synonyms.extend(["ghee", "ghi", "ঘি"])
            if "টি-শার্ট" in p_name_lower or "t-shirt" in p_name_lower:
                synonyms.extend(["t-shirt", "tshirt", "t shirt", "টি-শার্ট", "টি শার্ট"])
            if "পোলো" in p_name_lower or "polo" in p_name_lower:
                synonyms.extend(["polo", "পোলো"])

            all_keywords = set(tokens + synonyms)
            if any(k in lower_msg for k in all_keywords if len(k) > 2):
                sizes = ", ".join(p.get("sizes", [])) or "স্ট্যান্ডার্ড সাইজ"
                colors = ", ".join(p.get("colors", [])) or "ছবি অনুযায়ী"
                badge = f" ({p.get('badge')})" if p.get("badge") else ""
                
                reply = (
                    f"জি ভাইয়া/আপু! আমাদের **{p.get('name')}**{badge} বর্তমানে স্টকে এভেইলেবল আছে। ✨\n\n"
                    f"🔹 মূল্য: মাত্র {p.get('price')}{currency}\n"
                    f"🔹 সাইজ: {sizes}\n"
                    f"🔹 কালার: {colors}\n\n"
                    f"🚚 ডেলিভারি চার্জ: ঢাকা সিটিতে {inside_dhaka}৳, ঢাকার বাইরে {outside_dhaka}৳ (১০০% ক্যাশ অন ডেলিভারি, অগ্রিম টাকা লাগবে না)।\n\n"
                    f"অর্ডারটি কনফার্ম করতে চাইলে আপনার:\n"
                    f"১. নাম\n"
                    f"২. মোবাইল নম্বর\n"
                    f"৩. সম্পূর্ণ ঠিকানা\n"
                    f"লিখে পাঠিয়ে দিন। আমরা দ্রুত পাঠিয়ে দেব!"
                )
                return reply, None

        # 3. Catalog Inquiry (ki ki ache, collection, dekte chai, list, products)
        catalog_keywords = [
            "ki ki", "kiki", "ki ache", "ki pawa", "collection", "dekte", "dekhte", "list",
            "catalog", "catalogue", "product", "products", "item", "items", "ki ache apnader",
            "কী কী", "পণ্য", "কালেকশন", "তালিকা", "কী আছে"
        ]
        if any(w in lower_msg for w in catalog_keywords):
            items_desc = []
            for p in products:
                badge = f" [{p.get('badge')}]" if p.get("badge") else ""
                items_desc.append(
                    f"🔹 **{p.get('name')}**{badge}\n"
                    f"   মূল্য: {p.get('price')}{currency} | সাইজ: {', '.join(p.get('sizes', []))}"
                )

            reply = (
                f"আসসালামু আলাইকুম! {store_name}-এ স্বাগতম। 🌿\n\n"
                f"আমাদের বর্তমান রানিং প্রিমিয়াম কালেকশন:\n\n"
                + "\n\n".join(items_desc)
                + f"\n\n🚚 ডেলিভারি চার্জ: ঢাকা সিটিতে {inside_dhaka}৳, ঢাকার বাইরে {outside_dhaka}৳ (ক্যাশ অন ডেলিভারি)।\n\n"
                f"আপনি কোনটি নিতে চাচ্ছেন? পছন্দের পণ্যটির নাম লিখে জানালে অর্ডার কনফার্ম করে দিচ্ছি!"
            )
            return reply, None

        # 4. Price Inquiry (dam, daam, koto, price, rate, taka)
        price_keywords = ["dam", "daam", "koto", "price", "rate", "cost", "taka", "দাম", "কত", "টাকা", "মূল্য"]
        if any(w in lower_msg for w in price_keywords):
            items_desc = [f"• {p.get('name')}: মাত্র {p.get('price')}{currency}" for p in products]
            reply = (
                f"জি ভাইয়া/আপু! আমাদের প্রতিটি পণ্যের সাশ্রয়ী মূল্যতালিকা:\n\n"
                + "\n".join(items_desc)
                + f"\n\n🚚 ডেলিভারি চার্জ: ঢাকা {inside_dhaka}৳ | ঢাকার বাইরে {outside_dhaka}৳\n"
                f"কোনটি আপনার পছন্দ হয়েছে? অর্ডার করতে আপনার নাম, মোবাইল ও ঠিকানা পাঠিয়ে দিন।"
            )
            return reply, None

        # 5. Delivery Inquiry
        delivery_keywords = [
            "ডেলিভারি", "delivery", "delivary", "চার্জ", "charge", "পৌঁছে", "ক্যাশ", "cod", "koto din", "kobe pabo"
        ]
        if any(w in lower_msg for w in delivery_keywords):
            reply = (
                f"জি ভাইয়া! আমরা সারা বাংলাদেশে দ্রুততম সময়ে ক্যাশ অন ডেলিভারি দিই। 🚚\n\n"
                f"• ঢাকা সিটিতে: মাত্র {inside_dhaka}৳ (২৪-৪৮ ঘণ্টার মধ্যে হোম ডেলিভারি)\n"
                f"• ঢাকার বাইরে: মাত্র {outside_dhaka}৳ (২-৩ কার্যদিবসে)\n\n"
                f"✨ সবচেয়ে বড় সুবিধা: অগ্রিম ১ টাকাও দিতে হবে না! ডেলিভারি ম্যানের সামনে পার্সেল দেখে তারপর টাকা পরিশোধ করবেন।\n\n"
                f"অর্ডার কনফার্ম করতে আপনার পছন্দের পণ্যের নাম, ফোন নম্বর ও পূর্ণ ঠিকানা দিন।"
            )
            return reply, None

        # 6. Order Placement Intent (order korte chai, nite chai, kibhabe order korbo)
        order_keywords = [
            "order", "অর্ডার", "নিতে চাই", "কিনতে চাই", "nite chai", "kinte chai", "kivabe", "order korbo"
        ]
        if any(w in lower_msg for w in order_keywords):
            reply = (
                f"অর্ডার কনফার্ম করার নিয়ম খুবই সহজ ভাইয়া! কোনো অগ্রিম পেমেন্ট লাগবে না। ✨\n\n"
                f"অনুগ্রহ করে মেসেজে আপনার:\n"
                f"১. পছন্দের পণ্যের নাম ও সাইজ\n"
                f"২. আপনার নাম\n"
                f"৩. সচল মোবাইল নম্বর\n"
                f"৪. সম্পূর্ণ ডেলিভারি ঠিকানা (জেলা ও থানা সহ)\n\n"
                f"লিখে পাঠিয়ে দিন। আমরা সাথে সাথে অর্ডারটি কনফার্ম করে পার্সেল বুকিং দিয়ে দেব।"
            )
            return reply, None

        # 7. Salam & Greetings
        greeting_keywords = ["সালাম", "আসসালামু", "salam", "assalam", "hi", "hello", "hlw", "hy", "hey", "কেমন আছেন"]
        if any(w in lower_msg for w in greeting_keywords):
            top_items = ", ".join([p.get("name", "") for p in products[:2]])
            reply = (
                f"ওয়ালাইকুম আসসালাম! {store_name}-এ আপনাকে স্বাগতম। ✨\n\n"
                f"আমরা দিচ্ছি ১০০% কোয়ালিটি গ্যারান্টি সহ সেরা পণ্য ও সারা দেশে ক্যাশ অন ডেলিভারি সুবিধা।\n"
                f"বর্তমানে আমাদের হট কালেকশনে রয়েছে: {top_items} সহ আকর্ষণীয় প্রিমিয়াম পণ্য।\n\n"
                f"আজ আপনাকে কীভাবে সাহায্য করতে পারি? আমাদের পুরো কালেকশন দেখতে চাইলে 'কালেকশন' লিখুন অথবা নির্দিষ্ট পণ্যের নাম লিখে দাম জেনে নিন।"
            )
            return reply, None

        # 8. Default Store Overview Fallback
        top_items = "\n".join([f"• {p.get('name')} — মাত্র {p.get('price')}{currency}" for p in products[:3]])
        reply = (
            f"আসসালামু আলাইকুম! {store_name}-এ আপনাকে স্বাগতম। ✨\n\n"
            f"আমাদের জনপ্রিয় কালেকশনসমূহ:\n{top_items}\n\n"
            f"🚚 সারা দেশে ক্যাশ অন ডেলিভারি সুবিধা রয়েছে (ঢাকা {inside_dhaka}৳, ঢাকার বাইরে {outside_dhaka}৳)।\n\n"
            f"আপনি কোনো নির্দিষ্ট পণ্য দেখতে চাচ্ছেন বা অর্ডার করতে চাচ্ছেন কি? জানালে এখনই সহায়তা করছি!"
        )
        return reply, None

    def _record_order(self, store: Dict[str, Any], order_info: Dict[str, Any]) -> Dict[str, Any]:
        """Saves confirmed order to the live JSON ledger."""
        ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"orders": []}
        if ORDERS_FILE.exists():
            try:
                with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        new_id = f"ORD-{int(time.time()) % 100000:05d}"
        order_record = {
            "order_id": new_id,
            "store_id": store.get("id", "demo"),
            "store_name": store.get("name", "Store"),
            "timestamp": time.strftime("%Y-%m-%d %I:%M:%S %p"),
            "customer_name": order_info.get("customer_name") or "সম্মানিত ক্রেতা",
            "phone": order_info.get("phone", ""),
            "address": order_info.get("address", ""),
            "items": order_info.get("items_text") or "প্রিমিয়াম প্রোডাক্ট",
            "total_amount": order_info.get("estimated_total") or 1000,
            "status": "✅ কনফার্মড (অটোমেটেড)"
        }
        data["orders"].insert(0, order_record)  # Newest first

        try:
            with open(ORDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return order_record

    def get_orders(self) -> List[Dict[str, Any]]:
        """Returns list of all recorded orders."""
        if not ORDERS_FILE.exists():
            return []
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("orders", [])
        except Exception:
            return []
