"""
Trend analyzer for generating topic frequency reports
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


class TrendAnalyzer:
    def __init__(self):
        """
        Initialize the trend analyzer
        """
        self.topic_frequencies = defaultdict(lambda: defaultdict(int))

    def add_daily_data(self, date: str, extraction_results: List[Dict]):
        """
        Add extraction results for a specific date

        Args:
            date: Date string in YYYY-MM-DD format
            extraction_results: List of extraction results with canonical topics
        """
        # Count topic frequencies for this date
        topic_counts = defaultdict(int)

        for result in extraction_results:
            for topic in result['topics']:
                topic_counts[topic] += 1

        # Store in the main data structure
        for topic, count in topic_counts.items():
            self.topic_frequencies[topic][date] = count

    def generate_trend_report(
            self,
            target_date: datetime,
            lookback_days: int = 30
    ) -> pd.DataFrame:
        """
        Generate trend report for the last N days up to target date

        Args:
            target_date: End date for the report
            lookback_days: Number of days to look back (default 30)

        Returns:
            DataFrame with topics as rows and dates as columns
        """
        # Generate date range
        start_date = target_date - timedelta(days=lookback_days)
        date_range = []
        current = start_date

        while current <= target_date:
            date_range.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        # Get all topics
        all_topics = sorted(self.topic_frequencies.keys())

        # Build the report data
        report_data = {}

        for topic in all_topics:
            topic_row = []
            for date in date_range:
                count = self.topic_frequencies[topic].get(date, 0)
                topic_row.append(count)
            report_data[topic] = topic_row

        # Create DataFrame
        df = pd.DataFrame(report_data, index=date_range).T
        df.index.name = 'Topic'

        # Sort by total frequency (descending)
        df['Total'] = df.sum(axis=1)
        df = df.sort_values('Total', ascending=False)
        df = df.drop('Total', axis=1)

        return df

    def get_trending_topics(
            self,
            target_date: datetime,
            lookback_days: int = 30,
            top_n: int = 10
    ) -> List[Dict]:
        """
        Get the top trending topics

        Args:
            target_date: End date for analysis
            lookback_days: Number of days to analyze
            top_n: Number of top topics to return

        Returns:
            List of dictionaries with topic and frequency info
        """
        start_date = target_date - timedelta(days=lookback_days)

        topic_totals = {}

        for topic, dates in self.topic_frequencies.items():
            total = 0
            current = start_date
            while current <= target_date:
                date_str = current.strftime('%Y-%m-%d')
                total += dates.get(date_str, 0)
                current += timedelta(days=1)

            if total > 0:
                topic_totals[topic] = total

        # Sort and get top N
        sorted_topics = sorted(
            topic_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {'topic': topic, 'frequency': freq}
            for topic, freq in sorted_topics
        ]

    def get_emerging_topics(
            self,
            target_date: datetime,
            recent_days: int = 7,
            older_days: int = 23
    ) -> List[Dict]:
        """
        Identify emerging topics (more frequent recently vs earlier)

        Args:
            target_date: End date for analysis
            recent_days: Days to consider as "recent"
            older_days: Days to consider as "older" period

        Returns:
            List of emerging topics with growth metrics
        """
        recent_start = target_date - timedelta(days=recent_days - 1)
        older_start = target_date - timedelta(days=recent_days + older_days - 1)
        older_end = target_date - timedelta(days=recent_days)

        emerging = []

        for topic, dates in self.topic_frequencies.items():
            # Calculate recent frequency
            recent_freq = 0
            current = recent_start
            while current <= target_date:
                date_str = current.strftime('%Y-%m-%d')
                recent_freq += dates.get(date_str, 0)
                current += timedelta(days=1)

            # Calculate older frequency
            older_freq = 0
            current = older_start
            while current <= older_end:
                date_str = current.strftime('%Y-%m-%d')
                older_freq += dates.get(date_str, 0)
                current += timedelta(days=1)

            # Calculate growth
            if older_freq > 0:
                growth_rate = (recent_freq - older_freq) / older_freq
                if growth_rate > 0.5:  # 50% increase
                    emerging.append({
                        'topic': topic,
                        'recent_frequency': recent_freq,
                        'older_frequency': older_freq,
                        'growth_rate': growth_rate
                    })
            elif recent_freq >= 3:  # New topic with decent volume
                emerging.append({
                    'topic': topic,
                    'recent_frequency': recent_freq,
                    'older_frequency': 0,
                    'growth_rate': float('inf')
                })

        # Sort by growth rate
        emerging.sort(key=lambda x: x['growth_rate'], reverse=True)

        return emerging

    def export_to_csv(self, df: pd.DataFrame, output_path: str):
        """
        Export trend report to CSV

        Args:
            df: DataFrame to export
            output_path: Path to save CSV file
        """
        df.to_csv(output_path)
        print(f"Trend report exported to {output_path}")