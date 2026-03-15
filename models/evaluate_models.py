import matplotlib.pyplot as plt
from src.data_loader import prepare_data
from src.evaluation import evaluate_model, compare_metrics, plot_predictions


def main():
  # 1. prepare test data only 
  print("Loading test data...")
  (_, _), (_, _), (X_test, y_test), scaler = prepare_data(
    filepath="data/processed/processed_traffic.csv",
    seq_len=96,
    forecast_horizon=1
  )
  print(f"X_test shape : {X_test.shape}")
  print(f"y_test shape : {y_test.shape}")


  # 2. evaluate LSTM
  print("\nEvaluating LSTM model...")
  actual, lstm_preds, lstm_metrics = evaluate_model(
    model_path="results/trained_models/lstm_model.keras",
    X_testt=X_test,
    y_test=y_test,
    scaler=scaler
  )
  print(f"MAE  : {lstm_metrics['MAE']:.4f}")
  print(f"RMSE : {lstm_metrics['RMSE']:.4f}")
  print(f"MAPE : {lstm_metrics['MAPE']:.4f}%")


  # 3. evaluate GRU
  print("\nEvaluating GRU model...")
  actual, gru_preds, gru_metrics = evaluate_model(
    model_path="results/trained_models/gru_model.keras",
    X_testt=X_test,
    y_test=y_test,
    scaler=scaler
  )
  print(f"MAE  : {gru_metrics['MAE']:.4f}")
  print(f"RMSE : {gru_metrics['RMSE']:.4f}")
  print(f"MAPE : {gru_metrics['MAPE']:.4f}%")


  # 4. print side by side
  print(f"\n{'Metric':<10} {'LSTM':>10} {'GRU':>10}")
  print("-" * 30)
  for metric in ["MAE", "RMSE", "MAPE"]:
    print(f"{metric:<10} {lstm_metrics[metric]:>10.4f} {gru_metrics[metric]:>10.4f}")


  # 5. plot individual predictions 
  print("\nSaving plots...")
  plot_predictions(actual, lstm_preds, title="LSTM Predictions")
  plot_predictions(actual, gru_preds, title="GRU Predictions")


  # 6. plot both on same graph 
  plt.figure(figsize=(14, 5))
  plt.plot(actual[:500], label="Actual", color="black")
  plt.plot(lstm_preds[:500], label="LSTM", color="blue", linestyle="dashed")
  plt.plot(gru_preds[:500], label="GRU", color="orange", linestyle="dashed")
  plt.title("LSTM vs GRU Predictions")
  plt.xlabel("Time Steps")
  plt.ylabel("Traffic Volume")
  plt.legend()
  plt.savefig("results/graphs/lstm_vs_gru.png")
  plt.show()
  print("Saved → results/graphs/lstm_vs_gru.png")


  # 7. compare metrics bar charts
  compare_metrics(lstm_metrics, gru_metrics)
  print("Saved → results/metrics/")

  print("\nDone!")


if __name__ == "__main__":
  main()