"""
Main pipeline for AI-powered trend analysis
"""
import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm

from scraper import ReviewScraper
from topic_extractor import TopicExtractor
from topic_consolidator import TopicConsolidator
from trend_analyzer import TrendAnalyzer


def load_seed_topics(seed_file: str = None) -> list:
    """Load seed topics from file if provided"""
    if seed_file and os.path.exists(seed_file):
        with open(seed_file, 'r') as f:
            return json.load(f)

    # Default seed topics for food delivery apps
    return [
        "Delivery issue",
        "Food stale",
        "Food cold",
        "Delivery partner rude",
        "Wrong order delivered",
        "Maps not working properly",
        "App crashes",
        "Payment failed",
        "Refund not received",
        "Customer support unresponsive",
        "Late delivery",
        "Missing items",
        "Food quality poor",
        "Packaging damaged"
    ]


def main():
    parser = argparse.ArgumentParser(
        description='AI-powered trend analysis for app reviews'
    )
    parser.add_argument(
        '--app-id',
        required=True,
        help='Google Play Store app ID (e.g., in.swiggy.android)'
    )
    parser.add_argument(
        '--target-date',
        required=True,
        help='Target date for analysis (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--seed-topics',
        help='Path to JSON file with seed topics'
    )
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory for reports'
    )

    args = parser.parse_args()

    # Parse target date
    target_date = datetime.strptime(args.target_date, '%Y-%m-%d')

    # ALWAYS use 30-day lookback from target date (T-30 to T)
    lookback_days = 30
    start_date = target_date - timedelta(days=lookback_days)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("AI-POWERED TREND ANALYSIS SYSTEM")
    print("=" * 80)
    print(f"App ID: {args.app_id}")
    print(f"Target Date (T): {target_date.date()}")
    print(f"Analysis Period: {start_date.date()} to {target_date.date()} (30 days)")
    print("=" * 80)

    # Initialize components
    print("\n[1/5] Initializing AI agents...")
    scraper = ReviewScraper(args.app_id)
    seed_topics = load_seed_topics(args.seed_topics)
    extractor = TopicExtractor(seed_topics=seed_topics)
    consolidator = TopicConsolidator()
    analyzer = TrendAnalyzer()

    print(f"Loaded {len(seed_topics)} seed topics")

    # Scrape reviews for the 30-day period
    print(f"\n[2/5] Scraping reviews from Google Play Store...")
    print(f"Fetching reviews from {start_date.date()} to {target_date.date()}")
    reviews_by_date = scraper.scrape_reviews_by_date_range(
        start_date,
        target_date  # Fetch enough reviews to cover 30 days
    )

    # Check if we have any reviews
    total_reviews = sum(len(revs) for revs in reviews_by_date.values())
    if total_reviews == 0:
        print("\n" + "=" * 80)
        print("ERROR: No reviews found in the specified date range!")
        print("=" * 80)
        print("\nPlease try:")
        print("1. Using a more recent date range (last 30 days from today)")
        print("2. Verifying the app ID is correct")
        print("3. Checking if the app has recent reviews")
        return

    # Process each day in the 30-day window
    print(f"\n[3/5] Processing daily batches with AI agents...")
    print(f"Processing {total_reviews} reviews across {lookback_days + 1} days")

    current_date = start_date
    days_processed = 0

    with tqdm(total=lookback_days + 1, desc="Processing days") as pbar:
        while current_date <= target_date:
            date_key = current_date.strftime('%Y-%m-%d')
            daily_reviews = reviews_by_date.get(date_key, [])

            if daily_reviews:
                days_processed += 1
                # Extract topics
                extraction_results = extractor.extract_topics_from_batch(daily_reviews)

                # Get unique topics from this batch
                unique_topics = extractor.get_all_unique_topics(extraction_results)

                # Consolidate topics (agent builds/updates taxonomy)
                topic_mapping = consolidator.consolidate_topics(unique_topics)

                # Apply mapping to results
                mapped_results = consolidator.apply_mapping(extraction_results)

                # Add to trend analyzer
                analyzer.add_daily_data(date_key, mapped_results)

            current_date += timedelta(days=1)
            pbar.update(1)

    print(f"Processed {days_processed} days with reviews")

    # Generate trend report for the 30-day period (T-30 to T)
    print(f"\n[4/5] Generating trend report...")
    trend_df = analyzer.generate_trend_report(target_date, lookback_days)

    # Get insights
    top_topics = analyzer.get_trending_topics(target_date, lookback_days, top_n=10)
    emerging_topics = analyzer.get_emerging_topics(target_date)

    # Save outputs
    print(f"\n[5/5] Saving outputs...")

    # Save trend report
    report_path = output_dir / f"trend_report_{args.target_date}.csv"
    analyzer.export_to_csv(trend_df, str(report_path))

    # Save topic mapping
    mapping_path = output_dir / f"topic_mapping_{args.target_date}.json"
    with open(mapping_path, 'w') as f:
        json.dump(consolidator.get_topic_mapping(), f, indent=2)

    # Save metadata and insights
    metadata = {
        'app_id': args.app_id,
        'target_date': args.target_date,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'lookback_days': lookback_days,
        'total_reviews_processed': total_reviews,
        'days_with_reviews': days_processed,
        'total_canonical_topics': len(consolidator.get_canonical_topics()),
        'top_topics': top_topics,
        'emerging_topics': emerging_topics[:5] if emerging_topics else []
    }

    metadata_path = output_dir / f"metadata_{args.target_date}.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nTotal reviews processed: {total_reviews}")
    print(f"Days with reviews: {days_processed} out of {lookback_days + 1}")
    print(f"Total canonical topics identified: {len(consolidator.get_canonical_topics())}")

    print(f"\nTop 5 Trending Topics:")
    for i, item in enumerate(top_topics[:5], 1):
        print(f"  {i}. {item['topic']}: {item['frequency']} occurrences")

    if emerging_topics:
        print(f"\nTop 3 Emerging Topics:")
        for i, item in enumerate(emerging_topics[:3], 1):
            growth = f"{item['growth_rate']:.1%}" if item['growth_rate'] != float('inf') else "NEW"
            print(f"  {i}. {item['topic']}: {growth} growth")

    print(f"\nOutputs saved to: {output_dir}")
    print(f"  - {report_path.name}")
    print(f"  - {mapping_path.name}")
    print(f"  - {metadata_path.name}")
    print("=" * 80)

    print("\nTrend Report Preview (first 10 topics):")
    print(trend_df.head(10).to_string())


if __name__ == "__main__":
    main()