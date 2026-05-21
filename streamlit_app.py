import streamlit as st
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

# --- 1. SUBSCRIPTION AUTH LOGIC ---
# For a 5-hour launch, manually add keys here as people buy them.
# Example: "MAPS-PRO-9912"
ACTIVE_LICENSE_KEYS = ["USER/20261", "USER/20262","USER/20263","USER/20264","USER/20265","USER/20266", "GUEST-BETA-2026", "USER-XP-92"]

st.set_page_config(page_title="MapsLead Pro SaaS", page_icon="🚀", layout="wide")

# --- 2. SIDEBAR INTERFACE ---
st.sidebar.title("🔑 Membership")
user_key = st.sidebar.text_input("Enter License Key", type="password", help="Get your key at yoursite.com")

if user_key not in ACTIVE_LICENSE_KEYS:
    st.sidebar.warning("Invalid or Expired Key")
    st.title("🔒 Access Restricted")
    st.info("This is a premium tool. Please enter a valid monthly subscription key in the sidebar to unlock the scraper.")
    st.stop()

# --- 3. THE APP CONTENT (Only visible if key is valid) ---
st.sidebar.success("License Active: Monthly Pro")
st.title("🚀 MapsLead Pro: Business Scraper")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Search Parameters")
    target_niche = st.text_input("Niche (e.g., HVAC, Dentists)", "Roofers")
    target_location = st.text_input("Location (e.g., Miami, FL)", "Austin, TX")
    limit = st.number_input("Max Leads to Pull", min_value=5, max_value=200, value=20)
    
    search_query = f"{target_niche} in {target_location}"

# --- 4. THE SCRAPER ENGINE ---
async def scrape_google_maps(query, total):
    async with async_playwright() as p:
        # Note: Set headless=True for cloud deployment
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to search
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        await page.goto(url)
        
        leads = []
        # Wait for the sidebar results to appear
        try:
            await page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]', timeout=10000)
        except:
            return pd.DataFrame()

        # Scroll to load leads
        for _ in range(3):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(1)

        listings = await page.query_selector_all('//a[contains(@href, "https://www.google.com/maps/place")]')
        
        for listing in listings[:total]:
            name = await listing.get_attribute('aria-label')
            leads.append({
                "Business Name": name,
                "Source": "Google Maps",
                "Status": "Verified Lead"
            })
            
        await browser.close()
        return pd.DataFrame(leads)

# --- 5. EXECUTION & DISPLAY ---
with col2:
    st.header("Lead Results")
    if st.button("Generate Leads Now"):
        if not target_niche or not target_location:
            st.error("Please fill in both Niche and Location.")
        else:
            with st.spinner(f"Scanning {target_location} for {target_niche}..."):
                results_df = asyncio.run(scrape_google_maps(search_query, limit))
                
                if not results_df.empty:
                    st.success(f"Successfully extracted {len(results_df)} leads!")
                    st.dataframe(results_df, use_container_width=True)
                    
                    # DOWNLOAD COMPONENT
                    csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV Report",
                        data=csv,
                        file_name=f"leads_{target_niche}.csv",
                        mime="text/csv",
                    )
                else:
                    st.error("No leads found. Try a broader search term.")
