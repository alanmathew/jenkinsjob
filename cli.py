#!/usr/bin/env python3
"""
Command-line interface for Jenkins data collection and analysis.

Usage:
    python cli.py collect                    # Collect Jenkins data
    python cli.py analyze                    # Analyze collected data
    python cli.py predict                    # Generate ML predictions
    python cli.py report                     # Generate summary report
    python cli.py --help                     # Show help
"""

import argparse
import sys
import os
import logging
from datetime import datetime

from jenkins_client import JenkinsClient
from data_collector import JenkinsDataCollector
from analysis import JenkinsAnalyzer


def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def collect_data(args):
    """Collect Jenkins data."""
    print("🔄 Starting Jenkins data collection...")
    
    try:
        collector = JenkinsDataCollector()
        
        # Test connection
        if not collector.client.test_connection():
            print("❌ Failed to connect to Jenkins")
            print("💡 Make sure Jenkins is running and credentials are configured")
            return False
        
        # Collect data
        data = collector.collect_all_data()
        
        # Print summary
        summary = data.get('summary', {})
        print(f"\n✅ Data collection completed!")
        print(f"📊 Summary:")
        print(f"   • Jobs: {summary.get('total_jobs', 0)}")
        print(f"   • Builds: {summary.get('total_builds', 0)}")
        print(f"   • Queue items: {summary.get('queue_length', 0)}")
        print(f"   • Nodes: {summary.get('total_nodes', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        if args.verbose:
            logging.exception("Collection error details:")
        return False


def analyze_data(args):
    """Analyze collected Jenkins data."""
    print("🔍 Starting Jenkins data analysis...")
    
    try:
        analyzer = JenkinsAnalyzer()
        
        # Load data
        data = analyzer.load_data()
        jobs_count = len(data.get('jobs', []))
        
        if jobs_count == 0:
            print("❌ No data found. Run 'collect' command first.")
            return False
        
        print(f"📊 Analyzing {jobs_count} jobs...")
        
        # Create feature matrix
        features_df = analyzer.create_feature_matrix(data)
        if not features_df.empty:
            print(f"✅ Feature matrix: {len(features_df)} builds, {len(features_df.columns)} features")
        
        # Analyze failure patterns
        failure_analysis = analyzer.analyze_failure_patterns(data)
        failure_jobs = len(failure_analysis.get('failure_by_job', {}))
        print(f"✅ Failure analysis: {failure_jobs} jobs analyzed")
        
        # Time-based metrics
        daily_metrics = analyzer.calculate_build_metrics_over_time(data, 'daily')
        if not daily_metrics.empty:
            print(f"✅ Daily metrics: {len(daily_metrics)} days analyzed")
        
        print(f"\n🎯 Analysis completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            logging.exception("Analysis error details:")
        return False


def generate_predictions(args):
    """Generate ML predictions for build outcomes."""
    print("🤖 Generating ML predictions...")
    
    try:
        # Check if ML libraries are available
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, roc_auc_score
        except ImportError:
            print("❌ ML libraries not available")
            print("💡 Install with: pip install scikit-learn")
            return False
        
        analyzer = JenkinsAnalyzer()
        
        # Generate prediction dataset
        X, y = analyzer.generate_build_prediction_dataset()
        
        if X.empty or len(X) < 50:
            print(f"❌ Insufficient data for ML (need ≥50 builds, have {len(X)})")
            return False
        
        print(f"📊 Dataset: {len(X)} builds, {len(X.columns)} features")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"🏆 Model Performance:")
        print(f"   • Accuracy: {accuracy:.3f}")
        print(f"   • AUC Score: {auc:.3f}")
        print(f"   • Success Rate: {y.mean():.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        if args.verbose:
            logging.exception("Prediction error details:")
        return False


def generate_report(args):
    """Generate summary report."""
    print("📋 Generating Jenkins summary report...")
    
    try:
        analyzer = JenkinsAnalyzer()
        data = analyzer.load_data()
        
        jobs = data.get('jobs', [])
        if not jobs:
            print("❌ No data found. Run 'collect' command first.")
            return False
        
        print(f"\n📊 Jenkins Analysis Report")
        print(f"={'=' * 50}")
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data collection: {data.get('collection_timestamp', 'Unknown')}")
        
        # Overview
        summary = data.get('summary', {})
        print(f"\n🔍 Overview:")
        print(f"   Total Jobs: {summary.get('total_jobs', 0)}")
        print(f"   Total Builds: {summary.get('total_builds', 0)}")
        print(f"   Queue Length: {summary.get('queue_length', 0)}")
        print(f"   Total Nodes: {summary.get('total_nodes', 0)}")
        print(f"   Offline Nodes: {summary.get('offline_nodes', 0)}")
        
        # Job metrics
        job_metrics = summary.get('job_metrics_summary', {})
        if job_metrics:
            print(f"\n📈 Build Performance:")
            print(f"   Overall Success Rate: {job_metrics.get('overall_success_rate', 0):.1%}")
            print(f"   Average Duration: {job_metrics.get('avg_build_duration_minutes', 0):.1f} min")
            print(f"   Jobs with Recent Failures: {job_metrics.get('jobs_with_recent_failures', 0)}")
        
        # Top performing and failing jobs
        job_stats = []
        for job in jobs:
            metrics = job.get('metrics', {})
            if metrics:
                job_stats.append({
                    'name': job.get('name'),
                    'success_rate': metrics.get('success_rate', 0),
                    'total_builds': metrics.get('total_builds', 0),
                    'avg_duration': metrics.get('avg_duration_minutes', 0)
                })
        
        if job_stats:
            # Top 5 most successful jobs
            job_stats.sort(key=lambda x: x['success_rate'], reverse=True)
            print(f"\n🏆 Top 5 Most Successful Jobs:")
            for i, job in enumerate(job_stats[:5], 1):
                print(f"   {i}. {job['name']}: {job['success_rate']:.1%} ({job['total_builds']} builds)")
            
            # Top 5 most problematic jobs
            problem_jobs = [j for j in job_stats if j['success_rate'] < 1.0]
            problem_jobs.sort(key=lambda x: x['success_rate'])
            if problem_jobs:
                print(f"\n⚠️  Top 5 Most Problematic Jobs:")
                for i, job in enumerate(problem_jobs[:5], 1):
                    print(f"   {i}. {job['name']}: {job['success_rate']:.1%} ({job['total_builds']} builds)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if job_metrics.get('jobs_with_recent_failures', 0) > 0:
            print(f"   • Investigate {job_metrics.get('jobs_with_recent_failures')} jobs with recent failures")
        
        if summary.get('offline_nodes', 0) > 0:
            print(f"   • Check {summary.get('offline_nodes')} offline nodes")
        
        if summary.get('queue_length', 0) > 5:
            print(f"   • Long build queue ({summary.get('queue_length')} items) - consider adding capacity")
        
        overall_success = job_metrics.get('overall_success_rate', 1.0)
        if overall_success < 0.8:
            print(f"   • Overall success rate is low ({overall_success:.1%}) - review build processes")
        
        print(f"\n✅ Report generated successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        if args.verbose:
            logging.exception("Report error details:")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Jenkins Data Analysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s collect                 # Collect Jenkins data
  %(prog)s analyze                 # Analyze collected data  
  %(prog)s predict                 # Generate ML predictions
  %(prog)s report                  # Generate summary report
  %(prog)s collect --verbose       # Collect with detailed logging
        """
    )
    
    parser.add_argument(
        'command',
        choices=['collect', 'analyze', 'predict', 'report'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Check config file exists
    if not os.path.exists(args.config):
        print(f"❌ Configuration file not found: {args.config}")
        print(f"💡 Make sure config.yaml exists in the current directory")
        return 1
    
    # Execute command
    success = False
    
    if args.command == 'collect':
        success = collect_data(args)
    elif args.command == 'analyze':
        success = analyze_data(args)
    elif args.command == 'predict':
        success = generate_predictions(args)
    elif args.command == 'report':
        success = generate_report(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())