import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt


def plot_series(time, series, format=".", start=0, end=None):
    plt.plot(time[start:end], series[start:end], format)
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.grid(None)


def trend(time, slope=0):
    return slope*time


def seasonal_pattern(season_time):
    return np.where(season_time < 0.1,
                    np.cos(season_time*6*np.pi),
                    2 / np.exp(9*season_time))


def seasonality(time, period, amplitude=1, phase=0):
    season_time = ((time+phase) % period) / period
    return amplitude + seasonal_pattern(season_time)


def noise (time, noise_level = 1, seed=None):
    rnd = np.random.RandomState(seed)
    return rnd.randn(len(time))*noise_level


def create_series():
    series = baseline+trend(time, slope) + seasonality(time, period=365, amplitude=amplitude)
    series += noise(time, noise_level, seed=51)

    time_train = time[:split_time]
    x_train = series[:split_time]
    time_valid = time[split_time:]
    x_valid = series[split_time:]

    return time_train, x_train, time_valid, x_valid


def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    dataset = tf.data.Dataset.from_tensor_slices(series)
    dataset = dataset.window(window_size+1, shift=1, drop_remainder=True)
    dataset = dataset.flat_map(lambda window: window.batch(window_size+1))
    dataset = dataset.shuffle(shuffle_buffer). map(lambda window: (window[:-1], window[-1]))
    dataset = dataset.batch(batch_size).prefetch(1)
    return dataset


def train(data, window_size):
    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(100, input_shape=[window_size], activation="relu"),
        tf.keras.layers.Dense(10, activation="relu"),
        tf.keras.layers.Dense(1)
    ])

    model.compile(loss="mse", optimizer=tf.keras.optimizers.SGD(lr=1e-6, momentum=0.9))
    history = model.fit(dataset, epochs=100, verbose=2)

    return model, history


def forecasting(model, series, window_size, split_time):
    forecast = []
    for time in range(len(series) - window_size):
        forecast.append(model.predict(series[time:time+window_size][np.newaxis]))
    forecast = forecast[split_time-window_size:]
    return np.array(forecast)[:, 0, 0]


if __name__ == "__main__":
    time = np.arange(10*365+1, dtype="float32")
    baseline= 10
    series = trend(time, 0.1)
    amplitude = 40
    slope = 0.005
    noise_level = 3
    split_time = 3000

    time_train, x_train, time_valid, x_valid = create_series()
    window_size = 20
    batch_size = 32
    shuffle_buffer_size = 1000
    dataset = windowed_dataset(x_train, window_size, batch_size, shuffle_buffer_size)
    model, history = train(dataset, window_size)
    results = forecasting(model, series, window_size, split_time)
    print(tf.keras.metrics.mean_absolute_error(x_valid, results).numpy())