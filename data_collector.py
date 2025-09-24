"""
Data collection module for Jenkins jobs and builds.
"""

import os
import json
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from jenkins_client import JenkinsClient


class JenkinsDataCollector:
    """Collects and processes Jenkins data for analysis."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """Initialize data collector."""
        self.client = JenkinsClient(config_file)
        self.config = self.client.config
        
        # Create output directory
        self.output_dir = self.config['data_collection']['output']['directory']
        os.makedirs(self.output_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def collect_all_data(self) -> Dict[str, Any]:
        """Collect all Jenkins data including jobs, builds, queue, and nodes."""
        logging.info("Starting comprehensive data collection...")
        
        data = {
            'collection_timestamp': datetime.now().isoformat(),
            'jenkins_info': self._get_jenkins_info(),
            'jobs': self.collect_jobs_data(),
            'queue': self.collect_queue_data(),
            'nodes': self.collect_nodes_data(),
            'summary': {}
        }
        
        # Generate summary statistics
        data['summary'] = self._generate_summary(data)
        
        # Save data
        self._save_data(data, 'complete_jenkins_data')
        
        logging.info("Data collection completed successfully")
        return data
    
    def collect_jobs_data(self) -> List[Dict[str, Any]]:
        """Collect detailed job and build data."""
        logging.info("Collecting jobs data...")
        
        jobs = self.client.get_all_jobs()
        jobs_data = []
        
        for job in jobs:
            job_name = job['name']
            logging.info(f"Processing job: {job_name}")
            
            try:
                # Get detailed job info
                job_info = self.client.get_job_info(job_name)
                
                # Get build history
                builds = self.client.get_job_builds(job_name)
                
                # Process and enrich build data
                processed_builds = self._process_builds(builds)
                
                job_data = {
                    'name': job_name,
                    'info': job_info,
                    'builds': processed_builds,
                    'metrics': self._calculate_job_metrics(processed_builds),
                    'last_updated': datetime.now().isoformat()
                }
                
                jobs_data.append(job_data)
                
            except Exception as e:
                logging.error(f"Failed to process job {job_name}: {e}")
                continue
        
        logging.info(f"Collected data for {len(jobs_data)} jobs")
        return jobs_data
    
    def collect_queue_data(self) -> List[Dict[str, Any]]:
        """Collect build queue data."""
        logging.info("Collecting queue data...")
        
        try:
            queue_info = self.client.get_queue_info()
            processed_queue = []
            
            for item in queue_info:
                processed_item = {
                    'id': item.get('id'),
                    'task_name': item.get('task', {}).get('name', 'Unknown'),
                    'why': item.get('why', ''),
                    'blocked': item.get('blocked', False),
                    'buildable': item.get('buildable', False),
                    'stuck': item.get('stuck', False),
                    'in_queue_since': item.get('inQueueSince', 0),
                    'wait_time_ms': datetime.now().timestamp() * 1000 - item.get('inQueueSince', 0)
                }
                processed_queue.append(processed_item)
            
            return processed_queue
            
        except Exception as e:
            logging.error(f"Failed to collect queue data: {e}")
            return []
    
    def collect_nodes_data(self) -> List[Dict[str, Any]]:
        """Collect Jenkins nodes/agents data."""
        logging.info("Collecting nodes data...")
        
        try:
            nodes_info = self.client.get_nodes_info()
            processed_nodes = []
            
            for node in nodes_info:
                processed_node = {
                    'name': node.get('displayName', 'Unknown'),
                    'offline': node.get('offline', False),
                    'offline_cause': node.get('offlineCause'),
                    'offline_cause_reason': node.get('offlineCauseReason', ''),
                    'num_executors': node.get('numExecutors', 0),
                    'busy_executors': len([ex for ex in node.get('executors', []) 
                                         if ex.get('currentExecutable')]),
                    'idle_executors': node.get('numExecutors', 0) - len([ex for ex in node.get('executors', []) 
                                                                        if ex.get('currentExecutable')]),
                    'node_description': node.get('nodeDescription', ''),
                    'architecture': node.get('monitorData', {}).get('hudson.node_monitors.ArchitectureMonitor', ''),
                    'response_time': node.get('monitorData', {}).get('hudson.node_monitors.ResponseTimeMonitor', {}).get('average', 0)
                }
                processed_nodes.append(processed_node)
            
            return processed_nodes
            
        except Exception as e:
            logging.error(f"Failed to collect nodes data: {e}")
            return []
    
    def _get_jenkins_info(self) -> Dict[str, Any]:
        """Get basic Jenkins server information."""
        try:
            return {
                'url': self.client.url,
                'version': self.client.version,
                'connection_test': self.client.test_connection()
            }
        except Exception as e:
            logging.error(f"Failed to get Jenkins info: {e}")
            return {'error': str(e)}
    
    def _process_builds(self, builds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and enrich build data."""
        processed_builds = []
        
        for build in builds:
            try:
                processed_build = {
                    'number': build.get('number'),
                    'timestamp': build.get('timestamp'),
                    'datetime': datetime.fromtimestamp(build.get('timestamp', 0) / 1000).isoformat(),
                    'duration': build.get('duration', 0),
                    'duration_minutes': build.get('duration', 0) / (1000 * 60),
                    'result': build.get('result'),
                    'building': build.get('building', False),
                    'queue_id': build.get('queueId'),
                    'url': build.get('url'),
                    'built_on': build.get('builtOn', ''),
                    'estimated_duration': build.get('estimatedDuration', 0),
                    'executor': build.get('executor'),
                    'full_display_name': build.get('fullDisplayName', ''),
                    'keep_log': build.get('keepLog', False),
                    'causes': self._extract_build_causes(build),
                    'parameters': self._extract_build_parameters(build),
                    'artifacts': len(build.get('artifacts', [])),
                    'test_results': self._extract_test_results(build),
                    'console_log_size': len(build.get('console_output', '')) if build.get('console_output') else 0
                }
                
                # Calculate additional metrics
                if build.get('timestamp') and build.get('duration'):
                    start_time = build.get('timestamp') / 1000
                    end_time = start_time + (build.get('duration', 0) / 1000)
                    processed_build['start_datetime'] = datetime.fromtimestamp(start_time).isoformat()
                    processed_build['end_datetime'] = datetime.fromtimestamp(end_time).isoformat()
                
                processed_builds.append(processed_build)
                
            except Exception as e:
                logging.warning(f"Failed to process build {build.get('number', 'unknown')}: {e}")
                continue
        
        return processed_builds
    
    def _extract_build_causes(self, build: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract build trigger causes."""
        causes = []
        for action in build.get('actions', []):
            if action and 'causes' in action:
                for cause in action['causes']:
                    causes.append({
                        'class': cause.get('_class', ''),
                        'short_description': cause.get('shortDescription', ''),
                        'user_id': cause.get('userId', ''),
                        'user_name': cause.get('userName', '')
                    })
        return causes
    
    def _extract_build_parameters(self, build: Dict[str, Any]) -> Dict[str, Any]:
        """Extract build parameters."""
        parameters = {}
        for action in build.get('actions', []):
            if action and 'parameters' in action:
                for param in action['parameters']:
                    parameters[param.get('name', 'unknown')] = param.get('value', '')
        return parameters
    
    def _extract_test_results(self, build: Dict[str, Any]) -> Dict[str, int]:
        """Extract test results from build."""
        test_results = {
            'total_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'passed_tests': 0
        }
        
        for action in build.get('actions', []):
            if action and '_class' in action and 'TestResult' in action['_class']:
                test_results['total_tests'] = action.get('totalCount', 0)
                test_results['failed_tests'] = action.get('failCount', 0)
                test_results['skipped_tests'] = action.get('skipCount', 0)
                test_results['passed_tests'] = test_results['total_tests'] - test_results['failed_tests'] - test_results['skipped_tests']
                break
        
        return test_results
    
    def _calculate_job_metrics(self, builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for a job based on its builds."""
        if not builds:
            return {}
        
        # Filter out builds that are still running
        completed_builds = [b for b in builds if not b.get('building', False) and b.get('result')]
        
        if not completed_builds:
            return {'status': 'no_completed_builds'}
        
        # Basic counts
        total_builds = len(completed_builds)
        successful_builds = len([b for b in completed_builds if b.get('result') == 'SUCCESS'])
        failed_builds = len([b for b in completed_builds if b.get('result') == 'FAILURE'])
        unstable_builds = len([b for b in completed_builds if b.get('result') == 'UNSTABLE'])
        aborted_builds = len([b for b in completed_builds if b.get('result') == 'ABORTED'])
        
        # Duration statistics
        durations = [b.get('duration_minutes', 0) for b in completed_builds if b.get('duration_minutes', 0) > 0]
        
        metrics = {
            'total_builds': total_builds,
            'successful_builds': successful_builds,
            'failed_builds': failed_builds,
            'unstable_builds': unstable_builds,
            'aborted_builds': aborted_builds,
            'success_rate': successful_builds / total_builds if total_builds > 0 else 0,
            'failure_rate': failed_builds / total_builds if total_builds > 0 else 0,
            'avg_duration_minutes': sum(durations) / len(durations) if durations else 0,
            'min_duration_minutes': min(durations) if durations else 0,
            'max_duration_minutes': max(durations) if durations else 0,
            'last_build_result': completed_builds[0].get('result') if completed_builds else None,
            'last_build_timestamp': completed_builds[0].get('timestamp') if completed_builds else None
        }
        
        # Build frequency (builds per day)
        if len(completed_builds) > 1:
            first_build_time = min(b.get('timestamp', 0) for b in completed_builds) / 1000
            last_build_time = max(b.get('timestamp', 0) for b in completed_builds) / 1000
            time_span_days = (last_build_time - first_build_time) / (24 * 3600)
            
            if time_span_days > 0:
                metrics['builds_per_day'] = total_builds / time_span_days
            else:
                metrics['builds_per_day'] = 0
        else:
            metrics['builds_per_day'] = 0
        
        return metrics
    
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for collected data."""
        jobs_data = data.get('jobs', [])
        queue_data = data.get('queue', [])
        nodes_data = data.get('nodes', [])
        
        summary = {
            'total_jobs': len(jobs_data),
            'total_builds': sum(len(job.get('builds', [])) for job in jobs_data),
            'queue_length': len(queue_data),
            'total_nodes': len(nodes_data),
            'offline_nodes': len([n for n in nodes_data if n.get('offline', False)]),
            'collection_duration': datetime.now().isoformat(),
            'job_metrics_summary': self._summarize_job_metrics(jobs_data)
        }
        
        return summary
    
    def _summarize_job_metrics(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize metrics across all jobs."""
        all_metrics = [job.get('metrics', {}) for job in jobs_data if job.get('metrics')]
        
        if not all_metrics:
            return {}
        
        total_builds = sum(m.get('total_builds', 0) for m in all_metrics)
        total_successful = sum(m.get('successful_builds', 0) for m in all_metrics)
        total_failed = sum(m.get('failed_builds', 0) for m in all_metrics)
        
        success_rates = [m.get('success_rate', 0) for m in all_metrics if m.get('success_rate') is not None]
        durations = [m.get('avg_duration_minutes', 0) for m in all_metrics if m.get('avg_duration_minutes', 0) > 0]
        
        return {
            'overall_success_rate': total_successful / total_builds if total_builds > 0 else 0,
            'overall_failure_rate': total_failed / total_builds if total_builds > 0 else 0,
            'avg_job_success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
            'avg_build_duration_minutes': sum(durations) / len(durations) if durations else 0,
            'jobs_with_recent_failures': len([m for m in all_metrics if m.get('last_build_result') == 'FAILURE'])
        }
    
    def _save_data(self, data: Dict[str, Any], filename_prefix: str):
        """Save collected data to files."""
        timestamp = datetime.now().strftime(self.config['data_collection']['output']['timestamp_format'])
        output_format = self.config['data_collection']['output']['format']
        
        if output_format in ['json', 'both']:
            json_filename = f"{filename_prefix}_{timestamp}.json"
            json_path = os.path.join(self.output_dir, json_filename)
            
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logging.info(f"Data saved to {json_path}")
        
        if output_format in ['csv', 'both']:
            # Save flattened data to CSV for easier analysis
            self._save_csv_data(data, f"{filename_prefix}_{timestamp}")
    
    def _save_csv_data(self, data: Dict[str, Any], filename_prefix: str):
        """Save data in CSV format for analysis."""
        try:
            # Jobs summary CSV
            jobs_summary = []
            for job in data.get('jobs', []):
                job_summary = {
                    'job_name': job.get('name'),
                    'total_builds': job.get('metrics', {}).get('total_builds', 0),
                    'success_rate': job.get('metrics', {}).get('success_rate', 0),
                    'avg_duration_minutes': job.get('metrics', {}).get('avg_duration_minutes', 0),
                    'last_build_result': job.get('metrics', {}).get('last_build_result'),
                    'builds_per_day': job.get('metrics', {}).get('builds_per_day', 0)
                }
                jobs_summary.append(job_summary)
            
            if jobs_summary:
                jobs_df = pd.DataFrame(jobs_summary)
                jobs_csv_path = os.path.join(self.output_dir, f"{filename_prefix}_jobs_summary.csv")
                jobs_df.to_csv(jobs_csv_path, index=False)
                logging.info(f"Jobs summary saved to {jobs_csv_path}")
            
            # Builds detail CSV
            builds_detail = []
            for job in data.get('jobs', []):
                job_name = job.get('name')
                for build in job.get('builds', []):
                    build_detail = {
                        'job_name': job_name,
                        'build_number': build.get('number'),
                        'result': build.get('result'),
                        'duration_minutes': build.get('duration_minutes'),
                        'timestamp': build.get('timestamp'),
                        'datetime': build.get('datetime'),
                        'built_on': build.get('built_on'),
                        'artifacts_count': build.get('artifacts', 0),
                        'total_tests': build.get('test_results', {}).get('total_tests', 0),
                        'failed_tests': build.get('test_results', {}).get('failed_tests', 0)
                    }
                    builds_detail.append(build_detail)
            
            if builds_detail:
                builds_df = pd.DataFrame(builds_detail)
                builds_csv_path = os.path.join(self.output_dir, f"{filename_prefix}_builds_detail.csv")
                builds_df.to_csv(builds_csv_path, index=False)
                logging.info(f"Builds detail saved to {builds_csv_path}")
                
        except Exception as e:
            logging.error(f"Failed to save CSV data: {e}")


if __name__ == "__main__":
    collector = JenkinsDataCollector()
    collector.collect_all_data()