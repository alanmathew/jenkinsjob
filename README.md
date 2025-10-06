# Jenkins Job Analysis & AI/ML Toolkit

A comprehensive Python toolkit for collecting, analyzing, and applying machine learning to Jenkins build data. This repository provides scripts and utilities to extract valuable insights from your Jenkins CI/CD pipeline for analysis, monitoring, and predictive modeling.

## Features

### 🔧 Data Collection
- **Complete Jenkins Data Extraction**: Jobs, builds, queue, and node information
- **Configurable Collection**: Filter by job names, date ranges, and build counts  
- **Multiple Export Formats**: JSON and CSV outputs for different analysis needs
- **Build History Analysis**: Detailed build metrics, test results, and failure patterns

### 📊 Analysis & Insights  
- **Failure Pattern Analysis**: Identify trends in build failures by job, time, and infrastructure
- **Performance Metrics**: Build duration, success rates, and frequency analysis
- **Time-based Trends**: Daily, weekly, and monthly aggregations
- **Infrastructure Analysis**: Node performance and capacity utilization

### 🤖 AI/ML Ready Features
- **Feature Matrix Generation**: Ready-to-use datasets for machine learning
- **Build Outcome Prediction**: Models to predict build success/failure
- **Historical Context**: Time-series features and build sequence analysis
- **Anomaly Detection Ready**: Structured data for identifying unusual patterns

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/alanmathew/jenkinsjob.git
cd jenkinsjob

# Install Python dependencies
pip install -r requirements.txt

# For full ML capabilities (optional)
pip install scikit-learn matplotlib seaborn
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Jenkins credentials
# JENKINS_URL=http://your-jenkins-server:8080
# JENKINS_USER=your_username  
# JENKINS_TOKEN=your_api_token
```

### 3. Collect Data

```bash
# Run data collection
python examples/collect_jenkins_data.py
```

### 4. Analyze Results

```bash  
# Analyze build patterns
python examples/analyze_build_patterns.py

# Run ML example
python examples/simple_ml_example.py
```

## Project Structure

```
jenkinsjob/
├── jenkins_client.py          # Jenkins API client
├── data_collector.py          # Data collection and processing  
├── analysis.py                # Analysis and ML feature generation
├── config.yaml                # Configuration settings
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── examples/                 # Example usage scripts
│   ├── collect_jenkins_data.py
│   ├── analyze_build_patterns.py
│   └── simple_ml_example.py
└── data/                     # Output directory (created automatically)
```

## Configuration Options

### Jenkins Connection (`config.yaml`)
```yaml
jenkins:
  url: "http://localhost:8080"
  username: ""                  # Or set JENKINS_USER env var
  token: ""                     # Or set JENKINS_TOKEN env var  
  timeout: 30
```

### Data Collection Settings
```yaml
data_collection:
  jobs:
    include_disabled: false     # Include disabled jobs
    max_builds: 100            # Max builds per job
    include_console_logs: false # Include console output (large files)
  
  filters:
    job_name_patterns: []      # Regex to include specific jobs
    exclude_patterns: []       # Regex to exclude jobs
    date_range:
      start_date: "2024-01-01" # YYYY-MM-DD format
      end_date: null           # null = no limit
```

## Usage Examples

### Basic Data Collection
```python
from data_collector import JenkinsDataCollector

collector = JenkinsDataCollector()
data = collector.collect_all_data()
print(f"Collected data for {len(data['jobs'])} jobs")
```

### Analysis and ML Features
```python
from analysis import JenkinsAnalyzer

analyzer = JenkinsAnalyzer()
data = analyzer.load_data()

# Create ML feature matrix
features_df = analyzer.create_feature_matrix(data)

# Analyze failure patterns  
failure_analysis = analyzer.analyze_failure_patterns(data)

# Generate prediction dataset
X, y = analyzer.generate_build_prediction_dataset(data)
```

### Machine Learning Example
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load and prepare data
analyzer = JenkinsAnalyzer()
X, y = analyzer.generate_build_prediction_dataset()

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Predict build outcomes
predictions = model.predict(X_test)
```

## Output Data Formats

### JSON Output
- **Complete Jenkins Data**: Full hierarchical structure with all collected information
- **Analysis Results**: Structured failure patterns, metrics, and insights

### CSV Output  
- **Jobs Summary**: Key metrics per job (success rates, duration, frequency)
- **Builds Detail**: Individual build records with features for analysis
- **Feature Matrix**: ML-ready dataset with engineered features

## ML/AI Features

The toolkit generates rich feature sets for machine learning:

### Build Features
- Duration metrics and trends
- Success/failure patterns  
- Test results and coverage
- Build triggers and parameters
- Infrastructure utilization

### Historical Context
- Previous build outcomes
- Consecutive failure/success counts
- Time-based patterns (hour, day, week)
- Build frequency and intervals

### Use Cases
- **Predictive Modeling**: Predict build outcomes before completion
- **Anomaly Detection**: Identify unusual build patterns
- **Capacity Planning**: Analyze resource utilization trends  
- **Process Optimization**: Find patterns in build performance

## API Token Setup

1. **Generate Jenkins API Token**:
   - Login to Jenkins → User Profile → Configure → API Token → Generate

2. **Set Environment Variables**:
   ```bash
   export JENKINS_URL="http://your-jenkins:8080"
   export JENKINS_USER="your_username"
   export JENKINS_TOKEN="your_generated_token"
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)  
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📖 Check the examples/ directory for usage patterns
- 🐛 Report issues on GitHub Issues
- 💡 Feature requests are welcome

---

**Note**: This toolkit is designed for Jenkins analysis and monitoring. Ensure you have appropriate permissions and follow your organization's data handling policies when collecting Jenkins data.
