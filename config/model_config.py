# Shared model/training hyperparameters to keep LSTM/GRU/evaluation in sync

# Sequence configuration
SEQ_LEN = 96              # 24 hours of 15-minute intervals
FORECAST_HORIZON = 1      # Predict 1 step (15 minutes) ahead
INPUT_FEATURES = 10       # traffic_volume, hour, day_of_week, hour_sin, hour_cos, dow_sin, dow_cos, is_peak, is_weekend, road_name

# Training configuration
EPOCHS = 120
BATCH_SIZE = 256
LEARNING_RATE = 0.001
DROPOUT_RATE = 0.25
L2_REG = 1e-4

# Callback tuning
EARLY_STOP_PATIENCE = 12
LR_REDUCE_PATIENCE = 6
LR_REDUCE_FACTOR = 0.5
MIN_LR = 1e-5
MONITOR_METRIC = "val_loss" 
