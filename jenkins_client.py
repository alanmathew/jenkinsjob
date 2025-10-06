"""
Jenkins API client for data extraction and analysis.
"""

import os
import logging
import requests
import jenkins
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import yaml


class JenkinsClient:
    """Jenkins API client for data extraction."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """Initialize Jenkins client with configuration."""
        load_dotenv()
        
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get credentials from environment or config
        self.url = os.getenv('JENKINS_URL', self.config['jenkins']['url'])
        self.username = os.getenv('JENKINS_USER', self.config['jenkins']['username'])
        self.token = os.getenv('JENKINS_TOKEN', self.config['jenkins']['token'])
        
        if not self.username or not self.token:
            logging.warning("Jenkins credentials not found. Some operations may fail.")
        
        # Initialize Jenkins client
        try:
            self.server = jenkins.Jenkins(
                self.url,
                username=self.username,
                password=self.token,
                timeout=self.config['jenkins']['timeout']
            )
            self.version = self.server.get_version()
            logging.info(f"Connected to Jenkins {self.version} at {self.url}")
        except Exception as e:
            logging.error(f"Failed to connect to Jenkins: {e}")
            self.server = None
    
    def get_all_jobs(self, include_disabled: bool = None) -> List[Dict[str, Any]]:
        """Get all jobs from Jenkins."""
        if not self.server:
            raise ConnectionError("Jenkins server not connected")
        
        include_disabled = include_disabled if include_disabled is not None else \
                          self.config['data_collection']['jobs']['include_disabled']
        
        try:
            jobs = self.server.get_all_jobs()
            
            if not include_disabled:
                jobs = [job for job in jobs if not job.get('color', '').endswith('disabled')]
            
            # Apply filters if configured
            jobs = self._apply_job_filters(jobs)
            
            logging.info(f"Retrieved {len(jobs)} jobs from Jenkins")
            return jobs
            
        except Exception as e:
            logging.error(f"Failed to retrieve jobs: {e}")
            return []
    
    def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific job."""
        if not self.server:
            raise ConnectionError("Jenkins server not connected")
        
        try:
            job_info = self.server.get_job_info(job_name)
            logging.debug(f"Retrieved info for job: {job_name}")
            return job_info
        except Exception as e:
            logging.error(f"Failed to get job info for {job_name}: {e}")
            return {}
    
    def get_job_builds(self, job_name: str, max_builds: int = None) -> List[Dict[str, Any]]:
        """Get build history for a specific job."""
        if not self.server:
            raise ConnectionError("Jenkins server not connected")
        
        max_builds = max_builds if max_builds is not None else \
                    self.config['data_collection']['jobs']['max_builds']
        
        try:
            job_info = self.get_job_info(job_name)
            builds = job_info.get('builds', [])
            
            # Limit number of builds
            if max_builds and len(builds) > max_builds:
                builds = builds[:max_builds]
            
            detailed_builds = []
            for build in builds:
                build_info = self.get_build_info(job_name, build['number'])
                if build_info:
                    detailed_builds.append(build_info)
            
            # Apply date filters
            detailed_builds = self._apply_date_filters(detailed_builds)
            
            logging.info(f"Retrieved {len(detailed_builds)} builds for job: {job_name}")
            return detailed_builds
            
        except Exception as e:
            logging.error(f"Failed to get builds for {job_name}: {e}")
            return []
    
    def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get detailed information about a specific build."""
        if not self.server:
            raise ConnectionError("Jenkins server not connected")
        
        try:
            build_info = self.server.get_build_info(job_name, build_number)
            
            # Add console log if configured
            if self.config['data_collection']['jobs']['include_console_logs']:
                try:
                    console_output = self.server.get_build_console_output(job_name, build_number)
                    build_info['console_output'] = console_output
                except Exception as e:
                    logging.warning(f"Failed to get console output for {job_name}#{build_number}: {e}")
                    build_info['console_output'] = None
            
            return build_info
            
        except Exception as e:
            logging.error(f"Failed to get build info for {job_name}#{build_number}: {e}")
            return {}
    
    def get_queue_info(self) -> List[Dict[str, Any]]:
        """Get current build queue information."""
        if not self.server:
            raise ConnectionError("Jenkins server not connected")
        
        try:
            queue_info = self.server.get_queue_info()
            logging.info(f"Retrieved {len(queue_info)} items from build queue")
            return queue_info
        except Exception as e:
            logging.error(f"Failed to get queue info: {e}")
            return []
    
    def get_nodes_info(self) -> List[Dict[str, Any]]:
        """Get information about Jenkins nodes/agents."""
        if not self.server:
            raise ConnectionError("Jenkins server not connected")
        
        try:
            nodes = self.server.get_nodes()
            detailed_nodes = []
            
            for node in nodes:
                node_info = self.server.get_node_info(node['name'])
                detailed_nodes.append(node_info)
            
            logging.info(f"Retrieved info for {len(detailed_nodes)} nodes")
            return detailed_nodes
            
        except Exception as e:
            logging.error(f"Failed to get nodes info: {e}")
            return []
    
    def _apply_job_filters(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply job name filters from configuration."""
        import re
        
        filters = self.config['data_collection']['filters']
        include_patterns = filters.get('job_name_patterns', [])
        exclude_patterns = filters.get('exclude_patterns', [])
        
        if include_patterns:
            compiled_includes = [re.compile(pattern) for pattern in include_patterns]
            jobs = [job for job in jobs 
                   if any(pattern.search(job['name']) for pattern in compiled_includes)]
        
        if exclude_patterns:
            compiled_excludes = [re.compile(pattern) for pattern in exclude_patterns]
            jobs = [job for job in jobs 
                   if not any(pattern.search(job['name']) for pattern in compiled_excludes)]
        
        return jobs
    
    def _apply_date_filters(self, builds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply date range filters to builds."""
        filters = self.config['data_collection']['filters']['date_range']
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if not start_date and not end_date:
            return builds
        
        filtered_builds = []
        for build in builds:
            build_timestamp = build.get('timestamp', 0) / 1000  # Convert to seconds
            build_date = datetime.fromtimestamp(build_timestamp).date()
            
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                if build_date < start:
                    continue
            
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                if build_date > end:
                    continue
            
            filtered_builds.append(build)
        
        return filtered_builds
    
    def test_connection(self) -> bool:
        """Test connection to Jenkins server."""
        try:
            if self.server:
                version = self.server.get_version()
                logging.info(f"Successfully connected to Jenkins {version}")
                return True
            else:
                logging.error("Jenkins server not initialized")
                return False
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False