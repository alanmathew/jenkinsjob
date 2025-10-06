#!/usr/bin/env python3
"""
Example script to collect Jenkins data for analysis.

Usage:
    python collect_jenkins_data.py
    
Make sure to:
1. Copy .env.example to .env and configure your Jenkins credentials
2. Modify config.yaml as needed for your Jenkins setup
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import JenkinsDataCollector
import logging

def main():
    """Main function to collect Jenkins data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Jenkins Data Collector")
    print("=====================")
    
    try:
        # Initialize collector
        collector = JenkinsDataCollector()
        
        # Test connection first
        if not collector.client.test_connection():
            print("❌ Failed to connect to Jenkins. Please check your configuration.")
            print("Make sure to:")
            print("1. Copy .env.example to .env")
            print("2. Set JENKINS_URL, JENKINS_USER, and JENKINS_TOKEN in .env")
            print("3. Verify Jenkins is accessible")
            return
        
        print("✅ Connected to Jenkins successfully!")
        
        # Collect all data
        print("\n📊 Starting data collection...")
        data = collector.collect_all_data()
        
        # Print summary
        summary = data.get('summary', {})
        print(f"\n📈 Collection Summary:")
        print(f"   • Total Jobs: {summary.get('total_jobs', 0)}")
        print(f"   • Total Builds: {summary.get('total_builds', 0)}")
        print(f"   • Queue Length: {summary.get('queue_length', 0)}")
        print(f"   • Total Nodes: {summary.get('total_nodes', 0)}")
        print(f"   • Offline Nodes: {summary.get('offline_nodes', 0)}")
        
        job_metrics = summary.get('job_metrics_summary', {})
        if job_metrics:
            print(f"   • Overall Success Rate: {job_metrics.get('overall_success_rate', 0):.2%}")
            print(f"   • Jobs with Recent Failures: {job_metrics.get('jobs_with_recent_failures', 0)}")
        
        print(f"\n✅ Data collection completed successfully!")
        print(f"📁 Data saved to: {collector.output_dir}/")
        
    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        logging.error(f"Data collection failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()