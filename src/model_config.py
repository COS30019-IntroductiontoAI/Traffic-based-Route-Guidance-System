# Shared model/training hyperparameters to keep LSTM/GRU/evaluation in sync

# Sequence configuration
SEQ_LEN = 128             # 48 hours of 15-minute intervals
FORECAST_HORIZON = 1      # Predict 1 step (15 minutes) ahead
INPUT_FEATURES = 8        # traffic_volume, hour, day_of_week, is_weekend, hour_sin, hour_cos, dow_sin, dow_cos

# Training configuration
EPOCHS = 120
BATCH_SIZE = 256
LEARNING_RATE = 0.001
DROPOUT_RATE = 0.2

# Callback tuning
EARLY_STOP_PATIENCE = 15
LR_REDUCE_PATIENCE = 5
LR_REDUCE_FACTOR = 0.5
MIN_LR = 1e-5 