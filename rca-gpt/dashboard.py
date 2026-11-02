"""
Streamlit dashboard for RCA-GPT
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from rca_gpt.db.manager import IncidentDatabase
from rca_gpt.similarity import SimilarityMatcher
from rca_gpt.patterns import PatternMiner
from rca_gpt.timeline import TimelineAnalyzer

# Page config
st.set_page_config(page_title="RCA-GPT Dashboard", layout="wide", page_icon="🔍")

# Initialize
@st.cache_resource
def init_components():
    return {
        'db': IncidentDatabase(),
        'similarity': SimilarityMatcher(),
        'patterns': PatternMiner(),
        'timeline': TimelineAnalyzer()
    }

components = init_components()
db = components['db']

# Sidebar
st.sidebar.title("🔍 RCA-GPT")
st.sidebar.markdown("AI-Powered Root Cause Analysis")

page = st.sidebar.radio("Navigate", [
    "📊 Dashboard",
    "🔍 Incident Explorer",
    "🔗 Pattern Analysis",
    "🕐 Timeline Viewer"
])

# ===== DASHBOARD =====
if page == "📊 Dashboard":
    st.title("📊 Incident Dashboard")
    
    # Summary stats
    summary = db.get_database_summary()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Incidents", summary['total_unique_incidents'])
    with col2:
        st.metric("Total Occurrences", summary['total_occurrences'])
    with col3:
        st.metric("Resolved", summary['resolved_occurrences'])
    with col4:
        st.metric("Unresolved", summary['unresolved_occurrences'])
    
    # Time period selector
    days = st.selectbox("Time Period", [7, 14, 30, 90], index=0)
    
    # Stats by type
    stats = db.get_incident_stats(days=days)
    
    if stats:
        st.subheader(f"Incidents by Type (Last {days} days)")
        
        # Create DataFrame
        df = pd.DataFrame([
            {
                'Type': k,
                'Unique': v['unique_incidents'],
                'Total': v['total_occurrences'],
                'Avg per Incident': v['avg_occurrences_per_incident']
            }
            for k, v in stats.items()
        ])
        
        # Bar chart
        st.bar_chart(df.set_index('Type')['Total'])
        
        # Table
        st.dataframe(df, use_container_width=True)
    
    # Top incidents
    st.subheader(f"Top 10 Incidents (Last {days} days)")
    top = db.get_top_incidents(limit=10, days=days)
    
    for i, inc in enumerate(top, 1):
        with st.expander(f"{i}. [{inc.incident_type}] {inc.message_template[:80]}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Occurrences:** {inc.occurrence_count}")
                st.write(f"**First seen:** {inc.first_seen.strftime('%Y-%m-%d %H:%M')}")
            with col2:
                st.write(f"**Last seen:** {inc.last_seen.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Severity:** {inc.severity}")

# ===== INCIDENT EXPLORER =====
elif page == "🔍 Incident Explorer":
    st.title("🔍 Incident Explorer")
    
    # Search
    search_term = st.text_input("Search incidents", placeholder="e.g., timeout, connection, auth")
    
    if search_term:
        results = db.search_incidents(search_term)
        st.write(f"Found {len(results)} incident(s)")
        
        for inc in results[:20]:
            with st.expander(f"#{inc.id} - {inc.incident_type}: {inc.message_template[:60]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {inc.incident_type}")
                    st.write(f"**Severity:** {inc.severity}")
                    st.write(f"**Occurrences:** {inc.occurrence_count}")
                
                with col2:
                    st.write(f"**First seen:** {inc.first_seen}")
                    st.write(f"**Last seen:** {inc.last_seen}")
                
                # Similar incidents
                if st.button(f"Find Similar", key=f"sim_{inc.id}"):
                    similar = components['similarity'].get_similar_with_context(inc.message_template)
                    
                    if similar:
                        st.write("**Similar Incidents:**")
                        for s in similar[:3]:
                            si = s['incident']
                            st.write(f"- #{si['id']} ({s['similarity']:.0%} similar): {si['message_template'][:60]}")
    
    # Recent incidents
    else:
        st.subheader("Recent Incidents")
        recent = db.get_recent_incidents(limit=20)
        
        for inc in recent:
            st.write(f"**#{inc.id}** [{inc.incident_type}] {inc.message_template} - {inc.occurrence_count}x")

# ===== PATTERN ANALYSIS =====
elif page == "🔗 Pattern Analysis":
    st.title("🔗 Pattern Analysis")
    
    days = st.slider("Look back (days)", 7, 90, 30)
    min_support = st.slider("Minimum occurrences", 2, 10, 3)
    
    if st.button("Mine Patterns"):
        with st.spinner("Mining patterns..."):
            patterns = components['patterns'].mine_patterns(days=days, min_support=min_support)
        
        if patterns:
            st.success(f"Found {len(patterns)} pattern(s)")
            
            for i, p in enumerate(patterns, 1):
                with st.expander(f"{i}. {p['pattern']} ({p['occurrences']}x)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Occurrences", p['occurrences'])
                    with col2:
                        st.metric("Avg Cascade Time", f"{p['avg_cascade_time_seconds']:.0f}s")
        else:
            st.info("No patterns found")

# ===== TIMELINE VIEWER =====
elif page == "🕐 Timeline Viewer":
    st.title("🕐 Timeline Viewer")
    
    incident_id = st.number_input("Incident ID", min_value=1, value=1)
    
    col1, col2 = st.columns(2)
    with col1:
        minutes_before = st.slider("Minutes before", 5, 30, 10)
    with col2:
        minutes_after = st.slider("Minutes after", 1, 15, 5)
    
    if st.button("Load Timeline"):
        timeline = components['timeline'].get_timeline(
            incident_id, 
            minutes_before=minutes_before,
            minutes_after=minutes_after
        )
        
        if timeline:
            st.subheader(f"Timeline for Incident #{incident_id}")
            
            # Original sin
            if timeline['original_sin']:
                os = timeline['original_sin']
                st.warning(f"🔍 **Original Sin**: {os['minutes_from_target']:.1f} min before - {os['message']}")
            
            # Events
            st.write(f"**Total events:** {timeline['total_events']}")
            
            for event in timeline['events']:
                if event['is_target']:
                    st.success(f"🎯 **TARGET** [{event['severity']}] {event['message']}")
                else:
                    color = "error" if event['severity'] == 'ERROR' else "info"
                    time_marker = f"{event['minutes_from_target']:+.1f}min"
                    st.write(f"{time_marker} [{event['severity']}] {event['message']}")
        else:
            st.error(f"Incident #{incident_id} not found")