"""
Utility functions for Jenkins data analysis.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging


def load_latest_data(data_dir: str = "data") -> Dict[str, Any]:
    """Load the most recent Jenkins data file."""
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Find JSON data files
    json_files = [f for f in os.listdir(data_dir) 
                  if f.startswith('complete_jenkins_data') and f.endswith('.json')]
    
    if not json_files:
        raise FileNotFoundError("No Jenkins data files found")
    
    # Get the most recent file
    latest_file = max(json_files)
    file_path = os.path.join(data_dir, latest_file)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    logging.info(f"Loaded data from {latest_file}")
    return data


def export_to_csv(data: Dict[str, Any], output_dir: str = "data") -> List[str]:
    """Export Jenkins data to CSV files for analysis."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    exported_files = []
    
    # Export jobs summary
    jobs_data = []
    for job in data.get('jobs', []):
        metrics = job.get('metrics', {})
        job_row = {
            'job_name': job.get('name'),
            'url': job.get('info', {}).get('url', ''),
            'description': job.get('info', {}).get('description', ''),
            'total_builds': metrics.get('total_builds', 0),
            'successful_builds': metrics.get('successful_builds', 0),
            'failed_builds': metrics.get('failed_builds', 0),
            'success_rate': metrics.get('success_rate', 0),
            'failure_rate': metrics.get('failure_rate', 0),
            'avg_duration_minutes': metrics.get('avg_duration_minutes', 0),
            'builds_per_day': metrics.get('builds_per_day', 0),
            'last_build_result': metrics.get('last_build_result', ''),
            'last_build_timestamp': metrics.get('last_build_timestamp', 0)
        }
        jobs_data.append(job_row)
    
    if jobs_data:
        jobs_df = pd.DataFrame(jobs_data)
        jobs_file = os.path.join(output_dir, f"jobs_summary_{timestamp}.csv")
        jobs_df.to_csv(jobs_file, index=False)
        exported_files.append(jobs_file)
        logging.info(f"Exported jobs summary to {jobs_file}")
    
    # Export builds detail
    builds_data = []
    for job in data.get('jobs', []):
        job_name = job.get('name')
        for build in job.get('builds', []):
            build_row = {
                'job_name': job_name,
                'build_number': build.get('number'),
                'result': build.get('result'),
                'timestamp': build.get('timestamp'),
                'datetime': build.get('datetime'),
                'duration_minutes': build.get('duration_minutes', 0),
                'built_on': build.get('built_on', ''),
                'queue_id': build.get('queue_id'),
                'estimated_duration': build.get('estimated_duration', 0),
                'artifacts_count': build.get('artifacts', 0),
                'total_tests': build.get('test_results', {}).get('total_tests', 0),
                'failed_tests': build.get('test_results', {}).get('failed_tests', 0),
                'passed_tests': build.get('test_results', {}).get('passed_tests', 0),
                'console_log_size': build.get('console_log_size', 0)
            }
            builds_data.append(build_row)
    
    if builds_data:
        builds_df = pd.DataFrame(builds_data)
        builds_file = os.path.join(output_dir, f"builds_detail_{timestamp}.csv")
        builds_df.to_csv(builds_file, index=False)
        exported_files.append(builds_file)
        logging.info(f"Exported builds detail to {builds_file}")
    
    # Export queue data
    queue_data = data.get('queue', [])
    if queue_data:
        queue_df = pd.DataFrame(queue_data)
        queue_file = os.path.join(output_dir, f"queue_data_{timestamp}.csv")
        queue_df.to_csv(queue_file, index=False)
        exported_files.append(queue_file)
        logging.info(f"Exported queue data to {queue_file}")
    
    # Export nodes data
    nodes_data = data.get('nodes', [])
    if nodes_data:
        nodes_df = pd.DataFrame(nodes_data)
        nodes_file = os.path.join(output_dir, f"nodes_data_{timestamp}.csv")
        nodes_df.to_csv(nodes_file, index=False)
        exported_files.append(nodes_file)
        logging.info(f"Exported nodes data to {nodes_file}")
    
    return exported_files


