import re
import numpy as np
from modules.data_extraction import extract_numeric_value

def predict_future_performance(extracted_data, metric_name, years_to_predict=3):
    """Simple prediction of future values based on historical data"""
    # Extract historical values for the metric
    historical_values = []
    years = []
    
    for doc_name, doc_metrics in extracted_data.items():
        if metric_name in doc_metrics:
            metric_data = doc_metrics[metric_name]
            
            # Extract year and convert to number
            year_str = metric_data.get('period', metric_data.get('year', ''))
            year_match = re.search(r'(\d{4})', year_str)
            if year_match:
                year = int(year_match.group(1))
                
                # Extract value
                value = extract_numeric_value(metric_data['value'])
                if value is not None:
                    historical_values.append(value)
                    years.append(year)
    
    # Sort by year
    if not years or not historical_values:
        return None, None, None, None
    
    years, historical_values = zip(*sorted(zip(years, historical_values)))
    
    # Need at least 2 data points for prediction
    if len(historical_values) < 2:
        return None, None, None, None
    
    # Simple linear regression
    years_array = np.array(years).reshape(-1, 1)
    values_array = np.array(historical_values)
    
    # Calculate the line of best fit
    slope, intercept = np.polyfit(years_array.flatten(), values_array, 1)
    
    # Generate future predictions
    future_years = np.array(range(max(years) + 1, max(years) + years_to_predict + 1))
    predicted_values = slope * future_years + intercept
    
    # Calculate R-squared (goodness of fit)
    y_pred = slope * np.array(years) + intercept
    y_mean = np.mean(historical_values)
    r_squared = 1 - np.sum((np.array(historical_values) - y_pred) ** 2) / np.sum((np.array(historical_values) - y_mean) ** 2)
    
    # Prepare data for plotting
    all_years = np.concatenate([years, future_years])
    all_values = np.concatenate([historical_values, predicted_values])
    predictions = dict(zip(future_years, predicted_values))
    
    return all_years, all_values, predictions, r_squared

def calculate_growth_rate(values):
    """Calculate compound annual growth rate (CAGR)"""
    if len(values) < 2:
        return None
    
    start_value = values[0]
    end_value = values[-1]
    num_periods = len(values) - 1
    
    if start_value <= 0:
        return None
    
    cagr = (end_value / start_value) ** (1 / num_periods) - 1
    return cagr

def create_advanced_prediction(historical_data, years_to_predict=3, model_type='linear'):
    """Create more advanced prediction models"""
    if len(historical_data) < 3:
        return None
    
    # Unpack years and values
    years, values = zip(*sorted(historical_data))
    years = np.array(years)
    values = np.array(values)
    
    # Future years to predict
    future_years = np.array(range(max(years) + 1, max(years) + years_to_predict + 1))
    
    if model_type == 'linear':
        # Linear regression
        slope, intercept = np.polyfit(years, values, 1)
        predicted_values = slope * future_years + intercept
        
        # Calculate confidence interval
        n = len(years)
        mean_x = np.mean(years)
        std_err = np.sqrt(np.sum((values - (slope * years + intercept))**2) / (n-2))
        
        # Standard error of prediction
        pred_err = std_err * np.sqrt(1 + 1/n + (future_years - mean_x)**2 / np.sum((years - mean_x)**2))
        
        # 95% confidence interval
        t_value = 2.0  # Approximate t-value for 95% confidence
        lower_bound = predicted_values - t_value * pred_err
        upper_bound = predicted_values + t_value * pred_err
        
        return {
            'years': future_years,
            'predictions': predicted_values,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'model_type': 'linear'
        }
        
    elif model_type == 'exponential':
        # Exponential growth model
        try:
            # Need to ensure all values are positive
            if np.any(values <= 0):
                return None
                
            # Use logarithmic transformation for exponential model
            log_values = np.log(values)
            slope, intercept = np.polyfit(years, log_values, 1)
            
            # Predictions (need to exponentiate)
            predicted_values = np.exp(slope * future_years + intercept)
            
            # Simple confidence interval (not statistically rigorous)
            predicted_past = np.exp(slope * years + intercept)
            mean_err_ratio = np.mean(np.abs((values - predicted_past) / values))
            
            lower_bound = predicted_values * (1 - mean_err_ratio * 1.5)
            upper_bound = predicted_values * (1 + mean_err_ratio * 1.5)
            
            return {
                'years': future_years,
                'predictions': predicted_values,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'model_type': 'exponential'
            }
        except:
            return None
    
    return None