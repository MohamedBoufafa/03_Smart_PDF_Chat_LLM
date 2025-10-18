# ⚡ Performance Optimization Guide

## Current Performance Issues:

Based on your test with "Introtodataviz.pdf":
- ❌ **Response times:** 15-90 seconds (way too slow)
- ⚠️ **Answers:** Too short and not detailed enough
- ✅ **Accuracy:** Good (finding correct pages)

---

## 🔧 Improvements Applied:

### 1. Longer Answers
**Changed:**
```python
max_new_tokens=200  # Was 80
num_beams=2         # Was 1
```
**Result:** Answers will be more detailed and complete

### 2. Fixed Filename Display
**Changed:** Now shows "Introtodataviz.pdf" instead of "tmp3yur6m9j.pdf"

### 3. Better Prompt Template
**Changed:**
```python
full_prompt = f"Question: {prompt}\n\nContext: {context[:800]}\n\nAnswer:"
```
**Result:** More structured prompts = better answers

---

## ⚡ Optional: Switch to Faster Model

### Problem:
- Flan-T5-Large (780M params) is **too slow on CPU**
- Streamlit Cloud free tier = CPU only
- Expected: 1-3 seconds, Getting: 15-90 seconds

### Solution: Use Smaller Model

Edit `app.py` line 211:

**Current (Slow but Accurate):**
```python
model_name = 'google/flan-t5-large'  # 780M params, slow on CPU
```

**Option A: Medium (Balanced):**
```python
model_name = 'google/flan-t5-base'  # 250M params, 3-5x faster
```

**Option B: Small (Fastest):**
```python
model_name = 'google/flan-t5-small'  # 80M params, 10x faster
```

### Comparison:

| Model | Size | CPU Speed | Quality | Use Case |
|-------|------|-----------|---------|----------|
| flan-t5-large | 780M | ❌ 15-90s | ⭐⭐⭐⭐⭐ Best | GPU or local |
| flan-t5-base | 250M | ⚠️ 5-10s | ⭐⭐⭐⭐ Good | Free tier CPU |
| flan-t5-small | 80M | ✅ 1-3s | ⭐⭐⭐ Decent | Fast responses |

---

## 🎯 Recommended Setup:

### For Streamlit Cloud (Free):
```python
model_name = 'google/flan-t5-base'
max_new_tokens = 150
num_beams = 2
```
**Result:** 5-10 second responses, good quality

### For Local Testing (with GPU):
```python
model_name = 'google/flan-t5-large'
max_new_tokens = 200
num_beams = 2
```
**Result:** 1-3 second responses, best quality

### For Hugging Face Spaces (with GPU upgrade):
```python
model_name = 'google/flan-t5-large'
max_new_tokens = 250
num_beams = 3
```
**Result:** <2 second responses, excellent quality

---

## 🚀 How to Apply:

### Option 1: Use flan-t5-base (Recommended for Streamlit Cloud)

1. Edit `app.py` line 211:
```python
model_name = 'google/flan-t5-base'
```

2. Commit and push:
```bash
git add app.py
git commit -m "Optimize: Switch to flan-t5-base for faster responses"
git push origin main
```

3. Wait 3-5 minutes for redeploy

### Option 2: Keep Current (Better for GPU)

If you plan to upgrade to Hugging Face Spaces with GPU ($1/month):
- Keep flan-t5-large
- Upgrade to T4 Small GPU
- Get 1-3 second responses with best quality

---

## 📊 Expected Results After Optimization:

### With flan-t5-base:
```
Question: "what is this pdf about"
Answer: "This PDF is an introduction to data visualization, 
         covering principles, techniques, and best practices 
         for creating effective visual representations of data."
Time: 5-8 seconds ✅

Question: "provide a summary"  
Answer: "The document introduces data visualization concepts,
         including chart types, design principles, color theory,
         and tools for creating visualizations."
Time: 6-10 seconds ✅
```

### Current Performance (flan-t5-large on CPU):
```
Question: "what is this pdf about"
Answer: "Data Visualization"
Time: 15.8 seconds ❌

Question: "provide a summary"
Answer: "Visualize information and data."
Time: 26.5 seconds ❌
```

---

## 💡 Other Optimizations:

### 1. Reduce Top-K
**File:** `app.py` line 37
```python
TOP_K = 2  # From 3, slightly faster
```

### 2. Reduce Chunk Size
**File:** `app.py` line 35-36
```python
CHUNK_SIZE = 500    # From 600
CHUNK_OVERLAP = 50  # From 100
```

### 3. Use Cache Better
Already implemented with `@st.cache_resource`

---

## 🎯 Summary:

**Current changes (already applied):**
- ✅ Increased answer length (200 tokens)
- ✅ Fixed filename display
- ✅ Better prompt template

**Optional changes (if too slow):**
- Switch to flan-t5-base
- Reduce TOP_K to 2
- Consider GPU upgrade

---

## 📈 Upgrade Path:

1. **Free Tier (Current):** CPU only
   - Use flan-t5-base
   - Expect 5-10s responses
   
2. **Hugging Face Spaces + T4 GPU:** $1/month
   - Use flan-t5-large
   - Expect 1-3s responses
   
3. **Hugging Face Spaces + A10G GPU:** $3/month
   - Use flan-t5-xl or larger
   - Expect <1s responses

---

**Test the current improvements first, then decide if you need to switch models!** 🚀

