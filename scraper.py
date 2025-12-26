"""
Review scraper for Google Play Store
"""
from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
from typing import List, Dict
import time
from tqdm import tqdm


class ReviewScraper:
    def __init__(self, app_id: str):
        """
        Initialize the scraper for a specific app

        Args:
            app_id: Google Play Store app ID (e.g., 'in.swiggy.android')
        """
        self.app_id = app_id

    def scrape_reviews_by_date_range(
            self,
            start_date: datetime,
            end_date: datetime,
            max_reviews_per_day: int = 1000
    ) -> Dict[str, List[Dict]]:
        """
        Scrape reviews for a date range, organized by date

        Args:
            start_date: Start date for scraping
            end_date: End date for scraping
            max_reviews_per_day: Maximum reviews to fetch per day

        Returns:
            Dictionary with dates as keys and lists of reviews as values
        """
        print(f"Scraping reviews for {self.app_id} from {start_date.date()} to {end_date.date()}")

        # Fetch reviews sorted by newest
        all_reviews = []
        continuation_token = None

        # Fetch in batches until we have enough reviews covering our date range
        while True:
            try:
                result, continuation_token = reviews(
                    self.app_id,
                    lang='en',
                    country='us',
                    sort=Sort.NEWEST,
                    count=200,
                    continuation_token=continuation_token
                )

                all_reviews.extend(result)

                # Check if we've gone back far enough
                if result and result[-1]['at'] < start_date:
                    break

                if not continuation_token:
                    break

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"Error fetching reviews: {e}")
                break

        # Organize reviews by date
        reviews_by_date = {}
        current_date = start_date

        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            reviews_by_date[date_key] = []
            current_date += timedelta(days=1)

        # Filter and organize reviews
        for review in all_reviews:
            review_date = review['at']
            if start_date <= review_date <= end_date:
                date_key = review_date.strftime('%Y-%m-%d')
                if date_key in reviews_by_date:
                    reviews_by_date[date_key].append({
                        'content': review['content'],
                        'score': review['score'],
                        'at': review['at'].isoformat(),
                        'reviewId': review['reviewId']
                    })

        # Print statistics
        total_reviews = sum(len(revs) for revs in reviews_by_date.values())
        print(f"Total reviews scraped: {total_reviews}")
        print(f"Date range: {len(reviews_by_date)} days")

        return reviews_by_date

    def scrape_single_day(self, target_date: datetime) -> List[Dict]:
        """
        Scrape reviews for a single day

        Args:
            target_date: Date to scrape reviews for

        Returns:
            List of reviews for that date
        """
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        reviews_by_date = self.scrape_reviews_by_date_range(start_date, end_date)
        date_key = target_date.strftime('%Y-%m-%d')

        return reviews_by_date.get(date_key, [])