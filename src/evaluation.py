import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tensorflow.keras.models import load_model


# Inverse transform the data using the scaler
def inverse_transform(scaler, data: np.ndarray) -> np.ndarray:
  return scaler.inverse_transform(data.reshape(-1, 1)).flatten()


# Compute evaluation metrics: MAE, RMSE, and MAPE
def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
  mae = mean_absolute_error(actual, predicted)
  rmse = np.sqrt(mean_squared_error(actual, predicted))
  mape = np.mean(np.abs((actual - predicted) / actual)) * 100
  
  return { "MAE": mae, "RMSE": rmse, "MAPE": mape }


# Main function to evaluate the model on the test set
def evaluate_model(model_path, X_testt, y_test, scaler):
  # Load the saved model and make predictions on the test set
  model = load_model(model_path) 
  predictions = model.predict(X_testt)
  
  # Inverse transform the predictions and actual values to get them back to the original scale
  actual_real = inverse_transform(scaler, y_test)
  predicted_real = inverse_transform(scaler, predictions.flatten())
  
  # Compute the evaluation metrics and print them
  metrics = compute_metrics(actual_real, predicted_real)
  print(f"Evaluation Metrics for {model_path}:")
  
  return actual_real, predicted_real, metrics


# Plot the actual vs predicted values for visual comparison
def plot_predictions(actual, predicted, title):
  plt.figure(figsize=(14, 5))
  plt.plot(actual, label="Actual", color="blue")
  plt.plot(predicted, label="Predicted", color="orange")
  plt.title(title)
  plt.xlabel("Time Steps")
  plt.ylabel("Traffic Volume")
  plt.legend()
  plt.savefig(f"{title.lower().replace(' ', '_')}_predictions.png")
  plt.show()
  

# Compare the evaluation metrics of LSTM and GRU models using bar charts
def compare_metrics(lstm_metrics, gru_metrics):
  metrics_names = ["MAE", "RMSE", "MAPE"]
  
  for metric in metrics_names:
    plt.bar(["LSTM", "GRU"], [lstm_metrics[metric], gru_metrics[metric]], color=["blue", "orange"])
    plt.title(f"Comparison of {metric} between LSTM and GRU")
    plt.ylabel(metric)
    plt.savefig(f"comparison_{metric.lower()}.png")
    plt.show()