"""
Analysis module for Jenkins data with ML/AI features.
"""

import os
import json
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import yaml


class JenkinsAnalyzer:
    """Analyzes Jenkins data and prepares features for ML/AI."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """Initialize analyzer."""
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = self.config['data_collection']['output']['directory']
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_data(self, data_file: str = None) -> Dict[str, Any]:
        """Load Jenkins data from JSON file."""
        if not data_file:
            # Find the most recent data file
            data_files = [f for f in os.listdir(self.output_dir) if f.startswith('complete_jenkins_data') and f.endswith('.json')]
            if not data_files:
                raise FileNotFoundError("No Jenkins data files found")
            data_file = max(data_files)
        
        data_path = os.path.join(self.output_dir, data_file)
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        logging.info(f"Loaded data from {data_path}")
        return data
    
    def create_feature_matrix(self, data: Dict[str, Any] = None) -> pd.DataFrame:
        """Create feature matrix for ML/AI analysis."""
        if data is None:
            data = self.load_data()
        
        logging.info("Creating feature matrix for ML/AI analysis...")
        
        features = []
        
        for job in data.get('jobs', []):
            job_name = job.get('name')
            builds = job.get('builds', [])
            
            if not builds:
                continue
            
            # Create features for each build
            for i, build in enumerate(builds):
                try:
                    feature_row = self._extract_build_features(job_name, build, builds, i)
                    features.append(feature_row)
                except Exception as e:
                    logging.warning(f"Failed to extract features for build {build.get('number', 'unknown')}: {e}")
                    continue
        
        if not features:
            logging.warning("No features extracted")
            return pd.DataFrame()
        
        df = pd.DataFrame(features)
        
        # Save feature matrix
        timestamp = datetime.now().strftime(self.config['data_collection']['output']['timestamp_format'])
        feature_file = os.path.join(self.output_dir, f"feature_matrix_{timestamp}.csv")
        df.to_csv(feature_file, index=False)
        
        logging.info(f"Feature matrix created with {len(df)} rows and {len(df.columns)} columns")
        logging.info(f"Feature matrix saved to {feature_file}")
        
        return df
    
    def _extract_build_features(self, job_name: str, build: Dict[str, Any], 
                              all_builds: List[Dict[str, Any]], build_index: int) -> Dict[str, Any]:
        """Extract ML features from a single build."""
        features = {}
        
        # Basic build information
        features['job_name'] = job_name
        features['build_number'] = build.get('number', 0)
        features['result'] = build.get('result', 'UNKNOWN')
        features['duration_minutes'] = build.get('duration_minutes', 0)
        features['timestamp'] = build.get('timestamp', 0)
        
        # Binary success indicator (target variable for classification)
        features['is_success'] = 1 if build.get('result') == 'SUCCESS' else 0
        features['is_failure'] = 1 if build.get('result') == 'FAILURE' else 0
        features['is_unstable'] = 1 if build.get('result') == 'UNSTABLE' else 0
        features['is_aborted'] = 1 if build.get('result') == 'ABORTED' else 0
        
        # Time-based features
        if build.get('timestamp'):
            dt = datetime.fromtimestamp(build.get('timestamp') / 1000)
            features['hour_of_day'] = dt.hour
            features['day_of_week'] = dt.weekday()
            features['day_of_month'] = dt.day
            features['month'] = dt.month
            features['is_weekend'] = 1 if dt.weekday() >= 5 else 0
            features['is_business_hours'] = 1 if 9 <= dt.hour <= 17 else 0
        
        # Build characteristics
        features['has_artifacts'] = 1 if build.get('artifacts', 0) > 0 else 0
        features['artifacts_count'] = build.get('artifacts', 0)
        features['estimated_duration'] = build.get('estimated_duration', 0) / (1000 * 60)  # Convert to minutes
        features['console_log_size_kb'] = build.get('console_log_size', 0) / 1024
        
        # Test results features
        test_results = build.get('test_results', {})
        features['total_tests'] = test_results.get('total_tests', 0)
        features['failed_tests'] = test_results.get('failed_tests', 0)
        features['passed_tests'] = test_results.get('passed_tests', 0)
        features['test_failure_rate'] = test_results.get('failed_tests', 0) / max(test_results.get('total_tests', 1), 1)
        features['has_tests'] = 1 if test_results.get('total_tests', 0) > 0 else 0
        
        # Historical features (based on previous builds)
        historical_features = self._extract_historical_features(all_builds, build_index)
        features.update(historical_features)
        
        # Build trigger features
        causes = build.get('causes', [])
        features['triggered_by_user'] = 1 if any('User' in cause.get('class', '') for cause in causes) else 0
        features['triggered_by_scm'] = 1 if any('SCM' in cause.get('class', '') for cause in causes) else 0
        features['triggered_by_timer'] = 1 if any('Timer' in cause.get('class', '') for cause in causes) else 0
        features['triggered_by_upstream'] = 1 if any('Upstream' in cause.get('class', '') for cause in causes) else 0
        
        # Build parameters features
        parameters = build.get('parameters', {})
        features['has_parameters'] = 1 if parameters else 0
        features['parameter_count'] = len(parameters)
        
        # Node/executor features
        features['built_on_master'] = 1 if build.get('built_on', '').lower() in ['master', ''] else 0
        features['executor_number'] = build.get('executor', {}).get('number', -1) if build.get('executor') else -1
        
        return features
    
    def _extract_historical_features(self, all_builds: List[Dict[str, Any]], 
                                   current_index: int, lookback_window: int = 10) -> Dict[str, Any]:
        """Extract features based on build history."""
        features = {}
        
        # Get previous builds (more recent builds have lower indices)
        previous_builds = all_builds[current_index + 1:current_index + 1 + lookback_window]
        
        if not previous_builds:
            # No history available
            features.update({
                'prev_success_rate': 0.5,  # Neutral prior
                'prev_avg_duration': 0,
                'prev_builds_count': 0,
                'days_since_last_build': 0,
                'consecutive_failures': 0,
                'consecutive_successes': 0,
                'trend_duration': 0,
                'prev_failure_rate': 0.5
            })
            return features
        
        # Calculate historical metrics
        prev_results = [b.get('result') for b in previous_builds if b.get('result')]
        prev_durations = [b.get('duration_minutes', 0) for b in previous_builds if b.get('duration_minutes')]
        
        # Success/failure rates
        if prev_results:
            success_count = sum(1 for r in prev_results if r == 'SUCCESS')
            failure_count = sum(1 for r in prev_results if r == 'FAILURE')
            features['prev_success_rate'] = success_count / len(prev_results)
            features['prev_failure_rate'] = failure_count / len(prev_results)
        else:
            features['prev_success_rate'] = 0.5
            features['prev_failure_rate'] = 0.5
        
        # Duration statistics
        features['prev_avg_duration'] = np.mean(prev_durations) if prev_durations else 0
        features['prev_max_duration'] = np.max(prev_durations) if prev_durations else 0
        features['prev_min_duration'] = np.min(prev_durations) if prev_durations else 0
        features['prev_std_duration'] = np.std(prev_durations) if len(prev_durations) > 1 else 0
        
        # Build count
        features['prev_builds_count'] = len(previous_builds)
        
        # Time since last build
        if previous_builds and previous_builds[0].get('timestamp'):
            current_timestamp = all_builds[current_index].get('timestamp', 0)
            last_timestamp = previous_builds[0].get('timestamp', 0)
            features['days_since_last_build'] = (current_timestamp - last_timestamp) / (1000 * 60 * 60 * 24)
        else:
            features['days_since_last_build'] = 0
        
        # Consecutive outcomes
        consecutive_failures = 0
        consecutive_successes = 0
        
        for build in previous_builds:
            result = build.get('result')
            if result == 'FAILURE':
                consecutive_failures += 1
                break
            elif result == 'SUCCESS':
                consecutive_successes += 1
            else:
                break
        
        features['consecutive_failures'] = consecutive_failures
        features['consecutive_successes'] = consecutive_successes
        
        # Duration trend (slope of last few builds)
        if len(prev_durations) >= 3:
            x = np.arange(len(prev_durations))
            slope, _ = np.polyfit(x, prev_durations, 1)
            features['trend_duration'] = slope
        else:
            features['trend_duration'] = 0
        
        return features
    
    def analyze_failure_patterns(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze failure patterns in Jenkins builds."""
        if data is None:
            data = self.load_data()
        
        logging.info("Analyzing failure patterns...")
        
        failure_analysis = {
            'failure_by_job': {},
            'failure_by_time': {},
            'failure_by_node': {},
            'failure_causes': {},
            'failure_trends': {}
        }
        
        all_builds = []
        
        # Collect all builds
        for job in data.get('jobs', []):
            job_name = job.get('name')
            for build in job.get('builds', []):
                build['job_name'] = job_name
                all_builds.append(build)
        
        if not all_builds:
            return failure_analysis
        
        # Analyze failures by job
        job_failures = {}
        for build in all_builds:
            job_name = build['job_name']
            result = build.get('result')
            
            if job_name not in job_failures:
                job_failures[job_name] = {'total': 0, 'failures': 0, 'successes': 0}
            
            job_failures[job_name]['total'] += 1
            if result == 'FAILURE':
                job_failures[job_name]['failures'] += 1
            elif result == 'SUCCESS':
                job_failures[job_name]['successes'] += 1
        
        # Calculate failure rates
        for job_name, stats in job_failures.items():
            failure_rate = stats['failures'] / stats['total'] if stats['total'] > 0 else 0
            failure_analysis['failure_by_job'][job_name] = {
                'total_builds': stats['total'],
                'failures': stats['failures'],
                'failure_rate': failure_rate,
                'success_rate': stats['successes'] / stats['total'] if stats['total'] > 0 else 0
            }
        
        # Analyze failures by time patterns
        time_failures = self._analyze_time_patterns(all_builds)
        failure_analysis['failure_by_time'] = time_failures
        
        # Analyze failures by node
        node_failures = {}
        for build in all_builds:
            node = build.get('built_on', 'unknown')
            result = build.get('result')
            
            if node not in node_failures:
                node_failures[node] = {'total': 0, 'failures': 0}
            
            node_failures[node]['total'] += 1
            if result == 'FAILURE':
                node_failures[node]['failures'] += 1
        
        for node, stats in node_failures.items():
            failure_rate = stats['failures'] / stats['total'] if stats['total'] > 0 else 0
            failure_analysis['failure_by_node'][node] = {
                'total_builds': stats['total'],
                'failures': stats['failures'],
                'failure_rate': failure_rate
            }
        
        # Save analysis results
        timestamp = datetime.now().strftime(self.config['data_collection']['output']['timestamp_format'])
        analysis_file = os.path.join(self.output_dir, f"failure_analysis_{timestamp}.json")
        
        with open(analysis_file, 'w') as f:
            json.dump(failure_analysis, f, indent=2, default=str)
        
        logging.info(f"Failure analysis saved to {analysis_file}")
        return failure_analysis
    
    def _analyze_time_patterns(self, builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze failure patterns by time."""
        time_patterns = {
            'hourly_failures': {},
            'daily_failures': {},
            'monthly_failures': {}
        }
        
        for build in builds:
            if not build.get('timestamp') or build.get('result') != 'FAILURE':
                continue
            
            dt = datetime.fromtimestamp(build.get('timestamp') / 1000)
            
            # Hourly patterns
            hour = dt.hour
            if hour not in time_patterns['hourly_failures']:
                time_patterns['hourly_failures'][hour] = 0
            time_patterns['hourly_failures'][hour] += 1
            
            # Daily patterns (day of week)
            day = dt.strftime('%A')
            if day not in time_patterns['daily_failures']:
                time_patterns['daily_failures'][day] = 0
            time_patterns['daily_failures'][day] += 1
            
            # Monthly patterns
            month = dt.strftime('%Y-%m')
            if month not in time_patterns['monthly_failures']:
                time_patterns['monthly_failures'][month] = 0
            time_patterns['monthly_failures'][month] += 1
        
        return time_patterns
    
    def generate_build_prediction_dataset(self, data: Dict[str, Any] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate dataset for build outcome prediction."""
        if data is None:
            data = self.load_data()
        
        logging.info("Generating build prediction dataset...")
        
        # Create feature matrix
        df = self.create_feature_matrix(data)
        
        if df.empty:
            logging.warning("No data available for prediction dataset")
            return pd.DataFrame(), pd.Series()
        
        # Remove non-feature columns
        feature_columns = [col for col in df.columns if col not in [
            'job_name', 'build_number', 'result', 'timestamp', 'is_success', 
            'is_failure', 'is_unstable', 'is_aborted'
        ]]
        
        X = df[feature_columns]
        y = df['is_success']  # Binary classification: success vs. not success
        
        # Handle missing values
        X = X.fillna(0)
        
        # Save dataset
        timestamp = datetime.now().strftime(self.config['data_collection']['output']['timestamp_format'])
        dataset_file = os.path.join(self.output_dir, f"prediction_dataset_{timestamp}.csv")
        
        dataset_df = X.copy()
        dataset_df['target'] = y
        dataset_df.to_csv(dataset_file, index=False)
        
        logging.info(f"Prediction dataset saved to {dataset_file}")
        logging.info(f"Dataset shape: {X.shape}, Target distribution: {y.value_counts().to_dict()}")
        
        return X, y
    
    def calculate_build_metrics_over_time(self, data: Dict[str, Any] = None, 
                                        period: str = 'daily') -> pd.DataFrame:
        """Calculate build metrics aggregated over time periods."""
        if data is None:
            data = self.load_data()
        
        logging.info(f"Calculating {period} build metrics...")
        
        all_builds = []
        for job in data.get('jobs', []):
            job_name = job.get('name')
            for build in job.get('builds', []):
                if build.get('timestamp'):
                    build_data = {
                        'job_name': job_name,
                        'timestamp': build.get('timestamp'),
                        'result': build.get('result'),
                        'duration_minutes': build.get('duration_minutes', 0),
                        'datetime': datetime.fromtimestamp(build.get('timestamp') / 1000)
                    }
                    all_builds.append(build_data)
        
        if not all_builds:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_builds)
        df['date'] = df['datetime'].dt.date
        
        # Group by time period
        if period == 'daily':
            grouped = df.groupby('date')
        elif period == 'weekly':
            df['week'] = df['datetime'].dt.isocalendar().week
            df['year'] = df['datetime'].dt.year
            grouped = df.groupby(['year', 'week'])
        elif period == 'monthly':
            df['month'] = df['datetime'].dt.to_period('M')
            grouped = df.groupby('month')
        else:
            raise ValueError("Period must be 'daily', 'weekly', or 'monthly'")
        
        # Calculate metrics
        metrics = []
        for name, group in grouped:
            total_builds = len(group)
            successful_builds = len(group[group['result'] == 'SUCCESS'])
            failed_builds = len(group[group['result'] == 'FAILURE'])
            avg_duration = group['duration_minutes'].mean()
            
            metric_row = {
                'period': str(name),
                'total_builds': total_builds,
                'successful_builds': successful_builds,
                'failed_builds': failed_builds,
                'success_rate': successful_builds / total_builds if total_builds > 0 else 0,
                'failure_rate': failed_builds / total_builds if total_builds > 0 else 0,
                'avg_duration_minutes': avg_duration
            }
            metrics.append(metric_row)
        
        metrics_df = pd.DataFrame(metrics)
        
        # Save metrics
        timestamp = datetime.now().strftime(self.config['data_collection']['output']['timestamp_format'])
        metrics_file = os.path.join(self.output_dir, f"{period}_metrics_{timestamp}.csv")
        metrics_df.to_csv(metrics_file, index=False)
        
        logging.info(f"{period.capitalize()} metrics saved to {metrics_file}")
        return metrics_df


if __name__ == "__main__":
    analyzer = JenkinsAnalyzer()
    
    # Run analysis
    data = analyzer.load_data()
    
    # Create feature matrix for ML
    features = analyzer.create_feature_matrix(data)
    
    # Analyze failure patterns
    failure_analysis = analyzer.analyze_failure_patterns(data)
    
    # Generate prediction dataset
    X, y = analyzer.generate_build_prediction_dataset(data)
    
    # Calculate time-based metrics
    daily_metrics = analyzer.calculate_build_metrics_over_time(data, 'daily')
    
    print("Analysis completed successfully!")