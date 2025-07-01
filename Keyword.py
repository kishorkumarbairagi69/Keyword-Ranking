import streamlit as st
import pandas as pd
import asyncio
import aiohttp
import base64
from urllib.parse import urlparse
from datetime import datetime
import io

# Set page config early
st.set_page_config(page_title="SEO Rank Checker", layout="centered")

# 👨‍💻 CREDIT LOCK — Do not remove this section
def verify_credit():
    CREDIT_NAME = "Kishor Kumar Bairagi"
    if "Kishor" not in CREDIT_NAME:
        st.error("❌ Unauthorized modification: Developer credit missing.")
        st.stop()

verify_credit()  # Call the credit check after setting page config

# App Header
st.title("🔍 SEO Keyword Rank Checker Dashboard")
st.markdown("### 👨‍💻 Developed by **Kishor Kumar Bairagi**")

# Function to fetch data
MAX_REQUESTS_PER_MINUTE = 2000
CONCURRENT_REQUESTS = 200

async def fetch(session, url, headers, payload):
    async with session.post(url, json=payload, headers=headers) as response:
        if response.status in [200, 201]:
            return await response.json()
        return None

async def get_results(keywords, username, password, domain):
    url = 'https://api.dataforseo.com/v3/serp/google/organic/live/advanced'
    b64_auth = base64.b64encode(f'{username}:{password}'.encode()).decode()
    headers = {'Authorization': f'Basic {b64_auth}', 'Content-Type': 'application/json'}

    results = []
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async def bound_fetch(session, keyword):
        async with semaphore:
            payload = [{
                "keyword": keyword,
                "location_code": 2840,
                "language_code": "en",
                "device": "desktop",
                "os": "windows",
                "depth": 100
            }]
            data = await fetch(session, url, headers, payload)
            if data and 'tasks' in data and data['tasks']:
                items = data['tasks'][0].get('result', [{}])[0].get('items', [])
                for item in items:
                    result_url = item.get('url', '')
                    parsed_domain = urlparse(result_url).netloc.replace('www.', '')
                    if parsed_domain == domain:
                        results.append([keyword, item.get('rank_absolute'), result_url, item.get('title'), item.get('description')])
                        return
            results.append([keyword, 100, '', '', ''])  # Not found

    async with aiohttp.ClientSession() as session:
        tasks = [bound_fetch(session, kw) for kw in keywords]
        await asyncio.gather(*tasks)
    return results

# Streamlit Form
with st.form("credentials_form"):
    username = st.text_input("🔐 DataForSEO Username")
    password = st.text_input("🔐 DataForSEO Password", type="password")
    domain = st.text_input("🌐 Target Domain (e.g., pw.live)")
    uploaded_file = st.file_uploader("📤 Upload keywords.csv", type="csv")
    submitted = st.form_submit_button("🚀 Start Ranking Check")

# If form is submitted
if submitted:
    if not (username and password and domain and uploaded_file):
        st.error("❗ Please fill in all fields and upload a CSV file.")
    else:
        keywords = pd.read_csv(uploaded_file, header=None)[0].tolist()
        st.info(f"⏳ Processing {len(keywords)} keywords...")
        with st.spinner("📡 Fetching rankings..."):
            results = asyncio.run(get_results(keywords, username, password, domain))
            df = pd.DataFrame(results, columns=["Keyword", "Position", "URL", "Title", "Snippet"])
            st.success("✅ Ranking fetched successfully!")
            st.dataframe(df)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="⬇️ Download Results as CSV",
                data=csv_buffer.getvalue(),
                file_name=f'rankings_{domain}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )

# Footer Credit (required to remain)
st.markdown("---")
st.markdown("Made with ❤️ by **Kishor Kumar Bairagi**")
