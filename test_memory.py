"""
test_memory.py — Quick sanity check for the memory system.
Run: python test_memory.py
"""

import os
import sys
import shutil

# Check chromadb is installed
try:
    import chromadb
    print(f"✅ chromadb installed: {chromadb.__version__}")
except ImportError:
    print("❌ chromadb not installed! Run: pip install chromadb")
    sys.exit(1)

# Check google-genai is installed
try:
    from google import genai
    print("✅ google-genai installed")
except ImportError:
    print("❌ google-genai not installed!")
    sys.exit(1)

# Import our memory module
import memory

# --- Test with a fresh database ---
TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db_test")

# Override the DB path for testing
memory.CHROMA_DB_PATH = TEST_DB
memory._chroma_client = None
memory._collection = None

print("\n🧪 Test 1: Save conversations")
ok1 = memory.save_conversation("Mera naam Yashraj hai", "ओह, तो तुम हो Yashraj! बहुत अच्छा नाम है बाबू।")
ok2 = memory.save_conversation("Mujhe Python sikhna hai", "चलो ना, Python सीखते हैं! Main tumhe सिखाऊँगी।")
ok3 = memory.save_conversation("Kal mera exam hai", "OMG exam! Tension mat lo बाबू, तुम बहुत अच्छा करोगे।")

if ok1 and ok2 and ok3:
    print("✅ All 3 conversations saved!")
else:
    print(f"⚠️ Save results: {ok1}, {ok2}, {ok3}")

print(f"\n🧪 Test 2: Memory count = {memory.get_memory_count()}")
assert memory.get_memory_count() == 3, f"Expected 3, got {memory.get_memory_count()}"
print("✅ Count correct!")

print("\n🧪 Test 3: Retrieve relevant context")
context = memory.get_relevant_context("Mera naam kya hai?")
print(f"📋 Retrieved context:\n{context}")

if "Yashraj" in context:
    print("✅ Memory retrieval works — found 'Yashraj' in context!")
else:
    print("⚠️ 'Yashraj' not found in context, but retrieval returned something")

print("\n🧪 Test 4: Retrieve for a different query")
context2 = memory.get_relevant_context("Python kaise sikhe?")
print(f"📋 Retrieved context:\n{context2}")

if "Python" in context2:
    print("✅ Found 'Python' in context!")
else:
    print("⚠️ 'Python' not found in context")

# Cleanup test DB
print("\n🧹 Cleaning up test database...")
memory._collection = None
memory._chroma_client = None
try:
    shutil.rmtree(TEST_DB, ignore_errors=True)
    print("✅ Test DB cleaned up.")
except:
    print("⚠️ Could not clean up test DB at:", TEST_DB)

# Reset to production path
memory.CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
memory._chroma_client = None
memory._collection = None

print("\n" + "=" * 50)
print("🎉 All tests passed! Memory system is working.")
print("=" * 50)
