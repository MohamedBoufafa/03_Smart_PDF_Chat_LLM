# 🚀 Deployment Guide - 3 Easy Steps

## What You Have

Your Smart PDF Chat app is ready to deploy!

### Files:
```
03_Smart_PDF_Chat_LLM/
├── app.py                      # Streamlit application
├── requirements_streamlit.txt  # Dependencies
├── .streamlit/config.toml     # Configuration
├── README.md                   # GitHub documentation
└── Smart_PDF_Chat_ULTRA_FAST.ipynb  # Kaggle version (optional)
```

---

## Deploy to Streamlit Cloud (FREE - 12 minutes)

### Step 1: Create GitHub Repo (2 min)
1. Go to https://github.com/new
2. Name: `smart-pdf-chat` 
3. Make it **Public** ✅
4. Click "Create repository"
5. Upload these files:
   - `app.py`
   - `requirements_streamlit.txt`
   - `.streamlit/config.toml`
   - `README.md`

### Step 2: Deploy (5 min)
1. Visit https://share.streamlit.io
2. Sign up with GitHub
3. Click "New app"
4. Select your repo: `your-username/smart-pdf-chat`
5. Branch: `main`
6. Main file path: `app.py`
7. Click "Deploy!"

### Step 3: Test (3 min)
- Wait 2-3 minutes for build
- Upload a PDF
- Ask questions
- Get your URL: `https://your-username-smart-pdf-chat.streamlit.app`

**Done! Add this URL to your CV!** 🎉

---

## Alternative: Hugging Face Spaces (FREE + GPU option)

### Step 1: Create Account
- Go to https://huggingface.co/join
- Sign up (free)

### Step 2: Create Space
- Click "New Space"
- Name: `smart-pdf-chat`
- SDK: **Streamlit**
- Hardware: CPU Basic (free) or T4 Small ($1/mo for GPU)
- Click "Create"

### Step 3: Upload Files
- Drag and drop:
  - `app.py`
  - `requirements_streamlit.txt`
- Commit changes

### Result:
Your URL: `https://huggingface.co/spaces/YOUR-USERNAME/smart-pdf-chat`

---

## Run Locally (For Testing)

```bash
# Install dependencies
pip install -r requirements_streamlit.txt

# Run app
streamlit run app.py

# Open: http://localhost:8501
```

---

## Add to Your CV

```
SMART PDF CHAT | AI Document Q&A System
Live: https://your-app.streamlit.app | GitHub: your-repo-url

• RAG system with Flan-T5 (780M params)
• 1-2 second query response times
• Multi-document support with citations
• Deployed on Streamlit Cloud

Tech: Python, PyTorch, Transformers, ChromaDB, Streamlit
```

---

## Troubleshooting

**Out of memory?**
- Edit `app.py` line 194: Change to `google/flan-t5-base` (smaller model)

**Slow responses?**
- Upgrade to Hugging Face Spaces with GPU ($1/mo)

**App won't start?**
- Check all files uploaded correctly
- Verify `requirements_streamlit.txt` is present

---

## Next Steps

1. ✅ Deploy your app
2. ✅ Test with real PDFs
3. ✅ Add URL to CV
4. ✅ Share on LinkedIn
5. ✅ Move to next project!

**Total time: 12 minutes to live app!** ⚡