def calculate_build_statistics(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive statistics for a list of builds."""
    if not builds:
        return {}
    
    # Filter completed builds
    completed_builds = [b for b in builds if not b.get('building', False) and b.get('result')]
    
    if not completed_builds:
        return {'status': 'no_completed_builds'}
    
    # Basic counts
    total = len(completed_builds)
    success_count = len([b for b in completed_builds if b.get('result') == 'SUCCESS'])
    failure_count = len([b for b in completed_builds if b.get('result') == 'FAILURE'])
    unstable_count = len([b for b in completed_builds if b.get('result') == 'UNSTABLE'])
    aborted_count = len([b for b in completed_builds if b.get('result') == 'ABORTED'])
    
    # Duration statistics
    durations = [b.get('duration_minutes', 0) for b in completed_builds if b.get('duration_minutes', 0) > 0]
    
    # Time-based analysis
    timestamps = [b.get('timestamp', 0) for b in completed_builds if b.get('timestamp')]
    
    stats = {
        'total_builds': total,
        'successful_builds': success_count,
        'failed_builds': failure_count,
        'unstable_builds': unstable_count,
        'aborted_builds': aborted_count,
        'success_rate': success_count / total if total > 0 else 0,
        'failure_rate': failure_count / total if total > 0 else 0,
        'unstable_rate': unstable_count / total if total > 0 else 0,
        'abort_rate': aborted_count / total if total > 0 else 0
    }
    
    # Duration statistics
    if durations:
        stats.update({
            'avg_duration_minutes': np.mean(durations),
            'median_duration_minutes': np.median(durations),
            'min_duration_minutes': np.min(durations),
            'max_duration_minutes': np.max(durations),
            'std_duration_minutes': np.std(durations),
            'p95_duration_minutes': np.percentile(durations, 95),
            'p99_duration_minutes': np.percentile(durations, 99)
        })
    
    # Time-based statistics
    if len(timestamps) > 1:
        timestamps.sort()
        first_build = min(timestamps) / 1000
        last_build = max(timestamps) / 1000
        time_span_days = (last_build - first_build) / (24 * 3600)
        
        if time_span_days > 0:
            stats['builds_per_day'] = total / time_span_days
            stats['time_span_days'] = time_span_days
            stats['first_build_date'] = datetime.fromtimestamp(first_build).isoformat()
            stats['last_build_date'] = datetime.fromtimestamp(last_build).isoformat()
    
    return stats


def identify_failure_patterns(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Identify patterns in build failures."""
    failure_builds = [b for b in builds if b.get('result') == 'FAILURE']
    
    if not failure_builds:
        return {'no_failures': True}
    
    patterns = {
        'total_failures': len(failure_builds),
        'failure_by_hour': {},
        'failure_by_day_of_week': {},
        'failure_by_node': {},
        'consecutive_failure_streaks': []
    }
    
    # Analyze failure timing
    for build in failure_builds:
        timestamp = build.get('timestamp')
        if timestamp:
            dt = datetime.fromtimestamp(timestamp / 1000)
            
            # Hour of day
            hour = dt.hour
            patterns['failure_by_hour'][hour] = patterns['failure_by_hour'].get(hour, 0) + 1
            
            # Day of week
            day = dt.strftime('%A')
            patterns['failure_by_day_of_week'][day] = patterns['failure_by_day_of_week'].get(day, 0) + 1
        
        # Node analysis
        node = build.get('built_on', 'unknown')
        patterns['failure_by_node'][node] = patterns['failure_by_node'].get(node, 0) + 1
    
    # Find consecutive failure streaks
    current_streak = 0
    streaks = []
    
    for build in sorted(builds, key=lambda x: x.get('timestamp', 0), reverse=True):
        if build.get('result') == 'FAILURE':
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
                current_streak = 0
    
    if current_streak > 0:
        streaks.append(current_streak)
    
    patterns['consecutive_failure_streaks'] = streaks
    patterns['max_consecutive_failures'] = max(streaks) if streaks else 0
    patterns['avg_consecutive_failures'] = np.mean(streaks) if streaks else 0
    
    return patterns


def generate_recommendations(data: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on Jenkins data analysis."""
    recommendations = []
    
    summary = data.get('summary', {})
    jobs = data.get('jobs', [])
    nodes = data.get('nodes', [])
    queue = data.get('queue', [])
    
    # Queue analysis
    queue_length = summary.get('queue_length', 0)
    if queue_length > 10:
        recommendations.append(f"🚨 Build queue is long ({queue_length} items). Consider adding more build capacity.")
    elif queue_length > 5:
        recommendations.append(f"⚠️ Build queue has {queue_length} items. Monitor for capacity issues.")
    
    # Node analysis
    total_nodes = summary.get('total_nodes', 0)
    offline_nodes = summary.get('offline_nodes', 0)
    if offline_nodes > 0:
        offline_percent = (offline_nodes / total_nodes * 100) if total_nodes > 0 else 0
        if offline_percent > 20:
            recommendations.append(f"🚨 {offline_percent:.0f}% of nodes are offline ({offline_nodes}/{total_nodes}). Check node health.")
        else:
            recommendations.append(f"⚠️ {offline_nodes} nodes are offline. Verify node connectivity.")
    
    # Job performance analysis
    job_metrics = summary.get('job_metrics_summary', {})
    overall_success_rate = job_metrics.get('overall_success_rate', 1.0)
    
    if overall_success_rate < 0.7:
        recommendations.append(f"🚨 Overall success rate is low ({overall_success_rate:.1%}). Review failing jobs urgently.")
    elif overall_success_rate < 0.9:
        recommendations.append(f"⚠️ Overall success rate could be improved ({overall_success_rate:.1%}). Investigate common failure causes.")
    
    # Individual job analysis
    problematic_jobs = []
    slow_jobs = []
    
    for job in jobs:
        metrics = job.get('metrics', {})
        job_name = job.get('name')
        
        success_rate = metrics.get('success_rate', 1.0)
        avg_duration = metrics.get('avg_duration_minutes', 0)
        total_builds = metrics.get('total_builds', 0)
        
        # Identify problematic jobs
        if total_builds >= 5 and success_rate < 0.5:
            problematic_jobs.append((job_name, success_rate, total_builds))
        
        # Identify slow jobs
        if avg_duration > 60:  # More than 1 hour
            slow_jobs.append((job_name, avg_duration))
    
    # Recommendations for problematic jobs
    if problematic_jobs:
        problematic_jobs.sort(key=lambda x: x[1])  # Sort by success rate
        top_problems = problematic_jobs[:3]
        job_list = ", ".join([f"{name} ({rate:.1%})" for name, rate, _ in top_problems])
        recommendations.append(f"🚨 Investigate these failing jobs: {job_list}")
    
    # Recommendations for slow jobs
    if slow_jobs:
        slow_jobs.sort(key=lambda x: x[1], reverse=True)  # Sort by duration
        top_slow = slow_jobs[:3]
        job_list = ", ".join([f"{name} ({duration:.0f}min)" for name, duration in top_slow])
        recommendations.append(f"⏰ Optimize these slow jobs: {job_list}")
    
    # Build frequency recommendations
    recent_failures = job_metrics.get('jobs_with_recent_failures', 0)
    if recent_failures > 0:
        recommendations.append(f"🔄 {recent_failures} jobs have recent failures. Monitor closely and fix root causes.")
    
    # Capacity recommendations
    avg_duration = job_metrics.get('avg_build_duration_minutes', 0)
    if avg_duration > 30:
        recommendations.append(f"⚡ Average build duration is {avg_duration:.0f} minutes. Consider optimizing build processes.")
    
    # Default recommendations if everything looks good
    if not recommendations:
        recommendations.append("✅ Jenkins appears healthy! Consider setting up monitoring for early problem detection.")
        if overall_success_rate > 0.95:
            recommendations.append("🏆 Excellent success rate! Consider sharing best practices with other teams.")
    
    return recommendations


def export_ml_features(data: Dict[str, Any], output_file: str = None) -> str:
    """Export ML-ready feature matrix to CSV."""
    from analysis import JenkinsAnalyzer
    
    analyzer = JenkinsAnalyzer()
    features_df = analyzer.create_feature_matrix(data)
    
    if features_df.empty:
        raise ValueError("No features could be generated from the data")
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"ml_features_{timestamp}.csv"
    
    features_df.to_csv(output_file, index=False)
    logging.info(f"ML features exported to {output_file}")
    
    return output_file


def validate_jenkins_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Jenkins data structure and quality."""
    validation_result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'statistics': {}
    }
    
    # Check basic structure
    required_keys = ['collection_timestamp', 'jobs', 'summary']
    for key in required_keys:
        if key not in data:
            validation_result['errors'].append(f"Missing required key: {key}")
            validation_result['valid'] = False
    
    # Validate jobs data
    jobs = data.get('jobs', [])
    if not jobs:
        validation_result['warnings'].append("No jobs found in data")
    else:
        jobs_with_builds = 0
        total_builds = 0
        
        for job in jobs:
            if not job.get('name'):
                validation_result['warnings'].append("Job found without name")
            
            builds = job.get('builds', [])
            if builds:
                jobs_with_builds += 1
                total_builds += len(builds)
            
            # Check for required build fields
            for build in builds:
                if not build.get('number'):
                    validation_result['warnings'].append(f"Build without number in job {job.get('name', 'unknown')}")
                if not build.get('result') and not build.get('building'):
                    validation_result['warnings'].append(f"Build without result in job {job.get('name', 'unknown')}")
        
        validation_result['statistics'].update({
            'total_jobs': len(jobs),
            'jobs_with_builds': jobs_with_builds,
            'total_builds': total_builds,
            'avg_builds_per_job': total_builds / len(jobs) if jobs else 0
        })
    
    # Validate timestamp format
    try:
        collection_time = data.get('collection_timestamp')
        if collection_time:
            datetime.fromisoformat(collection_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        validation_result['warnings'].append("Invalid collection timestamp format")
    
    return validation_result