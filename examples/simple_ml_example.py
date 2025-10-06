#!/usr/bin/env python3
"""
Simple machine learning example using Jenkins build data.

This script demonstrates how to use the collected Jenkins data for 
basic machine learning tasks like predicting build outcomes.

Usage:
    python simple_ml_example.py
    
Requirements:
    pip install scikit-learn matplotlib seaborn
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import JenkinsAnalyzer
import logging

# Optional ML imports (install with: pip install scikit-learn matplotlib seaborn)
try:
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, roc_auc_score
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    print("⚠️  Machine learning libraries not available.")
    print("Install with: pip install scikit-learn matplotlib seaborn")
    ML_AVAILABLE = False

def simple_build_prediction(X, y):
    """Train a simple model to predict build outcomes."""
    if not ML_AVAILABLE:
        return
    
    print(f"\n🤖 Training Machine Learning Models")
    print(f"===================================")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📊 Dataset Split:")
    print(f"   • Training samples: {len(X_train)}")
    print(f"   • Testing samples: {len(X_test)}")
    print(f"   • Features: {X_train.shape[1]}")
    
    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    accuracy = (y_pred == y_test).mean()
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n🏆 Model Results:")
    print(f"   • Accuracy: {accuracy:.3f}")
    print(f"   • AUC Score: {auc_score:.3f}")
    
    return model

def main():
    """Main function for ML example."""
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise
    
    print("Jenkins Build Prediction - ML Example")
    print("=====================================")
    
    try:
        # Initialize analyzer
        analyzer = JenkinsAnalyzer()
        
        # Load data
        print(f"📊 Loading Jenkins data...")
        data = analyzer.load_data()
        
        if not data.get('jobs'):
            print(f"❌ No job data found. Run data collection first.")
            return
        
        # Generate ML dataset
        print(f"🧠 Preparing ML dataset...")
        X, y = analyzer.generate_build_prediction_dataset(data)
        
        if X.empty or len(X) < 50:
            print(f"❌ Insufficient data for ML analysis (need at least 50 builds)")
            print(f"   Current dataset size: {len(X)} builds")
            return
        
        print(f"✅ Dataset ready: {len(X)} builds, {len(X.columns)} features")
        print(f"   Success rate: {y.mean():.1%}")
        
        # Run ML prediction
        if ML_AVAILABLE:
            model = simple_build_prediction(X, y)
        else:
            print(f"⚠️  Skipping ML prediction (libraries not installed)")
        
        print(f"\n✅ ML analysis completed!")
        
        if not ML_AVAILABLE:
            print(f"\n💡 To enable full ML capabilities, install required packages:")
            print(f"   pip install scikit-learn matplotlib seaborn")
        
    except FileNotFoundError:
        print(f"❌ No Jenkins data found.")
        print(f"💡 Run 'python collect_jenkins_data.py' first to collect data")
    except Exception as e:
        print(f"❌ Error during ML analysis: {e}")
        logging.error(f"ML analysis failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()