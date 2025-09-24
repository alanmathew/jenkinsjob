#!/usr/bin/env python3
"""
Example script to analyze Jenkins build patterns for AI/ML insights.

Usage:
    python analyze_build_patterns.py [data_file.json]
    
If no data file is specified, the most recent data file will be used.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import JenkinsAnalyzer
import logging

def main():
    """Main function to analyze Jenkins build patterns."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Jenkins Build Pattern Analyzer")
    print("=============================")
    
    try:
        # Initialize analyzer
        analyzer = JenkinsAnalyzer()
        
        # Load data
        data_file = sys.argv[1] if len(sys.argv) > 1 else None
        print(f"📊 Loading Jenkins data...")
        data = analyzer.load_data(data_file)
        
        print(f"✅ Data loaded successfully!")
        print(f"   • Collection timestamp: {data.get('collection_timestamp', 'Unknown')}")
        print(f"   • Total jobs: {len(data.get('jobs', []))}")
        
        # 1. Create feature matrix for ML
        print(f"\n🧠 Creating feature matrix for ML/AI analysis...")
        features_df = analyzer.create_feature_matrix(data)
        
        if not features_df.empty:
            print(f"   • Features created: {len(features_df.columns)} columns, {len(features_df)} rows")
            print(f"   • Success rate in dataset: {features_df['is_success'].mean():.2%}")
        
        # 2. Analyze failure patterns
        print(f"\n🔍 Analyzing failure patterns...")
        failure_analysis = analyzer.analyze_failure_patterns(data)
        
        # Display top failing jobs
        failure_by_job = failure_analysis.get('failure_by_job', {})
        if failure_by_job:
            print(f"\n❌ Top Failing Jobs:")
            sorted_jobs = sorted(failure_by_job.items(), 
                               key=lambda x: x[1]['failure_rate'], reverse=True)[:5]
            
            for job_name, stats in sorted_jobs:
                failure_rate = stats['failure_rate']
                total_builds = stats['total_builds']
                print(f"   • {job_name}: {failure_rate:.1%} failure rate ({total_builds} builds)")
        
        # 3. Generate prediction dataset
        print(f"\n🎯 Generating prediction dataset for ML models...")
        X, y = analyzer.generate_build_prediction_dataset(data)
        
        if not X.empty:
            print(f"   • Feature matrix shape: {X.shape}")
            print(f"   • Target distribution: Success={y.sum()}, Failure={len(y)-y.sum()}")
            print(f"   • Class balance: {y.mean():.2%} success rate")
        
        print(f"\n✅ Build pattern analysis completed!")
        print(f"📁 Analysis results saved to: {analyzer.output_dir}/")
        
    except FileNotFoundError as e:
        print(f"❌ Data file not found: {e}")
        print(f"💡 Run 'python collect_jenkins_data.py' first to collect data")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        logging.error(f"Analysis failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()