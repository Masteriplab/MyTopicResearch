import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from isodate import parse_duration

# YouTube API Key
API_KEY = "AIzaSyDd__3DY2tsGLBHQdUaLX8n7BU7mnzO5Dw"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topic Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
keyword_input = st.text_input("Enter Keywords (comma-separated, e.g., Dark Psychology, Carl Jung Shadow Work):")

# Default keywords
default_keywords = [
    "Dark Psychology", "Carl Jung Shadow Work", "Machiavellian Tactics", "Philosophy of Power",
    "Mental Toughness", "Nietzsche Motivation", "Emotional Detachment", "Psychological Manipulation",
    "Self-Mastery Psychology", "Philosophical Truths", "Human Behavior Explained", "Inner Shadow Psychology",
    "Control and Influence", "Ego Death", "Power of Silence"
]

# Process keywords
keywords = [k.strip() for k in keyword_input.split(",") if k.strip()] if keyword_input else default_keywords

# Fetch Data Button
if st.button("Fetch Data"):
    if not keywords:
        st.error("Please enter at least one keyword or use default keywords.")
    else:
        try:
            # Calculate date range
            start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
            all_results = []

            # Iterate over the list of keywords
            for keyword in keywords:
                st.write(f"Searching for keyword: {keyword}")

                # Define search parameters
                search_params = {
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": start_date,
                    "maxResults": 5,
                    "key": API_KEY,
                }

                # Fetch video data
                response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
                data = response.json()

                # Check if "items" key exists
                if "items" not in data or not data["items"]:
                    st.warning(f"No videos found for keyword: {keyword}")
                    continue

                videos = data["items"]
                video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
                channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

                if not video_ids or not channel_ids:
                    st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                    continue

                # Fetch video statistics and content details (for duration)
                stats_params = {
                    "part": "statistics,contentDetails",
                    "id": ",".join(video_ids),
                    "key": API_KEY
                }
                stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
                stats_data = stats_response.json()

                if "items" not in stats_data or not stats_data["items"]:
                    st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                    continue

                # Fetch channel statistics
                channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
                channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
                channel_data = channel_response.json()

                if "items" not in channel_data or not channel_data["items"]:
                    st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                    continue

                stats = stats_data["items"]
                channels = channel_data["items"]

                # Collect results
                for video, stat, channel in zip(videos, stats, channels):
                    title = video["snippet"].get("title", "N/A")
                    description = video["snippet"].get("description", "")[:200]
                    video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                    views = int(stat["statistics"].get("viewCount", 0))
                    subs = int(channel["statistics"].get("subscriberCount", 0))
                    duration = parse_duration(stat["contentDetails"].get("duration", "PT0S")).total_seconds()

                    # Filter by subscribers, views, and duration (10 min to 60 min)
                    if (subs < 3000 and 
                        10000 <= views <= 1000000 and 
                        600 <= duration <= 3600):
                        all_results.append({
                            "Title": title,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Subscribers": subs,
                            "Duration (min)": round(duration / 60, 2)
                        })

            # Sort results by views in descending order
            all_results = sorted(all_results, key=lambda x: x["Views"], reverse=True)

            # Display results
            if all_results:
                st.success(f"Found {len(all_results)} results across all keywords!")
                for result in all_results:
                    st.markdown(
                        f"**Title:** {result['Title']}  \n"
                        f"**Description:** {result['Description']}  \n"
                        f"**URL:** [Watch Video]({result['URL']})  \n"
                        f"**Views:** {result['Views']}  \n"
                        f"**Subscribers:** {result['Subscribers']}  \n"
                        f"**Duration:** {result['Duration (min)']} minutes"
                    )
                    st.write("---")

                # Create a bar chart for view counts
                df = pd.DataFrame(all_results)
                chart_data = pd.DataFrame({
                    "Title": df["Title"],
                    "Views": df["Views"]
                }).set_index("Title")
                st.bar_chart(chart_data)

            else:
                st.warning("No results found for channels with fewer than 3,000 subscribers, views between 10K and 1M, and duration between 10 and 60 minutes.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
